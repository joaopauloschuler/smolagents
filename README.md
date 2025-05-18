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
**Beyond Python Smolagents** is a fork of the original [smolagents](https://github.com/huggingface/smolagents) that extends its original abilities to code in pascal, php and other languages.
It also excels at generating or updating documentation for existing code bases including writing readme files. It also does a good job at researching and experimenting ideas.
**Contrary to the original implementation, this implementation allows agents to take full control of the host environment. ONLY RUN THIS CODE INSIDE A VMs OR DOCKER WITHOUT ANY IMPORTANT INFORMATION ON IT. USE IT AT YOUR OWN RISK!**

## Installation
```
!pip install litellm==1.67.2
!git clone -b development5 https://github.com/joaopauloschuler/beyond-python-smolagents smolagents
!pip install ./smolagents[litellm]
```

## Basic usage (single agent)

```
import smolagents
from smolagents.bp_tools import *
from smolagents.bp_utils import *
from smolagents.bp_thinkers import *
from smolagents import HfApiModel, LiteLLMModel, LogLevel
from smolagents import CodeAgent, MultiStepAgent, ToolCallingAgent
from smolagents import PythonInterpreterTool, VisitWebpageTool, UserInputTool, DuckDuckGoSearchTool
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

the_boss = CodeAgent(model=coder_model, tools = tools, add_base_tools=True)
the_boss.run("Code, test and debug something that will impress me!")
```

## Use heavy thinking
This method combines evolutive computing, genetic algorithms and agents to produce a final result. This is the most expensive method but it delivers the best results. This is a source code example to produce a readme from an existing code base:
```
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

As you are required to run python code at each step, for intermediate steps, you can follow this example:

Code:
```py
print('I updated the first paragraph, this is so interesting, I have just realized how much ... , I will next review ..., thanks to this insight, I now realize ..., knowledge is incremental ...')
```<end_code>

When you finish, you can use this example (if you like):
Code:
```py
final_answer('I have finished the task. YAY!')
```<end_code>

You will write the documentation in a technical and non commercial language.
You contribution will be helping others to understand how to use this project and its inner workings so future
developers will be able to build on the top of it.
It would be fantastic if you could add to the documentation ideas about to solve problems using this project. Solving ideas about how to use it to solve problems in the real world.
For saving documentation, use the tags <savetofile> and <appendtofile>. Trying to save documentation via python code is just too hard and error prone.
When asked to test or review documentation, make sure that refered files or functions do actually exist. This is to prevent broken links.
Your documentation should focus on existing features only. Do not document future or to be be developed features.
Your goal is documentation.
Avoid adding code snippets.
"""
print("Input size:", len(task))
evolutive_problem_solver(coder_model, task, agent_steps=54, steps=4, start_now=True, fileext='.md', tools=tools)
```
