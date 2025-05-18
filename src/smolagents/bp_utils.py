import time
import ast
import re
from textwrap import dedent

def delay_execution_10(pagent, **kwargs) -> bool:
    """
    Delays the execution for 10 seconds.
    """
    time.sleep(10)
    return True

def delay_execution_30(pagent, **kwargs) -> bool:
    """
    Delays the execution for 30 seconds.
    """
    time.sleep(30)
    return True

def delay_execution_120(pagent, **kwargs) -> bool:
    """
    Delays the execution for 120 seconds.
    """
    time.sleep(120)
    return True

def bp_parse_code_blobs(text: str) -> str:
    """Extract code blocs from the LLM's output.

    If a valid code block is passed, it returns it directly.

    Args:
        text (`str`): LLM's output text to parse.

    Returns:
        `str`: Extracted code block.

    Raises:
        ValueError: If no valid code block is found in the text.
    """
    pattern = r"```(?:runpy)\s*\n(.*?)\n```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return "\n\n".join(match.strip() for match in matches)
    # Maybe the LLM outputted a code blob directly
    try:
        ast.parse(text)
        return text
    except SyntaxError:
        raise ValueError(
            dedent(
                f"""
Your code snippet is invalid, because the regex pattern {pattern} was not found in it.
Here is your code snippet:
{text}
Make sure to include code with the correct pattern, for instance:
Thoughts: Your thoughts
Code:
```runpy
# Your python code here
```<end_code>
"""
            ).strip()
        )
