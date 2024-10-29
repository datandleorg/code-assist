from pathlib import Path
import sys
import time
from langchain_core.tools import tool
import subprocess
import tempfile
import os

from codev1.src.rag import getContext

@tool
def run_bash_command(command: str):
    """
    Runs a bash command and returns the output.
    
    Args:
        command (str): The bash command to run.
    
    Returns:
        str: The output of the bash command.
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False)

    script = f'tell application "Terminal" to do script "{command} > {temp_file.name} 2>&1"'
    subprocess.run(["osascript", "-e", script])
    
    input("Press Enter after the command finishes...")

   # Read the output from the temporary file
    with open(temp_file.name, "r") as f:
        output = f.read()

    return output
    # return os.popen(command).read()

@tool
def create_or_update_file(path: str, content: str):
    """
    Creates a new file or updates an existing file at the specified path with the given content.
    If the file already exists, its content will be replaced with the new content.
    
    Args:
        path (str): The file path where the file should be created or updated.
        content (str): The content to write into the file.
    
    Returns:
        str: A message indicating the operation status.
    """
    try:
        file_path = Path(path)
        # Create parent directories if they do not exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the content to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        return f"File successfully created or updated at: {file_path}"
    except Exception as e:
        return f"An error occurred: {e}"

@tool
def retrieve_code_context(query):
    """
    Retrieves the code base context for the given query.
    
    Args:
        query (str): The query to decide whether to retrieve the context or not.

    Returns:
        str: The context retrieved from the query.
    """
    return getContext(query)