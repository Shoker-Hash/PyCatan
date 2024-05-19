import subprocess

def run_py_catan():
    # Define the command and arguments
    command = "/bin/python3"
    script_path = "main.py"
    
    # Prepare the input for the subprocess
    inputs = "\n".join([
        "AdrianHerasBot.AdrianHerasBot",  # First bot
        "AdrianHerasBot.AdrianHerasBot",  # Second bot
        "AdrianHerasBot.AdrianHerasBot",  # Third bot
        "AdrianHerasBot.AdrianHerasBot",  # Fourth bot
        "50"                              # Number of games
    ]) + "\n"  # End with a newline

    # Run the script with the inputs
    process = subprocess.Popen([command, script_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, errors = process.communicate(input=inputs)

    # Print the output and errors (if any)
    print("Output:")
    print(output)
    if errors:
        print("Errors:")
        print(errors)

if __name__ == "__main__":
    run_py_catan()
