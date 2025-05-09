#!/usr/bin/env python
# coding=utf-8

# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import base64
import json
import pickle
import re
import time
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from typing import Any
import subprocess
import sys
import io
import contextlib

import PIL.Image
import requests

from .local_python_executor import PythonExecutor
from .monitoring import LogLevel
from .tools import Tool, get_tools_definition_code
from .utils import AgentError


try:
    from dotenv import load_dotenv

    load_dotenv()
except ModuleNotFoundError:
    pass


class RemotePythonExecutor(PythonExecutor):
    def __init__(self, additional_imports: list[str], logger):
        self.additional_imports = additional_imports
        self.logger = logger
        self.logger.log("Initializing executor, hold on...")
        self.final_answer_pattern = re.compile(r"^final_answer\((.*)\)$", re.M)
        self.installed_packages = []

    def run_code_raise_errors(self, code: str, return_final_answer: bool = False) -> tuple[Any, str]:
        raise NotImplementedError

    def send_tools(self, tools: dict[str, Tool]):
        tool_definition_code = get_tools_definition_code(tools)

        packages_to_install = set()
        for tool in tools.values():
            for package in tool.to_dict()["requirements"]:
                if package not in self.installed_packages:
                    packages_to_install.add(package)
                    self.installed_packages.append(package)

        execution = self.run_code_raise_errors(
            f"!pip install {' '.join(packages_to_install)}\n" + tool_definition_code
        )
        self.logger.log(execution[1])

    def send_variables(self, variables: dict):
        """
        Send variables to the kernel namespace using pickle.
        """
        pickled_vars = base64.b64encode(pickle.dumps(variables)).decode()
        code = f"""
import pickle, base64
vars_dict = pickle.loads(base64.b64decode('{pickled_vars}'))
locals().update(vars_dict)
"""
        self.run_code_raise_errors(code)

    def __call__(self, code_action: str) -> tuple[Any, str, bool]:
        """Check if code is a final answer and run it accordingly"""
        is_final_answer = bool(self.final_answer_pattern.search(code_action))
        output = self.run_code_raise_errors(code_action, return_final_answer=is_final_answer)
        # print("Hello:",output[0], ':', output[1], ':', is_final_answer)
        return output[0], output[1], is_final_answer

    def install_packages(self, additional_imports: list[str]):
        additional_imports = additional_imports + ["smolagents"]
        _, execution_logs = self.run_code_raise_errors(f"!pip install {' '.join(additional_imports)}")
        self.logger.log(execution_logs)
        return additional_imports


class E2BExecutor(RemotePythonExecutor):
    """
    Executes Python code using E2B.

    Args:
        additional_imports (`list[str]`): Additional imports to install.
        logger (`Logger`): Logger to use.
        **kwargs: Additional arguments to pass to the E2B Sandbox.
    """

    def __init__(self, additional_imports: list[str], logger, **kwargs):
        super().__init__(additional_imports, logger)
        try:
            from e2b_code_interpreter import Sandbox
        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                """Please install 'e2b' extra to use E2BExecutor: `pip install 'smolagents[e2b]'`"""
            )
        self.sandbox = Sandbox(**kwargs)
        self.installed_packages = self.install_packages(additional_imports)
        self.logger.log("E2B is running", level=LogLevel.INFO)

    def run_code_raise_errors(self, code: str, return_final_answer: bool = False) -> tuple[Any, str]:
        execution = self.sandbox.run_code(
            code,
        )
        if execution.error:
            execution_logs = "\n".join([str(log) for log in execution.logs.stdout])
            logs = execution_logs
            logs += "Executing code yielded an error:"
            logs += execution.error.name + "\n"
            logs += execution.error.value
            logs += execution.error.traceback
            raise AgentError(logs, self.logger)
        execution_logs = "\n".join([str(log) for log in execution.logs.stdout])
        if not execution.results:
            return None, execution_logs
        else:
            for result in execution.results:
                if result.is_main_result:
                    for attribute_name in ["jpeg", "png"]:
                        if getattr(result, attribute_name) is not None:
                            image_output = getattr(result, attribute_name)
                            decoded_bytes = base64.b64decode(image_output.encode("utf-8"))
                            return PIL.Image.open(BytesIO(decoded_bytes)), execution_logs
                    for attribute_name in [
                        "chart",
                        "data",
                        "html",
                        "javascript",
                        "json",
                        "latex",
                        "markdown",
                        "pdf",
                        "svg",
                        "text",
                    ]:
                        if getattr(result, attribute_name) is not None:
                            return getattr(result, attribute_name), execution_logs
            if return_final_answer:
                raise AgentError("No main result returned by executor!", self.logger)
            return None, execution_logs


