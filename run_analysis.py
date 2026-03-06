"""
run_analysis.py
---------------
Master script to run the entire competitor analysis workflow end-to-end.
"""

import sys
import subprocess

def run_step(script_name):
    print(f"\n{'='*50}")
    print(f"🚀 Running: {script_name}")
    print(f"{'='*50}\n")
    
    # Run the script module using the current python executable
    path = f"tools/{script_name}"
    result = subprocess.run([sys.executable, path])
    
    if result.returncode != 0:
        print(f"\n❌ Pipeline stopped. '{script_name}' failed with exit code {result.returncode}")
        sys.exit(result.returncode)

if __name__ == "__main__":
    print("\n🏢 Starting Competitor Analysis Workflow for Hacker's Unity\n")
    run_step("find_competitors.py")
    run_step("scrape_competitor.py")
    run_step("analyze_competitors.py")
    run_step("generate_report.py")
    print("\n🎉 All done! Pipeline finished successfully.")
