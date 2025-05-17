from .tools import *
from .bp_tools import *
from .bp_utils import *
from .agents import *
import shutil

STEP_CALLBACKS = [delay_execution_30]

def evolutive_problem_solver(p_coder_model,
  task_str,
  agent_steps:int,
  steps:int,
  system_prompt,
  start_now=True,
  fileext:str='.py',
  tools=[load_string_from_file, source_code_to_string],
  executor_type='exec',
  add_base_tools=True,
  step_callbacks=STEP_CALLBACKS,
  log_level = LogLevel.DEBUG,
  ):
  def get_local_agent():
    coder_agent = CodeAgent(
      tools=tools,
      model=p_coder_model,
      additional_authorized_imports=['*'],
      add_base_tools=add_base_tools,
      max_steps=agent_steps,
      step_callbacks=step_callbacks,
      executor_type=executor_type
      ) # , planning_interval=3
    coder_agent.system_prompt(coder_agent, system_prompt)
    coder_agent.logger.log_level = log_level
    return coder_agent

  def test_and_refine(local_agent, solution_file):
    print('Refine 1')
    task_description="""Thank you!
Please detail what did you change.
"""
    local_agent.run(task_description, reset=False)
    print('Refine 2')
    task_description="""Thank you! Love your work!
In the case that you believe that you have not properly reviewed/tested it yet, please review/test your own solution now.
After you test and bug fix it, please save the full updated source code that solves the task described in <task></task> into the file '"""+solution_file+"""'.
When you have finished, call the function final_answer("Task completed! YAY!") please.
"""
    local_agent.run(task_description, reset=False)
    print('Refine 3')
    task_description="""Thank you again!
In the case that you have any advice that you would like to give to yourself the next time you have to code anything, call the function final_answer
with any advice that you would like to give to yourself to a future version of yourself.
"""
    print('Refine 4')
    new_advice = str(local_agent.run(task_description, reset=False))
    # if new_advice len is bigger then zero
    if (len(new_advice) > 0):
      # append the file advices.notes with the new advice
      append_string_to_file("""
---
"""+new_advice, 'advices.notes')
    # end of test_and_refine


  local_task_description = 'The task description is enclosed in the tags <task></task>:' + \
    '<task>'+task_str+'</task>'
  valid_solutions=['solution1','solution2','solution3']
  motivation = \
      " Please, try to produce a solution that is as extensive, detailed and rich as you can." + \
      " Feel free to show your intelligence with no restrains. It is the time for you to show the world your full power." + \
      " Feel free to use your creativity and true hidden skills."
  if start_now:
    local_agent = get_local_agent()
    local_agent.run(local_task_description + motivation + ' Save the solution into the file solution1'+fileext, reset=True)
    test_and_refine(local_agent, 'solution1'+fileext)
    local_agent.run(local_task_description + motivation + ' Save the solution into the file solution2'+fileext, reset=True)
    test_and_refine(local_agent, 'solution2'+fileext)
    local_agent.run(local_task_description + motivation + ' Save the solution into the file solution3'+fileext, reset=True)
    test_and_refine(local_agent, 'solution3'+fileext)
  for i in range(steps):
    try:
      local_agent = get_local_agent()
      # !rm *.txt
      # !rm *.json
      print('Evolutive problem solver is starting:', i)
      task_description=""" Hello super-intelligence!
We have 3 possible solutions for the task <task>"""+local_task_description+"""</task>
Please explain the advantages and disvantages of each solution.
This environment is simulated. Therefore, real user inputs will not work.
No real person can interact with this code.
The more features, the better it is. Always give preference to source
codes with more features.
The 3 solutions are given in the tags:
<solution1></solution1>
<solution2></solution2>
<solution3></solution3>

These are the solutions:
<solution1>"""+load_string_from_file('solution1'+fileext)+"""</solution1>
<solution2>"""+load_string_from_file('solution2'+fileext)+"""</solution2>
<solution3>"""+load_string_from_file('solution3'+fileext)+"""</solution3>

YOUR TASK PRODUCING A TEXT ABOUT THE SOLUTIONS.

You'll finish your task with something similar to:

final_answer(" my evaluations here ").

DO NOT CODE ANYTHING EXCEPT FOR CALLING final_answer WITH TEXT INSIDE ONLY.

"""
      local_agent.run(task_description, reset=True)
      # do not mix solutions at the end of the work.
      if (i<steps-2):
        task_description="""Thank you very much.
Would we build something better or more interesting or more useful than each individual solution by mixing parts of them into a new solution?
If you believe that mixing is a good idea, you'll call the function final_answer('yes').
If you believe that this is not a good idea, you'll call the function final_answer('no').
"""
        should_mix = (local_agent.run(task_description, reset=False)=='yes')
        if should_mix:
          solution_file = 'solution2'+fileext
          task_description="""Thank you very much.
Please mix parts of the solutions into a new solution.
Save the new solution into the file """+solution_file+""".
When you have finished, call the function final_answer("Task completed! YAY!") please."""
          local_agent.run(task_description, reset=False)
          test_and_refine(local_agent, solution_file)
          # when mixing, we don't try to pick the best of 3 solutions.
          continue

      task_description="""Thank you very much.
If you believe that the solution 1 is the best, you'll call the function final_answer('solution1').
If you believe that the solution 2 is the best, you'll call the function final_answer('solution2').
If you believe that the solution 3 is the best, you'll call the function final_answer('solution3').
"""
      selected_solution = local_agent.run(task_description, reset=False)
      if selected_solution in valid_solutions:
        best_solution = selected_solution+fileext
        copy_file(best_solution, 'best_solution.best')
        if i<steps-1:
          # the past best solution is always the solution3.py
          # !cp best_solution.py solution3.py
          shutil.copyfile('best_solution.best', 'solution3'+fileext)
          for alternatives_cnt in range(2):
            solution_cnt = alternatives_cnt+1
            solution_file = 'solution'+str(solution_cnt)+fileext
            task_description=""" Hello super-intelligence!
"""+local_task_description+"""'.
The current solution for this task is enclosed in the tags <solution></solution>:
<solution>"""+load_string_from_file('best_solution.best')+"""</solution>
A previous version of yourself wrote the following advices in the tags <advices></advices>:
<advices>"""+load_string_from_file('advices.notes')+"""</advices>
Your next step is suggesting improvements. Feel free to say whatever you would like.
DO NOT CODE ANYTHING except for providing final via

final_answer(" your suggestions ").

YOUR TASK IS SUGGESTING IMPROVEMENTS.

This environment is simulated. Therefore, real user inputs will not work.  Sending emails will also not work.

No real person can interact with this code.
"""
            local_agent.run(task_description, reset=True)
            local_agent.run("From the proposed improvements, please randomly pick one.", reset=False)
            task_description="""Thank you. Please code the randomly selected improvement."""+motivation+"""
When you finish, call the function

final_answer("I have finished the task.").

Your goal is not to start a new solution. Your goal is to update the existing solution.
THE FULL SOLUTION IS INTENDED TO BE PLACED IN A SINGLE FILE. DO NOT CREATE AN ARCHITECTURE WITH MULTIPLE FILES!"""
            if alternatives_cnt==0:
              task_description += """
As you are very intelligent, try to be bold by adding as much improvement to the existing solution.
Try to add as much as you can in your first attempt to modify the existing solution."""
            local_agent.run(task_description, reset=False)
            local_agent.run("Do you need to review/test it a bit more?", reset=False)
            task_description="""Fantastic! Save the full updated solution that solves the task described in <task></task> into the file '"""+solution_file+"""'.
YOU ARE REQUIRED TO SAVE THE FULL SOLUTION AND NOT JUST THE PORTIONS THAT YOU HAVE MODIFIED.
You can follow this example:
<savetofile filename="""+solution_file+""">
print("your source code or text here")
</savetofile>
```py
final_answer("Task completed! YAY!")
```<end_code>
"""
            local_agent.run(task_description, reset=False)
            # refine solution code here
            test_and_refine(local_agent, solution_file)

            if get_file_size('best_solution.best') > get_file_size(solution_file):
              task_description=""" Hello super-intelligence!
We have 2 portions of the solution about: '"""+local_task_description+"""'.
The base solution for this task is enclosed in the tags <basesolution></basesolution>:
<basesolution>"""+load_string_from_file('best_solution.best')+"""</basesolution>
The new solution is enclosed in the tags <newcode></newcode>:
<newcode>"""+load_string_from_file(solution_file)+"""</newcode>
YOUR TASK IS TO MERGE BOTH SOLUTIONS.
When you finish merging, you will call:
final_answer("I have merged both solutions").

This environment is simulated. Therefore, real user inputs will not work. Sending emails will also not work.

No real person can interact with this solution at this moment.
"""
              local_agent.run(task_description, reset=True)
              task_description="""Fantastic! Save the full merged solution into the file '"""+solution_file+"""'.
YOU ARE REQUIRED TO SAVE THE FULL SOLUTION AND NOT JUST THE PORTIONS THAT YOU HAVE MODIFIED.
You can follow this example:
<savetofile filename="""+solution_file+""">
print("your source code or text here")
</savetofile>
```py
final_answer("Task completed! YAY!")
```<end_code>
"""
              local_agent.run(task_description, reset=False)

    except:
      print('ERROR')
  return load_string_from_file('best_solution.py')