class DockerExecutor(RemotePythonExecutor):
    """
    Executes Python code using Jupyter Kernel Gateway in a Docker container.
    """

    def __init__(
        self,
        additional_imports: list[str],
        logger,
        host: str = "127.0.0.1",
        port: int = 8888,
        image_name: str = "jupyter-kernel",
        build_new_image: bool = True,
        container_run_kwargs: dict[str, Any] | None = None,
    ):
        """
        Initialize the Docker-based Jupyter Kernel Gateway executor.

        Args:
            additional_imports: Additional imports to install.
            logger: Logger to use.
            host: Host to bind to.
            port: Port to bind to.
            image_name: Name of the Docker image to use. If the image doesn't exist, it will be built.
            build_new_image: If True, the image will be rebuilt even if it already exists.
            container_run_kwargs: Additional keyword arguments to pass to the Docker container run command.
        """
        super().__init__(additional_imports, logger)
        try:
            import docker
            from websocket import create_connection
        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                "Please install 'docker' extra to use DockerExecutor: `pip install 'smolagents[docker]'`"
            )
        self.host = host
        self.port = port
        self.image_name = image_name

        # Initialize Docker
        try:
            self.client = docker.from_env()
        except docker.errors.DockerException as e:
            raise RuntimeError("Could not connect to Docker daemon: make sure Docker is running.") from e

        # Build and start container
        try:
            # Check if image exists, unless forced to rebuild
            if not build_new_image:
                try:
                    self.client.images.get(self.image_name)
                    self.logger.log(f"Using existing Docker image: {self.image_name}", level=LogLevel.INFO)
                except docker.errors.ImageNotFound:
                    self.logger.log(f"Image {self.image_name} not found, building...", level=LogLevel.INFO)
                    build_new_image = True

            if build_new_image:
                self.logger.log(f"Building Docker image {self.image_name}...", level=LogLevel.INFO)
                dockerfile_path = Path(__file__).parent / "Dockerfile"
                if not dockerfile_path.exists():
                    with open(dockerfile_path, "w") as f:
                        f.write("""FROM python:3.12-slim

RUN pip install jupyter_kernel_gateway requests numpy pandas
RUN pip install jupyter_client notebook

EXPOSE 8888
CMD ["jupyter", "kernelgateway", "--KernelGatewayApp.ip='0.0.0.0'", "--KernelGatewayApp.port=8888", "--KernelGatewayApp.allow_origin='*'"]
""")
                _, build_logs = self.client.images.build(
                    path=str(dockerfile_path.parent), dockerfile=str(dockerfile_path), tag=self.image_name
                )
                self.logger.log(build_logs, level=LogLevel.DEBUG)

            self.logger.log(f"Starting container on {host}:{port}...", level=LogLevel.INFO)
            # Create base container parameters
            container_kwargs = {}
            if container_run_kwargs:
                container_kwargs.update(container_run_kwargs)

            # Ensure required port mapping and background running
            if not isinstance(container_kwargs.get("ports"), dict):
                container_kwargs["ports"] = {}
            container_kwargs["ports"]["8888/tcp"] = (host, port)
            container_kwargs["detach"] = True

            self.container = self.client.containers.run(self.image_name, **container_kwargs)

            retries = 0
            while self.container.status != "running" and retries < 5:
                self.logger.log(f"Container status: {self.container.status}, waiting...", level=LogLevel.INFO)
                time.sleep(1)
                self.container.reload()
                retries += 1

            self.base_url = f"http://{host}:{port}"

            # Create new kernel via HTTP
            r = requests.post(f"{self.base_url}/api/kernels")
            if r.status_code != 201:
                error_details = {
                    "status_code": r.status_code,
                    "headers": dict(r.headers),
                    "url": r.url,
                    "body": r.text,
                    "request_method": r.request.method,
                    "request_headers": dict(r.request.headers),
                    "request_body": r.request.body,
                }
                self.logger.log_error(f"Failed to create kernel. Details: {json.dumps(error_details, indent=2)}")
                raise RuntimeError(f"Failed to create kernel: Status {r.status_code}\nResponse: {r.text}") from None

            self.kernel_id = r.json()["id"]

            ws_url = f"ws://{host}:{port}/api/kernels/{self.kernel_id}/channels"
            self.ws = create_connection(ws_url)

            self.installed_packages = self.install_packages(additional_imports)
            self.logger.log(
                f"Container {self.container.short_id} is running with kernel {self.kernel_id}", level=LogLevel.INFO
            )

        except Exception as e:
            self.cleanup()
            raise RuntimeError(f"Failed to initialize Jupyter kernel: {e}") from e

    def run_code_raise_errors(self, code_action: str, return_final_answer: bool = False) -> tuple[Any, str]:
        """
        Execute code and return result based on whether it's a final answer.
        """
        try:
            if return_final_answer:
                match = self.final_answer_pattern.search(code_action)
                if match:
                    pre_final_answer_code = self.final_answer_pattern.sub("", code_action)
                    result_expr = match.group(1)
                    wrapped_code = pre_final_answer_code + dedent(f"""
                        import pickle, base64
                        _result = {result_expr}
                        print("RESULT_PICKLE:" + base64.b64encode(pickle.dumps(_result)).decode())
                        """)
            else:
                wrapped_code = code_action

            # Send execute request
            msg_id = self._send_execute_request(wrapped_code)

            # Collect output and results
            outputs = []
            result = None
            waiting_for_idle = False

            while True:
                msg = json.loads(self.ws.recv())
                msg_type = msg.get("msg_type", "")
                parent_msg_id = msg.get("parent_header", {}).get("msg_id")

                # Only process messages related to our execute request
                if parent_msg_id != msg_id:
                    continue

                if msg_type == "stream":
                    text = msg["content"]["text"]
                    if return_final_answer and text.startswith("RESULT_PICKLE:"):
                        pickle_data = text[len("RESULT_PICKLE:") :].strip()
                        result = pickle.loads(base64.b64decode(pickle_data))
                        waiting_for_idle = True
                    else:
                        outputs.append(text)
                elif msg_type == "error":
                    traceback = msg["content"].get("traceback", [])
                    raise AgentError("\n".join(traceback), self.logger)
                elif msg_type == "status" and msg["content"]["execution_state"] == "idle":
                    if not return_final_answer or waiting_for_idle:
                        break

            return result, "".join(outputs)

        except Exception as e:
            self.logger.log_error(f"Code execution failed: {e}")
            raise

    def _send_execute_request(self, code: str) -> str:
        """Send code execution request to kernel."""
        import uuid

        # Generate a unique message ID
        msg_id = str(uuid.uuid4())

        # Create execute request
        execute_request = {
            "header": {
                "msg_id": msg_id,
                "username": "anonymous",
                "session": str(uuid.uuid4()),
                "msg_type": "execute_request",
                "version": "5.0",
            },
            "parent_header": {},
            "metadata": {},
            "content": {
                "code": code,
                "silent": False,
                "store_history": True,
                "user_expressions": {},
                "allow_stdin": False,
            },
        }

        self.ws.send(json.dumps(execute_request))
        return msg_id

    def cleanup(self):
        """Clean up resources."""
        try:
            if hasattr(self, "container"):
                self.logger.log(f"Stopping and removing container {self.container.short_id}...", level=LogLevel.INFO)
                self.container.stop()
                self.container.remove()
                self.logger.log("Container cleanup completed", level=LogLevel.INFO)
        except Exception as e:
            self.logger.log_error(f"Error during cleanup: {e}")

    def delete(self):
        """Ensure cleanup on deletion."""
        self.cleanup()

