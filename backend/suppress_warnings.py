import warnings
import sys
import os

def run_with_warnings_suppressed():
    """
    Run a Python script with specific pandas warnings suppressed.
    Usage: python suppress_warnings.py <script_to_run> [args...]
    """
    # Suppress specific pandas FutureWarning about observed parameter
    warnings.filterwarnings("ignore", category=FutureWarning, 
                           message="The default of observed=False is deprecated")
    
    # Get the script to run and its arguments
    if len(sys.argv) < 2:
        print("Usage: python suppress_warnings.py <script_to_run> [args...]")
        sys.exit(1)
    
    script = sys.argv[1]
    args = sys.argv[2:]
    
    # Construct command
    cmd = f"python {script} {' '.join(args)}"
    print(f"Running: {cmd}")
    
    # Execute the script with its arguments
    os.system(cmd)

if __name__ == "__main__":
    run_with_warnings_suppressed()
