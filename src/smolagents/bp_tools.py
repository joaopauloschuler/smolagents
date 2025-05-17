# beyond python tools

from .tools import tool, Tool, VisitWebpageTool
import os
import subprocess
import shlex
import re

@tool
def save_string_to_file(content: str, filename: str) -> bool:
    """
    Saves the given content to the specified file.
    Args:
      content: str
      filename: str
    """
    with open(filename, "w") as text_file:
      text_file.write(content)
    return True

@tool
def append_string_to_file(content: str, filename: str) -> bool:
    """
    Appends the given content to the specified file.
    Args:
      content: str
      filename: str
    """
    with open(filename, "a") as text_file:
      text_file.write(content)
    return True

@tool
def load_string_from_file(filename: str) -> str:
    """
    Loads the content from the specified file.
    Args:
      filename: str
    """
    content = ''
    if os.path.isfile(filename):
      with open(filename, "r") as text_file:
        content = text_file.read()
    return content

@tool
def copy_file(source_filename: str, dest_filename: str) -> bool:
    """
    Copy the source_filename into the dest_filename.
    Args:
      source_filename: str
      dest_filename: str
    """
    save_string_to_file(load_string_from_file(source_filename), dest_filename)
    return True

@tool
def replace_on_file(filename: str, old_value: str, new_value: str) -> str:
    """
    Replace the old_value with the new_value in the filename.
    This function is useful for fixing source code directly on file.
    It returns the updated file.
    This is its implementation:
    str_code = load_string_from_file(filename)
    new_code = str_code.replace(old_value, new_value)
    save_string_to_file(new_code, filename)
    return new_code
    Args:
      filename: str
      old_value: str
      new_value: str
    """
    str_code = load_string_from_file(filename)
    new_code = str_code.replace(old_value, new_value)
    save_string_to_file(new_code, filename)
    return new_code

@tool
def replace_on_file_with_files(filename: str, file_with_old_value: str, file_with_new_value: str) -> str:
    """
    Replace the content from the file_with_old_value with the content from the file_with_new_value in the filename.
    This function is useful for fixing source code directly on the file specified by filename.
    It returns the updated file.

    This is its implementation:
    str_code = load_string_from_file(filename)
    old_value = load_string_from_file(file_with_old_value)
    new_value = load_string_from_file(file_with_new_value)
    new_code = str_code.replace(old_value, new_value)
    save_string_to_file(new_code, filename)
    return new_code

    Args:
      filename: str
      file_with_old_value: str
      file_with_new_value: str
    """
    str_code = load_string_from_file(filename)
    old_value = load_string_from_file(file_with_old_value)
    new_value = load_string_from_file(file_with_new_value)
    new_code = str_code.replace(old_value, new_value)
    save_string_to_file(new_code, filename)
    return new_code

@tool
def get_file_size(filename: str) -> int:
    """
    Returns the size of the file in bytes.
    Args:
      filename: str
    """
    if os.path.isfile(filename):
      return os.path.getsize(filename)
    return 0

@tool
def force_directories(file_path: str) -> None:
    """
    Extracts the directory path from a full file path and creates
    the directory structure if it does not already exist.

    Args:
        file_path: The full path to a file (e.g., '/path/to/some/directory/file.txt').
                   Can be a relative or absolute path.
    """
    # Use os.path.dirname() to get the directory part of the path.
    # This works for both files and directories (if path ends with a slash).
    directory_path = os.path.dirname(file_path)

    # If the path ends with a directory separator or refers to the current
    # directory or root, dirname might return an empty string or '.'.
    # os.makedirs handles these cases correctly.
    # os.makedirs() with exist_ok=True will create the directories recursively
    # if they don't exist, and will do nothing if they already exist.
    if directory_path: # Only attempt to create if directory_path is not empty
      os.makedirs(directory_path, exist_ok=True)

