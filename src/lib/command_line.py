
import  subprocess
import  os

def bash_prompt(command: str) -> str:
    if not command:
        raise Exception(f"Empty prompt used: '{command}'")

    try:
        result = os.popen(command)
        lines = result.readlines()
        lines = [line[:-1] for line in lines]
        retstring = "\n".join(lines)
        result.close()

        return retstring
    except subprocess.CalledProcessError as e:
        raise Exception(f"Command '{command}' failed: {e.stderr}") from None
