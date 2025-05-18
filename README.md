<!---
Copyright 2024 The HuggingFace Team. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
# Beyond Python Smolagents
**Beyond Python Smolagents** is a fork of the original [smolagents](https://github.com/huggingface/smolagents) that extends its original abilities to code in pascal, php and other languages. **It is also able to natively run python code via the `exec` command allowing faster and unrestricted code execution**.
This fork dramatically expands its original capabilities to work with multiple programming languages and complex tasks through autonomous agent collaboration.
It also excels at generating or updating documentation for existing code bases including writing readme files. It also does a good job at researching and experimenting ideas.

***
### 🔥🚨 EXTREME SECURITY RISK 🚨🔥
***

**This implementation grants agents extensive access and control over the environment in which they run.** This level of control is intentionally designed to enable powerful automation and interaction capabilities across different languages and the operating system (including file system access, running arbitrary OS commands, and executing code in various languages).

**CONSEQUENTLY, USING THIS SOFTWARE IN AN ENVIRONMENT CONTAINING SENSITIVE DATA, PRODUCTION SYSTEMS, OR IMPORTANT PERSONAL INFORMATION IS HIGHLY DANGEROUS AND STRONGLY DISCOURAGED.**

**YOU MUST ONLY RUN THIS CODE INSIDE A SECURELY ISOLATED ENVIRONMENT** specifically set up for this purpose, such as:
*   **A dedicated Virtual Machine (VM):** Configure a VM with minimal or no sensitive data, isolated from your main network if possible. Treat anything inside the VM as potentially compromised.
*   **A locked-down Container (like Docker):** Use containerization to create an isolated filesystem and process space. Ensure no sensitive volumes from your host machine are mounted into the container. Limit network access if possible.

**DO NOT** run this code directly on your primary development machine, production servers, personal computer, or any environment with valuable data or system access you wish to protect.

**USE THIS SOFTWARE ENTIRELY AT YOUR OWN RISK! The developers explicitly disclaim responsibility for any damage, data loss, security breaches, or other negative consequences resulting from the use of this software in an insecure or inappropriate environment.** This warning cannot be overstated.
***

## Installation
To get started with Beyond Python Smolagents, follow these steps:

1.  **Install LiteLLM:** LiteLLM is used to interact with various language models.
    ```bash
    !pip install litellm==1.67.2
    ```

2.  **Clone the Repository:** Clone the `v1.14-bp` branch of the Beyond Python Smolagents repository.
    ```bash
    !git clone -b v1.14-bp https://github.com/joaopauloschuler/beyond-python-smolagents smolagents
    ```

3.  **Install Beyond Python Smolagents:** Install the cloned project, including the LiteLLM dependencies.
    ```bash
    !pip install ./smolagents[litellm]
    ```

This will set up the necessary libraries and the Beyond Python Smolagents framework in your environment.

## Basic usage (single agent)
Create a single agent with various tools for working with different programming languages:
```
import smolagents
from smolagents.bp_tools import *
from smolagents.bp_utils import *
from smolagents.bp_thinkers import *
from smolagents import HfApiModel, LiteLLMModel, LogLevel
from smolagents import CodeAgent, MultiStepAgent, ToolCallingAgent
from smolagents import tool

MAX_TOKENS = 64000
coder_model_id = "gemini/gemini-2.5-flash-preview-04-17"
coder_model = LiteLLMModel(model_id=coder_model_id, api_key=YOUR_KEY_VALUE, max_tokens=MAX_TOKENS)

tools = [ run_os_command,
  compile_and_run_pascal_code, run_php_file,
  pascal_interface_to_string, source_code_to_string, string_to_source_code,  
  save_string_to_file, load_string_from_file, 
  copy_file, replace_on_file, replace_on_file_with_files, get_file_size, 
  ]

coder_agent = CodeAgent( model=coder_model, tools = tools, add_base_tools=True)
coder_agent.run("Please list the files in the current folder.")
```

## Create a team of agents (sub-assistants) and use them as tools

### Core Concepts

Beyond Python Smolagents is built around the concept of AI agents equipped with tools to interact with their environment and solve tasks.

*   **Agents** (inherited from [smolagents](https://github.com/huggingface/smolagents)): Autonomous entities powered by language models that receive instructions and use available tools to achieve objectives. Different agent types (`CodeAgent`, `ToolCallingAgent`, `MultiStepAgent`) are available, each tailored for potentially different purposes and capable of being configured with specific tool sets:
    *   `CodeAgent`: Specialized in code generation, execution, and debugging across multiple languages.
    *   `ToolCallingAgent`: A general-purpose agent capable of utilizing a defined set of tools.
    *   `MultiStepAgent`: Designed to break down complex tasks into smaller steps and execute them sequentially or iteratively.
*   **Models** (inherited from [smolagents](https://github.com/huggingface/smolagents)): The underlying Language Models (LLMs) that provide the cognitive capabilities for the agents, enabling them to understand tasks, reason, and generate responses or code. The framework integrates with various LLMs via the LiteLLM library, allowing users to select models based on cost, performance, context window size, and specific capabilities.
*   **Tools:** (inherited from [smolagents](https://github.com/huggingface/smolagents)): Functions or utilities that agents can call to perform actions in the environment. These abstract interactions such as running OS commands, accessing the filesystem, interacting with the internet, or executing code in different programming languages. Tools are fundamental; without them, agents can only generate text; with them, they can *act*. The framework provides many built-in tools, and users can define custom ones.
*   **Sub-assistants:** Instances of agents are treated as tools and provided to a primary agent (often called "the boss"). This allows a higher-level agent to delegate specific sub-tasks to specialized agents. For example, a main agent tasked with building a project might delegate code generation to a `CoderSubassistant` or research to an `InternetSearchSubassistant`. This enables building complex, modular artificial workforce and leverages the specialized capabilities of different agent configurations.
*   **Base Tools (`add_base_tools=True/False`)** (inherited from [smolagents](https://github.com/huggingface/smolagents)): A crucial parameter when initializing agents. It controls whether an agent automatically receives a default, standard set of tools provided by the Beyond Python Smolagents framework.
    *   Setting `add_base_tools=True` equips the agent with a common set of utilities right out of the box. This set typically includes tools for basic file operations (`save_string_to_file`, `load_string_from_file`), web interaction (`VisitWebpageTool`, `DuckDuckGoSearchTool`), and Python execution (`PythonInterpreterTool`), among others. These are added *in addition to* any tools explicitly provided in the `tools` list during initialization. This is useful for creating general-purpose agents.
    *   Setting `add_base_tools=False` means the agent will *only* have access to the tools explicitly passed to it via the `tools` parameter during initialization. This allows for creating highly minimal or very specifically-purposed agents with a restricted set of actions, which can be beneficial for security or task focus.


### Creating the team
Beyond Python Smolagents allows you to compose complex working groups by having agents delegate tasks to other specialized agents, referred to as sub-assistants. This modular approach helps manage complexity and leverage agents optimized for specific tasks (e.g., coding, internet search, summarization).

The library provides wrapper classes (Subassistant, CoderSubassistant, InternetSearchSubassistant, Summarize, etc.) that turn an agent instance into a tool that another agent can call.

Here's an example demonstrating how to set up a "boss" agent that can utilize other agents as sub-assistants:
```
no_tool_agent = ToolCallingAgent(tools=[], model=model, add_base_tools=False)
tooled_agent = ToolCallingAgent(tools=tools, model=model, add_base_tools=True)
internet_search_agent = ToolCallingAgent(tools=[save_string_to_file, load_string_from_file], model=model, add_base_tools=True)

subassistant = Subassistant(tooled_agent)
internet_search_subassistant = InternetSearchSubassistant(internet_search_agent)
coder_subassistant = CoderSubassistant(coder_agent)
summarize = Summarize(no_tool_agent)
summarize_url = SummarizeUrl(no_tool_agent)
summarize_local_file = SummarizeLocalFile(no_tool_agent)
get_relevant_info_from_file = GetRelevantInfoFromFile(no_tool_agent)
get_relevant_info_from_url = GetRelevantInfoFromUrl(no_tool_agent)

tools = [save_string_to_file, load_string_from_file, copy_file, get_file_size,
  source_code_to_string, string_to_source_code, pascal_interface_to_string,
  replace_on_file, replace_on_file_with_files,
  subassistant, coder_subassistant, internet_search_subassistant,
  summarize, summarize_url, summarize_local_file,
  get_relevant_info_from_file, get_relevant_info_from_url,
  run_os_command, run_php_file, compile_and_run_pascal_code,
  ]

task_str="""Code, test and debug something that will impress me!
For completing the task, you will first plan for it.
You will decide what task will be assigned to each of your sub-assistants.
You will decide the need for researching using internet_search_subassistant before you actually start coding a solution."""

the_boss = CodeAgent(model=coder_model, tools = tools, add_base_tools=True)
the_boss.run(task_str)
```

## Use heavy thinking
Using "Heavy Thinking" is typically more computationally intensive and time-consuming than basic single-agent tasks, but it is designed to yield superior results for difficult problems that benefit from a more thorough, multi-pass approach.
`evolutive_problem_solver` combines evolutive computing, genetic algorithms and agents to produce a final result.

The "Heavy Thinking" method within Beyond Python Smolagents represents an advanced paradigm for tackling highly complex or open-ended problems that may not be solvable in a single agent turn. It's particularly useful for tasks requiring significant iterative refinement, exploration, or multi-step reasoning, such as generating comprehensive documentation from a large codebase or complex coding tasks.

While `evolutive_problem_solver` internal workings involve sophisticated logic, the user interacts with it by providing a detailed task prompt and a set of tools. `evolutive_problem_solver` has an iterative process, potentially involving multiple agent interactions, intermediate evaluations, and refinements over several "steps" and "agent_steps" within each step, aiming to converge on a high-quality solution.

Here is how you might conceptually set up and invoke the `evolutive_problem_solver` for a task like generating comprehensive documentation from source code. This example focuses on *how* you would structure the input prompt and call the function:

```
!git clone git@github.com:joaopauloschuler/neural-api.git
current_source = source_code_to_string('neural-api')
project_name = 'neural-api'
task = """You have access to an Ubuntu system. You have available to you python, php and free pascal.
You are given the source code of the """+project_name+""" project in the tags <file filename="..."> source code file content </file>.
This is the source code:"""+current_source+"""
Your highly important and interesting task is producing a better version of the README.md file.
You will save the updated versions of the README.md into new files as directed.
The original version of the readme file is provided in the tag <file filename="README.md"><file>.
When asked to test, given that this is a task regarding documentation, you should review the README file.
When asked to code, you will produce documentation.

You will write the documentation in a technical and non commercial language.
You contribution will be helping others to understand how to use this project and its inner workings so future
developers will be able to build on the top of it.
It would be fantastic if you could add to the documentation ideas about to solve problems using this project. Solving ideas about how to use it to solve problems in the real world.
For saving documentation, use the tags <savetofile> and <appendtofile>. Trying to save documentation via python code is just too hard and error prone.
When asked to test or review documentation, make sure that referred files or functions do actually exist. This is to prevent broken links.
Your documentation should focus on existing features only. Do not document future or to be be developed features.
Your goal is documentation.
Avoid adding code snippets.
"""
print("Input size:", len(task))
# Run the evolutive solver
evolutive_problem_solver(
    coder_model,       # The LLM to use
    task,              # The task description
    agent_steps=54,    # Number of steps each agent can take
    steps=4,           # Number of evolutionary iterations
    start_now=True,    # Start from scratch
    fileext='.md',     # File extension for outputs
    tools=tools        # Tools available to the agents
)
```

The source code above shows one of the core strengths of Beyond Python Smolagents: Its ability to work with codebases across multiple languages to generate and update documentation automatically. The `source_code_to_string` and `pascal_interface_to_string` tools are particularly useful here, allowing agents to ingest the codebase structure and content.

For complex documentation tasks, such as generating a comprehensive README from a large project, you should leverage advanced techniques provided by `evolutive_problem_solver`.

## Available agent tools

The `bp_tools.py` files provides a suite of functions and classes that can be used as tools by agents. This list details key tools and a brief description of their function:

*   `run_os_command(str_command: string, timeout: integer)`: Executes an arbitrary command in the host operating system's shell (e.g., `ls`, `cd`, `mkdir`, `pip install <package>`, `apt-get update`). Returns the standard output from the command. Use with extreme caution due to security implications.
*   `compile_and_run_pascal_code(pasfilename: string, timeout: integer)`: Compiles and executes a Free Pascal source file (`.pas`). Accepts standard Free Pascal compiler options via the `pasfilename` string. Returns the output of the compiled program.
*   `run_php_file(filename: string, timeout: integer)`: Executes a PHP script file (`.php`) using the installed PHP interpreter. Returns the standard output generated by the script.
*   `source_code_to_string(folder_name: string)`: Recursively scans a specified folder and its subfolders for common source code file types (.py, .pas, .php, .inc, .txt, .md). It reads their content and concatenates them into a single string, structured using `<file filename="...">...</file>` XML-like tags. This is invaluable for giving an agent a comprehensive view of a project's source code for documentation, analysis, or refactoring tasks.
*   `string_to_source_code(string_with_files: string, output_base_dir: string = '.', overwrite: boolean = True, verbose: boolean = False)`: Performs the inverse operation of `source_code_to_string`. It parses a structured string (like the output of `source_code_to_string`) and recreates the specified files and directory structure within the `output_base_dir`. Useful for agents generating multiple code or documentation files.
*   `pascal_interface_to_string(folder_name: string)`: Specifically scans Pascal source files in a folder and extracts only the content located within the `interface` section of units, ignoring comments and strings. The extracted content is returned in a string structured with `<pascal_interface filename="...">...</pascal_interface>` tags. Helps agents understand Pascal unit dependencies.
*   `save_string_to_file(content: string, filename: string)`: Writes the given string `content` to the specified `filename`. If the file exists, it is overwritten. A fundamental tool for agents to output generated text or code.
*   `load_string_from_file(filename: string)`: Reads the entire content of the specified `filename` and returns it as a single string. Allows agents to read existing files.
*   `copy_file(source_filename: string, dest_filename: string)`: Copies the file located at `source_filename` to `dest_filename`. Standard file system copy operation.
*   `get_file_size(filename: string)`: Returns the size of a specified file in bytes as an integer. Useful for file management tasks.
*   `replace_on_file(filename: string, old_value: string, new_value: string)`: Reads the content of `filename`, replaces all occurrences of `old_value` with `new_value` in the content, and writes the modified content back to the same file. Returns the modified content string. Useful for in-place file patching.
*   `replace_on_file_with_files(filename: string, file_with_old_value: string, file_with_new_value: string)`: Reads content from `file_with_old_value` and `file_with_new_value`, then replaces all occurrences of the old content with the new content within the `filename` file. Returns the modified content string of `filename`.