class LocalExecExecutor(RemotePythonExecutor):
    """
    Executes Python code using the built-in exec() function.
    
    This executor runs code in the local Python environment without sandboxing,
    capturing output and handling various return types.
    
    WARNING: This executor is NOT SECURE for untrusted code. It executes code directly
    in the current Python process without any isolation. Use only with trusted code.
    
    Args:
        additional_imports (`list[str]`): Additional packages to install.
        logger (`Logger`): Logger to use.
        capture_graphics (`bool`): Whether to capture matplotlib and other graphics output.
        restricted_modules (`List[str]`, optional): List of modules to restrict from importing.
        **kwargs: Additional configuration parameters.
    """

    def __init__(self, additional_imports: list[str], logger, capture_graphics: bool = True, 
                 restricted_modules: list[str] = None, **kwargs):
        super().__init__(additional_imports, logger)
        self.installed_packages = self.install_packages(additional_imports)
        self.globals_dict = {
            '_output_data': None,
            '_output_type': None,
            '_last_value': None,
            '_final_answer': None,
            'display': self._display_func
        }
        self.capture_graphics = capture_graphics
        self.restricted_modules = restricted_modules or []
        self.tools = {}

    def __call__(self, code_action: str) -> tuple[Any, str, bool]:
        """Check if code is a final answer and run it accordingly"""
        does_not_care = False
        output = self.run_code_raise_errors(code_action, return_final_answer=does_not_care)
        is_final_answer = output[2]
        return output[0], output[1], is_final_answer
        
    def send_tools(self, tools: dict[str, Tool]):
        self.tools = tools
    
    def _setup_security_restrictions(self):
        """
        Set up basic security restrictions for executing code.
        Not foolproof, but provides some basic protection.
        """
        original_import = __import__
        
        def restricted_import(name, *args, **kwargs):
            # Check if the module is restricted
            for restricted in self.restricted_modules:
                if name == restricted or name.startswith(f"{restricted}."):
                    raise ImportError(f"Import of '{name}' is restricted for security reasons")
            return original_import(name, *args, **kwargs)
        
        # Add the restricted import to the globals dict
        self.globals_dict['__builtins__'] = dict(__import__=restricted_import, **__builtins__.__dict__)
        
        # Add a note about the restrictions
        modules_list = ", ".join(self.restricted_modules)
        self.logger.log(f"Basic import restrictions applied for: {modules_list}", level=LogLevel.INFO)
    
    def install_packages(self, packages: list[str]) -> list[str]:
        """Install Python packages using pip."""
        installed = []
    
    def _display_func(self, obj, mime_type=None):
        """
        Function to handle display of various object types.
        Similar to IPython's display function.
        """
        # Determine the MIME type if not specified
        if mime_type is None:
            if hasattr(obj, '_repr_png_'):
                mime_type = 'image/png'
                obj = obj._repr_png_()
            elif hasattr(obj, '_repr_jpeg_'):
                mime_type = 'image/jpeg'
                obj = obj._repr_jpeg_()
            elif hasattr(obj, '_repr_html_'):
                mime_type = 'text/html'
                obj = obj._repr_html_()
            elif hasattr(obj, '_repr_markdown_'):
                mime_type = 'text/markdown'
                obj = obj._repr_markdown_()
            elif hasattr(obj, '_repr_json_'):
                mime_type = 'application/json'
                obj = obj._repr_json_()
            elif isinstance(obj, PIL.Image.Image):
                mime_type = 'image/png'
                buffer = BytesIO()
                obj.save(buffer, format='PNG')
                buffer.seek(0)
                obj = base64.b64encode(buffer.read()).decode('utf-8')
            else:
                mime_type = 'text/plain'
                obj = str(obj)
        
        # Store the output
        self.globals_dict['_output_data'] = obj
        self.globals_dict['_output_type'] = mime_type
    
    def _setup_matplotlib_hook(self):
        """Set up hooks to capture matplotlib output."""
        if not self.capture_graphics:
            return
        
        # This code will be executed in the globals context
        setup_code = """
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import io, base64

    # Save the original show method
    _original_show = plt.show

    # Define a custom show method to capture figures
    def _custom_show(*args, **kwargs):
        global _output_data, _output_type
        buf = io.BytesIO()
        plt.savefig(buf, format='PNG')
        buf.seek(0)
        _output_data = base64.b64encode(buf.read()).decode('utf-8')
        _output_type = 'image/png'
        plt.close()
        return None

    # Replace plt.show with our custom version
    plt.show = _custom_show
except ImportError:
    # Matplotlib is not available, skip setup
    pass
"""
        try:
            exec(setup_code, self.globals_dict)
            # self.logger.log("Matplotlib hooks configured for graphics capture", level=LogLevel.INFO)
        except Exception as e:
            self.logger.log(f"Failed to configure matplotlib hooks: {e}", level=LogLevel.WARNING)
    
    def run_code_raise_errors(self, code: str, return_final_answer: bool = False) -> tuple[Any, str]:
        """
        Execute Python code and return the result and output logs.
        
        Args:
            code (str): The Python code to execute
            return_final_answer (bool): Whether to raise an error if no result is returned
            
        Returns:
            tuple[Any, str]: A tuple containing (result, logs)
        """
        # Reset output data
        self.globals_dict['_output_data'] = None
        self.globals_dict['_output_type'] = None
        self.globals_dict['_last_value'] = None
        self.globals_dict['_final_answer'] = None
        self.globals_dict.update(self.tools)
        is_final_answer = False
        
        # Set up matplotlib if needed
        if self.capture_graphics:
            self._setup_matplotlib_hook()
        
        # Create buffers for stdout and stderr
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        
        locals_dict = None
        wrapped_code = f"""
_final_answer = None
_last_value = None
def final_answer(pfinal):
    global _final_answer
    _final_answer = pfinal
{code}
if '_' in locals():
    _last_value = _
"""
        # print(wrapped_code)
        
        # Execute the code, capturing stdout and stderr
        with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
            try:
                # Add special handling for Jupyter-style last expression value
                # Wrap the code to capture the last expression value
                # Execute the code
                exec(wrapped_code, self.globals_dict, locals_dict)                
            except Exception as e:
                # Get the traceback
                import traceback
                tb = traceback.format_exc()
                error_msg = f"Error executing code: {str(e)}\n{tb}"
                stderr_buffer.write(error_msg)
                raise AgentError(error_msg, self.logger)
        
        # print('Global dict', self.globals_dict)
        # print('Local dict', locals_dict)

        is_final_answer = (self.globals_dict['_final_answer'] is not None)
        # Collect logs
        stdout_content = stdout_buffer.getvalue()
        stderr_content = stderr_buffer.getvalue()
        
        logs = stdout_content
        logs += "\nLast value:\n" + str(self.globals_dict['_last_value'])
        if stderr_content:
            logs += "\nStderr:\n" + stderr_content
        print('Logs', logs)
        
        # Check if result is required but not found
        # if return_final_answer and result is None:
        #    raise AgentError("No result was returned from the code execution", self.logger)
        
        return self.globals_dict['_final_answer'], logs, is_final_answer
        
__all__ = ["E2BExecutor", "DockerExecutor"]