@tool
def run_os_command(str_command: str, timeout: int = 60) -> str:
    """
    Runs an OS command and returns the output.
    Args:
      str_command: str
      timeout: int
    """
    command = shlex.split(str_command)
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        outs, errs = proc.communicate(input="", timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        outs, errs = proc.communicate()
    result = ""
    if outs is not None: result += outs.decode('utf-8')
    if errs is not None: result += errs.decode('utf-8')
    return result

@tool
def run_php_file(filename: str, timeout: int = 60) -> str:
    """
    Runs a PHP file and returns the output.
    Args:
      filename: str
      timeout: int
    """
    return run_os_command("php " + filename, timeout)

@tool
def compile_and_run_pascal_code(pasfilename: str, timeout: int = 60) -> str:
  """
    Compiles and runs pascal code. pasfilename contains the filename to be compiled.
    If you need to pass additional parameters such as to include existing units, you can include into the pasfilename parameter.
    This is an example to compile a file named myfile.pas with the units from neural-api/neural:
    compile_and_run_pascal_code('-Funeural-api/neural/ myfile.pas', 120)
    Args:
      pasfilename: str
      timeout: int
  """
  filename = 'compiled'
  if os.path.exists(filename):
      os.remove(filename)
  print(run_os_command("fpc -O3 -Mobjfpc "+pasfilename+' -o'+filename, timeout=timeout))
  if os.path.exists(filename):
    print(run_os_command("./compiled", timeout=timeout))
  else:
    print('Compilation error.')

@tool
def source_code_to_string(folder_name: str) -> str:
    """
    Scans a folder and subfolders for specific source code file types (.py, .txt, .pas, .inc, .md),
    concatenates their content into a single string with XML-like tags,
    and orders the files in the output string (.md first, then .txt, then others),
    using the base filename in the tag.

    Includes robust error handling for file reading and deterministic sorting.

    Args:
        folder_name: The path to the root folder to scan.

    Returns:
        A single string containing the concatenated content of the scanned files,
        formatted with <file filename="...">...</file> tags, or an empty string
        if the folder does not exist or no relevant files are found.
    """
    if not os.path.isdir(folder_name):
        print(f"Error: Folder '{folder_name}' not found.")
        return ""

    relevant_files_info = []
    allowed_extensions = ('.py', '.txt', '.pas', '.inc', '.md', '.pp', '.lpr', '.dpr', '.lfm', '.dfm', '.php', '.c', '.cc', '.cpp')

    for root, _, files in os.walk(folder_name):
        for filename in files:
            filepath = os.path.join(root, filename)
            _, file_extension = os.path.splitext(filename)
            file_extension_lower = file_extension.lower()

            if file_extension_lower in allowed_extensions:
                # Store full path for sorting, base filename for output tag, and extension
                relevant_files_info.append({
                    'filepath': filepath,
                    'filename': filename, # Use base filename for the tag
                    'extension': file_extension_lower
                })

    # Custom sorting key: .md files first (0), then .txt files (1), then others (2).
    # Within each group, sort alphabetically by full path for consistency (deterministic).
    def sort_key(file_info):
        extension = file_info['extension']
        filepath = file_info['filepath']
        if extension == '.md':
            primary_key = 0
        elif extension == '.txt':
            primary_key = 1
        else:
            primary_key = 2
        return (primary_key, filepath)

    # Sort the list of file info dictionaries
    relevant_files_info.sort(key=sort_key)

    output_string_parts = []

    for file_info in relevant_files_info:
        filepath = file_info['filepath']
        filename_for_tag = filepath.replace(folder_name+'/','')
        content = ""
        try:
            # Attempt to read file content, trying multiple common encodings
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                 try:
                    # Try a different common encoding if utf-8 fails
                    with open(filepath, 'r', encoding='latin-1') as f:
                        content = f.read()
                 except Exception as e:
                    # If both common encodings fail, report the error
                    print(f"Could not read file {filepath} due to encoding issues or other errors.")
                    content = f"Error reading file content (encoding or other issue): {e}"

        except FileNotFoundError:
             # This should ideally not happen since os.walk found it, but included for robustness
             print(f"Error: File not found unexpectedly: {filepath}")
             content = "Error: File not found unexpectedly."

        except Exception as e:
            # Catch any other potential reading errors
            print(f"An unexpected error occurred while reading file {filepath}: {e}")
            content = f"An unexpected error occurred while reading: {e}"


        # Format the content block using the base filename
        formatted_block = f'<file filename="{filename_for_tag}">\n{content}\n</file>'
        output_string_parts.append(formatted_block)


    # Join all formatted blocks with a newline separator between blocks
    return '\n'.join(output_string_parts)

@tool
def string_to_source_code(string_with_files: str, output_base_dir: str = '.', overwrite: bool = True, verbose: bool = True) -> None:
    """
    Parses a string containing concatenated file content with <file filename="...">...</file> tags,
    and recreates the files and directories in a specified base directory.
    This function does the opposite work of the function source_code_to_string.

    Args:
        string_with_files: The input string containing file data.
        output_base_dir: The base directory where files should be saved. Defaults to the current directory.
        overwrite: If True, overwrite existing files. If False, skip saving the file if it already exists.
        verbose: If True, print status and error messages during processing.
    """
    if verbose:
        print("Starting file reconstruction process...")
        print(f"Target output base directory: {os.path.abspath(output_base_dir)}")
        print(f"Overwrite existing files: {overwrite}")

    # Regex to find file blocks.
    # - <file filename="([^"]+?)"> : Matches the opening tag and captures the filename attribute
    #   - ([^"]+?) : Group 1, captures one or more characters that are NOT a double quote (non-greedy)
    # - (.*?) : Group 2, captures the content (non-greedy). Uses re.DOTALL to match newlines.
    # - </file> : Matches the closing tag
    # This regex is robust for filenames within double quotes and captures the content exactly
    # as it appears between the tags (including any surrounding newlines added by the source function).
    file_pattern = re.compile(r'<file filename="([^"]+?)">\n(.*?)\n</file>', re.DOTALL)

    matches = file_pattern.findall(string_with_files)

    if not matches:
        if verbose:
            print("No file blocks found in the input string.")
        return

    if verbose:
        print(f"Found {len(matches)} file blocks.")

    successful_saves = 0
    skipped_saves = 0
    failed_saves = 0

    for relative_filepath, content in matches:
        # Construct the full output path using the specified base directory
        output_filepath = os.path.join(output_base_dir, relative_filepath)

        if verbose:
            print(f"\nProcessing file block for: {relative_filepath}")
            print(f"Target output path: {output_filepath}")

        # Ensure the directory exists for the output file
        output_dir = os.path.dirname(output_filepath)
        if output_dir and not os.path.exists(output_dir): # Only create directory if it's not the root and doesn't exist
            if verbose:
                print(f"Ensuring directory exists: {output_dir}")
            try:
                # exist_ok=True prevents an error if the directory already exists
                os.makedirs(output_dir, exist_ok=True)
                if verbose:
                    print(f"Directory ensured: {output_dir}")
            except OSError as e:
                if verbose:
                    print(f"Error creating directory {output_dir}: {e}")
                    print(f"Skipping file {output_filepath} due to directory creation error.")
                failed_saves += 1
                continue # Skip saving this file

        # Check if file exists and if overwrite is disabled
        if os.path.exists(output_filepath) and not overwrite:
            if verbose:
                print(f"File already exists and overwrite is False. Skipping file: {output_filepath}")
            skipped_saves += 1
            continue # Skip saving this file

        # Attempt to save file
        if verbose:
            print(f"Attempting to save file: {output_filepath}")
        try:
            # Use utf-8 encoding for writing
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            if verbose:
                print(f"Successfully saved file: {output_filepath}")
            successful_saves += 1
        except IOError as e:
            if verbose:
                print(f"Error writing file {output_filepath}: {e}")
            failed_saves += 1
        except Exception as e:
            if verbose:
                 print(f"An unexpected error occurred while writing file {output_filepath}: {e}")
            failed_saves += 1

    if verbose:
        print("\nFile reconstruction process finished.")
        print(f"Summary: {successful_saves} files saved successfully, {skipped_saves} skipped, {failed_saves} failed.")

@tool
def pascal_interface_to_string(folder_name: str) -> str:
    """
    Scans a folder and subfolders for Pascal source code file types
    (.pas, .inc, .pp, .lpr, .dpr), extracts the content between the 'interface'
    and 'implementation' keywords (case-insensitive) using a robust stateful
    parser that correctly ignores content within comments and strings.
    Concatenates the extracted content into a single string with
    <pascal_interface filename="...">...</pascal_interface> tags.

    If an 'implementation' section is not found after 'interface', it extracts
    from 'interface' to the end of the file. If 'interface' is not found,
    it extracts nothing for that file's interface section. Handles basic
    encoding issues. Reports file reading errors within the output tags.

    Args:
        folder_name: The path to the root folder to scan.

    Returns:
        A single string containing the concatenated interface sections,
        formatted with tags, or an empty string if the folder does not
        exist or no relevant files are found.
    """
    if not os.path.isdir(folder_name):
        # Print to execution log for debugging/info, but return empty string as per inspired function
        print(f"Error: Folder '{folder_name}' not found.")
        return ""

    relevant_files = []
    # Added .pp, .lpr, .dpr based on common Pascal file types
    allowed_extensions = ('.pas', '.inc', '.pp', '.lpr', '.dpr')

    for root, _, files in os.walk(folder_name):
        for filename in files:
            filepath = os.path.join(root, filename)
            _, file_extension = os.path.splitext(filename)
            file_extension_lower = file_extension.lower()

            if file_extension_lower in allowed_extensions:
                relevant_files.append(filepath)

    # Sort files alphabetically by full path for deterministic output
    relevant_files.sort()

    output_parts = []

    for filepath in relevant_files:
        # Determine the relative path for the tag filename attribute
        relative_filepath = os.path.relpath(filepath, folder_name)
        content = ""
        interface_content = ""
        read_error = None

        try:
            # Attempt to read file content, trying multiple common encodings
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                 try:
                    # Try a different common encoding if utf-8 fails
                    with open(filepath, 'r', encoding='latin-1') as f:
                        content = f.read()
                 except Exception as e:
                    read_error = f"Could not read file due to encoding issues or other errors: {e}"
                    print(f"Error reading file {filepath}: {read_error}") # Print to execution log


        except FileNotFoundError:
             # Should not happen based on os.walk, but included for robustness
             read_error = "File not found unexpectedly."
             print(f"Error reading file {filepath}: {read_error}") # Print to execution log

        except Exception as e:
            # Catch any other potential reading errors
            read_error = f"An unexpected error occurred while reading: {e}"
            print(f"An unexpected error occurred while reading file {filepath}: {e}") # Print to execution log

        if read_error:
            # If read failed, add an error tag and skip to the next file
             formatted_block = f'<pascal_interface filename="{relative_filepath}">\nError reading file: {read_error}\n</pascal_interface>'
             output_parts.append(formatted_block)
             continue # Skip to the next file

        # --- Robust Extraction Logic (Stateful Character Parser from Solution 2) ---
        interface_section_content_chars = [] # Use a list to build the string efficiently
        is_interface_found = False
        is_implementation_found = False # Stop when implementation is found after interface

        in_curly_comment = False
        in_star_comment = False
        in_string = False
        in_line_comment = False

        i = 0
        while i < len(content):
            char = content[i]
            chars_left = len(content) - i

            # Check for end of line comment
            if in_line_comment and char == '\n':
                in_line_comment = False
                # Newline terminates the line comment state. It should be included if capturing.
                if is_interface_found and not is_implementation_found:
                     interface_section_content_chars.append(char)
                i += 1
                continue
            elif in_line_comment:
                 # Inside line comment, do not process keywords or toggle states.
                 # Include character in output if capturing interface section.
                 if is_interface_found and not is_implementation_found:
                      interface_section_content_chars.append(char)
                 i += 1
                 continue

            # State transitions for block comments and strings (only if not in line comment)
            if not in_line_comment:
                # Handle string state (simplified: toggle on single quote)
                if char == "'":
                    in_string = not in_string
                    # Include the quote if capturing
                    if is_interface_found and not is_implementation_found:
                         interface_section_content_chars.append(char)
                    i += 1
                    continue

                # Handle } for curly comment end
                if in_curly_comment and char == '}':
                    in_curly_comment = False
                    # Include the bracket if capturing
                    if is_interface_found and not is_implementation_found:
                         interface_section_content_chars.append(char)
                    i += 1
                    continue

                # Handle *} for star comment end
                if in_star_comment and chars_left >= 2 and content[i:i+2] == '*}':
                     in_star_comment = False
                     # Include the bracket if capturing
                     if is_interface_found and not is_implementation_found:
                          interface_section_content_chars.extend(content[i:i+2])
                     i += 2
                     continue

                # Handle { for curly comment start
                if char == '{' and not in_star_comment and not in_string: # { cannot start a curly comment inside star comment or string
                    # Check if it's a star comment {*
                    if chars_left >= 2 and content[i+1] == '*':
                         # This is {*, handled below
                         pass # Let the next check handle {*
                    else: # This is {
                        in_curly_comment = True
                        # Include the bracket if capturing
                        if is_interface_found and not is_implementation_found:
                             interface_section_content_chars.append(char)
                        i += 1
                        continue

                # Handle {* for star comment start
                if chars_left >= 2 and content[i:i+2] == '{*' and not in_curly_comment and not in_string: # {* cannot start inside curly comment or string
                     in_star_comment = True
                     # Include the marker if capturing
                     if is_interface_found and not is_implementation_found:
                          interface_section_content_chars.extend(content[i:i+2])
                     i += 2
                     continue

                # Handle // for line comment start
                if chars_left >= 2 and content[i:i+2] == '//' and not in_curly_comment and not in_star_comment and not in_string:
                    in_line_comment = True
                    # Include the marker if capturing
                    if is_interface_found and not is_implementation_found:
                         interface_section_content_chars.extend(content[i:i+2])
                    i += 2
                    continue

            # --- Keyword Detection (only when not in comment or string or line comment) ---
            # Only check for keywords if none of the comment/string states are active
            if not in_curly_comment and not in_star_comment and not in_string and not in_line_comment:
                # Check for 'interface' keyword
                if not is_interface_found and chars_left >= len('interface') and content[i:i+len('interface')].lower() == 'interface':
                     # Check for word boundary - simplified check using isalnum() and _
                     is_word_boundary_before = (i == 0 or not content[i-1].isalnum() and content[i-1] != '_')
                     is_word_boundary_after = (i + len('interface') == len(content) or not content[i+len('interface')].isalnum() and content[i+len('interface')] != '_')

                     if is_word_boundary_before and is_word_boundary_after:
                         is_interface_found = True
                         # Start capturing content *after* the keyword 'interface'
                         # Skip the keyword itself
                         i += len('interface')
                         # Skip any immediate whitespace after the keyword
                         while i < len(content) and content[i].isspace():
                             i += 1
                         continue # Continue loop from the character after 'interface' + whitespace

                # Check for 'implementation' keyword (only if interface was found)
                if is_interface_found and not is_implementation_found and chars_left >= len('implementation') and content[i:i+len('implementation')].lower() == 'implementation':
                     # Check for word boundary
                     is_word_boundary_before = (i == 0 or not content[i-1].isalnum() and content[i-1] != '_')
                     is_word_boundary_after = (i + len('implementation') == len(content) or not content[i+len('implementation')].isalnum() and content[i+len('implementation')] != '_')

                     if is_word_boundary_before and is_word_boundary_after:
                        is_implementation_found = True
                        # Stop processing this file's content as we found the end marker
                        # Do NOT include 'implementation' keyword or anything after it
                        break

            # --- Content Capture ---
            # If we are inside the interface section AND the 'implementation' keyword hasn't been found yet,
            # append the current character to the output. This captures everything between 'interface' and 'implementation',
            # including comments and strings within that section.
            if is_interface_found and not is_implementation_found:
                 interface_section_content_chars.append(char)

            # Move to the next character if not handled by multi-char sequence above
            i += 1

        # --- End of Extraction Logic ---

        # Join the captured characters into a string
        interface_content = "".join(interface_section_content_chars).strip() # Strip leading/trailing whitespace

        # Construct the output block for this file using the tag format from Solution 1
        # Only add a block if 'interface' was actually found in the file
        if is_interface_found:
             formatted_block = f'<pascal_interface filename="{relative_filepath}">\n{interface_content}\n</pascal_interface>'
             output_parts.append(formatted_block)


    # Join all formatted blocks with a newline separator between blocks
    # Add an extra newline after each block for better readability in the final output
    return '\n\n'.join(output_parts)

@tool
def trim_right_lines(multi_line_string: str) -> str:
  """
  This function will do a right trim in all lines of the string.
  Args:
    multi_line_string: str
  """
  lines = multi_line_string.splitlines()
  # Trim only the right side of each line
  trimmed_lines = [line.rstrip() for line in lines]
  # Join the lines back together
  trimmed_string = '\n'.join(trimmed_lines)
  return trimmed_string


class Summarize(Tool):
    name = "summarize"
    description = """This subassistant will return the summary of a string. Use this subassistant as much as you can with the goal to save your own context size.
You can restart the chat by setting restart_chat to True or ask for more details by setting restart_chat to False."""
    inputs = {
        "text_str": {
            "type": "string",
            "description": "Input text to be summarized.",
        },
        "restart_chat": {
            "type": "boolean",
            "description": "When true, forgets the previous chat.",
            "nullable" : True
        }
    }
    output_type = "string"
    agent = None

    def __init__(self, agent):
        super().__init__()
        self.agent = agent

    def forward(self, text_str: str, restart_chat: bool = True) -> str:
        task_str = 'Hello super-intelligence! Please provide a summary for the following as a string: '+ text_str
        result = self.agent.run(task_str, reset=restart_chat)
        return result
    
class SummarizeUrl(Tool):
    name = "summarize_url"
    description = """This subassistant will return the summary of a web page given its url as a string. Use this subassistant as much as you can with the goal to save your own context size.
  You can restart the chat by setting restart_chat to True or ask for more details by setting restart_chat to False."""
    inputs = {
        "url": {
            "type": "string",
            "description": "url to be summarized.",
        },
        "restart_chat": {
            "type": "boolean",
            "description": "When true, forgets the previous chat.",
            "nullable" : True
        }
    }
    output_type = "string"
    agent = None

    def __init__(self, agent):
        super().__init__()
        self.agent = agent

    def forward(self, url: str, restart_chat: bool = True) -> str:
        LocalVistWebPageTool = VisitWebpageTool()
        task_str = 'Hello super-intelligence! Please write all the information in plain English text without tags from the following as a string (do not use python code except for the final answer): '+ LocalVistWebPageTool(url)[:15000]
        result = self.agent.run(task_str, reset=restart_chat)
        return result
    
class SummarizeLocalFile(Tool):
        name = "summarize_local_file"
        description = """This function will return the summary of a local file. Use this subassistant as much as you can with the goal to save your own context.
    You can restart the chat by setting restart_chat to True or ask for more details by setting restart_chat to False."""
        inputs = {
            "filename": {
                "type": "string",
                "description": "File in the file system.",
            },
            "restart_chat": {
                "type": "boolean",
                "description": "When true, forgets the previous chat.",
                "nullable" : True
            }
        }
        output_type = "string"
        agent = None

        def __init__(self, agent):
            super().__init__()
            self.agent = agent

        def forward(self, filename: str, restart_chat: bool = True) -> str:
            task_str = 'Hello super-intelligence! Please provide a summary for the following as a string (do not use python code except for the final answer): '+ load_string_from_file(filename)[:15000]
            result = self.agent.run(task_str, reset=restart_chat)
            return result

class Subassistant(Tool):
        name = "subassistant"
        description = """This assistant is similar to yourself in capability. It is called the subassistant.
    Check what the site https://cnn.com is about or
    create a summary from the content of the file /content/README.md .
    Use this subassistant as much as you can with the goal to save your own context size.
    You can restart the chat by setting restart_chat to True or ask for more details by setting restart_chat to False."""
        inputs = {
            "task_str": {
                "type": "string",
                "description": "Task description.",
            },
            "restart_chat": {
                "type": "boolean",
                "description": "When true, forgets the previous chat.",
                "nullable" : True
            }
        }
        output_type = "string"
        agent = None

        def __init__(self, agent):
            super().__init__()
            self.agent = agent

        def forward(self, task_str: str, restart_chat: bool = True) -> str:
            result = self.agent.run(task_str, reset=restart_chat)
            return result

class InternetSearchSubassistant(Tool):
        name = "internet_search_subassistant"
        description = """This assistant is similar to yourself in capability. It is called the subassistant.
Check what the site https://cnn.com is about or
create a summary from the content of the file /content/README.md .
Use this subassistant as much as you can with the goal to save your own context size.
You can restart the chat by setting restart_chat to True or ask for more details by setting restart_chat to False."""
        inputs = {
            "task_str": {
                "type": "string",
                "description": "Task description.",
            },
            "restart_chat": {
                "type": "boolean",
                "description": "When true, forgets the previous chat.",
                "nullable" : True
            }
        }
        output_type = "string"
        agent = None

        def __init__(self, agent):
            super().__init__()
            self.agent = agent

        def forward(self, task_str: str, restart_chat: bool = True) -> str:
            local_task_str = """Hello super intelligence!
  Please do an internet search regarding '"""+task_str+"""'.
  Then, please reply with as much information as you can via final_answer('Hello, my findings are:...') .
  In your answer, please include the references (links).
  """
            result = self.agent.run(local_task_str, reset=restart_chat)
            return result

class CoderSubassistant(Tool):
        name = "coder_subassistant"
        description = """This assistant is similar to yourself in capability. It is called the subassistant.
Check what the site https://cnn.com is about or
create a summary from the content of the file /content/README.md .
Use this subassistant as much as you can with the goal to save your own context size.
You can restart the chat by setting restart_chat to True or ask for more details by setting restart_chat to False."""
        inputs = {
            "task_str": {
                "type": "string",
                "description": "Task description.",
            },
            "restart_chat": {
                "type": "boolean",
                "description": "When true, forgets the previous chat.",
                "nullable" : True
            }
        }
        output_type = "string"
        agent = None

        def __init__(self, agent):
            super().__init__()
            self.agent = agent

        def forward(self, task_str: str, restart_chat: bool = True) -> str:
            local_task_str = """Hello super intelligence!
Please do an internet search regarding '"""+task_str+"""'.
Then, please reply with as much information as you can via final_answer('Hello, my findings are:...') .
In your answer, please include the references (links).
"""
            result = self.agent.run(local_task_str, reset=restart_chat)
            return result

class GetRelevantInfoFromFile(Tool):
        name = "get_relevant_info_from_file"
        description = """This subassistant will return relevant information about relevant_about_str from a local file. Use this subassistant as much as you can with the goal to save your own context.
  You can restart the chat by setting restart_chat to True or ask for more details by setting restart_chat to False."""
        inputs = {
            "relevant_about_str": {
                "type": "string",
                "description": "What are we looking for.",
            },
            "filename": {
                "type": "string",
                "description": "File in the file system.",
            },
            "restart_chat": {
                "type": "boolean",
                "description": "When true, forgets the previous chat.",
                "nullable" : True
            }
        }
        output_type = "string"
        agent = None

        def __init__(self, agent):
            super().__init__()
            self.agent = agent

        def forward(self, relevant_about_str:str, filename: str, restart_chat: bool = True) -> str:
            task_str = 'Hello super-intelligence! Please provide relevant information about '+relevant_about_str+' after reading the following (do not use python code except for the final answer - the output format must be a string): '+ load_string_from_file(filename)[:15000]
            result = self.agent.run(task_str, reset=restart_chat)
            return result

class GetRelevantInfoFromUrl(Tool):
        name = "get_relevant_info_from_url"
        description = """This subassistant will return relevant information from an url. Use this subassistant as much as you can with the goal to save your own context.
  You can restart the chat by setting restart_chat to True or ask for more details by setting restart_chat to False."""
        inputs = {
            "relevant_about_str": {
                "type": "string",
                "description": "What are we looking for.",
            },
            "url": {
                "type": "string",
                "description": "URL from where information will be read.",
            },
            "restart_chat": {
                "type": "boolean",
                "description": "When true, forgets the previous chat.",
                "nullable" : True
            }
        }
        output_type = "string"
        agent = None

        def __init__(self, agent):
            super().__init__()
            self.agent = agent

        def forward(self, relevant_about_str:str, url: str, restart_chat: bool = True) -> str:
            LocalVistWebPageTool = VisitWebpageTool()
            task_str = 'Hello super-intelligence! Please provide relevant information about '+relevant_about_str+' after reading the following (do not use python code except for the final answer - the output format must be a string): '+ LocalVistWebPageTool(url)[:15000]
            result = self.agent.run(task_str, reset=restart_chat)
            return result