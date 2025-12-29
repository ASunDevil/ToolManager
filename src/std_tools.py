"""
Standard utility tools for the ToolManager.
This module contains general-purpose tools that don't fit into other specific categories.
"""

import subprocess

def execute_shell_command(command: str) -> str:
    """
    Executes a shell command and returns the output.

    This tool allows the agent to execute arbitrary shell commands.
    It is powerful but carries security risks, so it should be used with caution.

    Args:
        command: The shell command to execute (e.g., "ls -la", "echo hello").

    Returns:
        The standard output of the command if successful, or an error message
        containing the exit code and stderr if it fails.
    """
    try:
        # We use shell=True to support compound commands (e.g., "echo a && echo b")
        # and shell features like pipes.
        # WARNING: This introduces shell injection risks if 'command' comes from untrusted user input.
        # However, for an agent tool intended to run arbitrary commands, this is the desired behavior.

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30 # Safety timeout to prevent indefinite hanging
        )

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error (Exit Code {result.returncode}): {result.stderr.strip()}"

    except subprocess.TimeoutExpired:
        return "Error: Command timed out."
    except Exception as e:
        return f"Error executing command: {str(e)}"
