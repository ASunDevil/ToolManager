import subprocess

def execute_shell_command(command: str) -> str:
    """
    Executes a shell command and returns the output.

    Args:
        command: The shell command to execute.

    Returns:
        The standard output of the command, or error message if it fails.
    """
    try:
        # Use shlex to split the command safely for subprocess (unless using shell=True)
        # Using shell=True for "executing shell command" as requested, to support pipes/etc if needed.
        # But generally shell=True is dangerous. The prompt asks to "run 'shell command'".
        # If I use shell=False, I can't run compound commands like "echo hi && echo bye".
        # I'll use shell=True but minimal processing.

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30 # Safety timeout
        )

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error (Exit Code {result.returncode}): {result.stderr.strip()}"

    except subprocess.TimeoutExpired:
        return "Error: Command timed out."
    except Exception as e:
        return f"Error executing command: {str(e)}"
