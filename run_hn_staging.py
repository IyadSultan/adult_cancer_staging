"""
Run the adult head and neck cancer staging module on medical notes.
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from src.adult_staging_module import AdultCancerStaging
import datetime


# Load environment variables
load_dotenv()


# disable crewai telemetry from https://www.reddit.com/r/crewai/comments/1cp5gby/how_can_i_disable_all_telemetry_in_crewai/
from crewai.telemetry import Telemetry

def noop(*args, **kwargs):
    pass

def disable_crewai_telemetry():
    for attr in dir(Telemetry):
        if callable(getattr(Telemetry, attr)) and not attr.startswith("__"):
            setattr(Telemetry, attr, noop)


def setup_openai_api():
    """
    Set up the OpenAI API key from environment variables.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Please set your OpenAI API key in the .env file.")
        print("You can run 'python setup_api_key.py' to set up your API key.")
        sys.exit(1)
    
    os.environ["OPENAI_API_KEY"] = api_key


def create_project_status(results_csv_path, results_md_path):
    """
    Create or update the project_status.md file.
    
    Args:
        results_csv_path: Path to the CSV results file
        results_md_path: Path to the markdown results file
    """
    status_file = Path("project_status.md")
    
    if results_csv_path.exists() and results_md_path.exists():
        status_content = f"""# Adult Cancer Staging Project Status

## Completed Steps
- Created adult cancer staging module with CrewAI agents
- Processed medical notes and extracted cancer type and staging information
- Applied AJCC 8th Edition staging system to medical notes
- Generated staging reports with clinical and pathologic stage explanations
- Saved results to CSV file at: {results_csv_path}
- Saved detailed markdown report with complete notes at: {results_md_path}

## Current Status
- The staging module has successfully processed the provided cancer medical notes
- Results are available in both CSV and markdown formats
- The detailed markdown report includes full patient information, disease category, extracted stage, AI-determined stages, and complete medical notes

## Next Steps
- Evaluate staging accuracy with clinical experts
- Extend the module to handle more complex medical notes
- Improve error handling and robustness
- Develop a user interface for easier interaction

"""
    else:
        status_content = f"""# Adult Cancer Staging Project Status

## Completed Steps
- Created adult cancer staging module with CrewAI agents
- Attempted to process cancer medical notes but encountered errors

## Current Status
- The staging module encountered issues during processing
- Results were not generated successfully

## Next Steps
- Debug the staging module
- Fix the identified issues
- Retry processing the medical notes

"""
    
    with open(status_file, "w", encoding="utf-8") as f:
        f.write(status_content)
    
    print(f"Project status updated in {status_file}")


def main():
    """
    Main function to run the adult cancer staging module.
    """
    disable_crewai_telemetry()

    parser = argparse.ArgumentParser(description="Process medical notes for adult head and neck cancer staging.")
    parser.add_argument("--note", default="hn_example.txt", help="Path to a single medical note to process")
    parser.add_argument("--note_dir", help="Path to a directory containing multiple medical notes to process")
    parser.add_argument("--output", default="results/results.csv", help="Path to save the output files (both CSV and markdown)")
    parser.add_argument("--staging_data", default="AJCC8.json", help="Path to the AJCC staging data file")
    parser.add_argument("--mapping_csv", default="disease_mappings.csv", help="Path to the disease mappings CSV file")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model to use")
    
    args = parser.parse_args()
    
    # Set up OpenAI API
    setup_openai_api()
    
    # Create results directory if it doesn't exist
    results_dir = os.path.dirname(args.output)
    if results_dir and not os.path.exists(results_dir):
        os.makedirs(results_dir)
        print(f"Created results directory: {results_dir}")
    
    # Check if staging data file exists
    staging_data_path = Path(args.staging_data)
    if not staging_data_path.exists():
        print(f"Error: Staging data file not found at {staging_data_path}")
        sys.exit(1)
    
    print(f"Using staging data from: {staging_data_path}")
    
    # Check if mapping CSV file exists
    mapping_csv_path = Path(args.mapping_csv)
    if not mapping_csv_path.exists():
        print(f"Warning: Disease mappings file not found at {mapping_csv_path}")
        print("Will use default disease mappings.")
    else:
        print(f"Using disease mappings from: {mapping_csv_path}")
    
    # Create the staging module
    staging_module = AdultCancerStaging(
        staging_data_path=str(staging_data_path),
        model=args.model,
        mapping_csv_path=str(mapping_csv_path)
    )
    
    output_path = Path(args.output)
    
    try:
        # Process either a single note or a directory of notes
        if args.note_dir:
            note_dir = Path(args.note_dir)
            if not note_dir.exists() or not note_dir.is_dir():
                print(f"Error: Note directory not found at {note_dir}")
                sys.exit(1)
                
            print(f"Processing medical notes in directory: {note_dir}")
            staging_module.process_multiple_notes(str(note_dir), str(output_path))
        else:
            note_path = args.note
            if not Path(note_path).exists():
                print(f"Error: Medical note not found at {note_path}")
                print("Please make sure the medical note file exists.")
                sys.exit(1)
                
            print(f"Processing medical note: {note_path}")
            staging_module.process_single_note(note_path, str(output_path))
            
        # Get timestamp for file access
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # Expected output paths
        output_base = os.path.splitext(args.output)[0]
        csv_path = Path(f"{output_base}_{timestamp}.csv")
        md_path = Path(f"{output_base}_{timestamp}.md")
        
        # Update project status with results
        create_project_status(csv_path, md_path)
    except Exception as e:
        print(f"Error: {e}")
        create_project_status(Path("error"), Path("error"))
        sys.exit(1)

if __name__ == "__main__":
    main() 