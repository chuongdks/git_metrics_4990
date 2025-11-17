import subprocess
import os

def run_pmd_analysis(source_dir, ruleset_path, output_file="pmd_report.xml"):
    """
    Runs the PMD static code analyzer using the command line interface.

    Args:
        source_dir (str): The directory containing the code to analyze.
        ruleset_path (str): The path to the PMD ruleset file (or built-in ruleset).
        output_file (str): The name of the file to save the PMD report to.
    
    Returns:
        bool: True if PMD ran successfully, False otherwise.
    """
    
    # 1. Construct the PMD command
    # Example command: pmd check -d /path/to/code -R category/java/quickstart.xml -f xml -r pmd_report.xml
    pmd_command = [
        "pmd.bat",
        "check",
        "-d", source_dir,
        "-R", ruleset_path,
        "-f", "xml",
        "-r", output_file
    ]
    
    print(f"Executing PMD command: {' '.join(pmd_command)}")

    try:
        # 2. Execute the command using subprocess.run
        # capture_output=True captures stdout/stderr
        # check=True raises an exception for non-zero exit codes
        result = subprocess.run(
            pmd_command, 
            capture_output=True, 
            text=True, 
            check=False # Set to False to catch PMD's non-zero exit code (4) if violations are found
        )
        
        # PMD returns exit code 4 if violations are found, which is a success for analysis
        if result.returncode == 0 or result.returncode == 4:
            print(f"PMD analysis completed. Report saved to: {output_file}")
            # Optionally print PMD's output/errors
            # print("PMD STDOUT:\n", result.stdout)
            # print("PMD STDERR:\n", result.stderr)
            return True
        else:
            print(f"PMD command failed with exit code {result.returncode}.")
            print("PMD Error Output:\n", result.stderr)
            return False

    except FileNotFoundError:
        print("Error: PMD command not found. Make sure PMD is installed and in your system's PATH.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during PMD execution: {e}")
        return False

# --- Example Usage ---
# NOTE: Replace these with your actual local paths
REPO_ROOT = "D:/Project/Java/java-util-master"
SOURCE_CODE_DIR = os.path.join(REPO_ROOT, "src", "main", "java") 
RULESET = "D:/Program Files/PMD/pmd-bin-7.18.0/rulesets/java/quickstart.xml" # A built-in ruleset
OUTPUT_REPORT = "./pr_pmd_violations.xml"

# Before calling this function, you must have used Git to checkout the PR's head commit
# For example: os.chdir(REPO_ROOT) then subprocess.run(["git", "checkout", "pr-123"])

run_pmd_analysis(SOURCE_CODE_DIR, RULESET, OUTPUT_REPORT)