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


def setup_azure_openai_api():
    """
    Set up the Azure OpenAI API configuration from environment variables.
    """
    # Get Azure OpenAI configuration
    api_key = os.getenv("AZURE_API_KEY")
    endpoint = os.getenv("AZURE_ENDPOINT")
    api_version = os.getenv("AZURE_API_VERSION")
    deployment = os.getenv("AZURE_GPT4O_DEPLOYMENT")
    
    if not api_key or not endpoint or not api_version or not deployment:
        print("Error: Azure OpenAI API configuration is incomplete.")
        print("Please ensure the following environment variables are set in the .env file:")
        print("  - AZURE_API_KEY")
        print("  - AZURE_ENDPOINT")
        print("  - AZURE_API_VERSION")
        print("  - AZURE_GPT4O_DEPLOYMENT")
        sys.exit(1)
    
    # Set environment variables for Azure OpenAI
    os.environ["AZURE_API_KEY"] = api_key
    os.environ["AZURE_API_BASE"] = endpoint  # LiteLLM uses AZURE_API_BASE
    os.environ["AZURE_API_VERSION"] = api_version
    os.environ["AZURE_GPT4O_DEPLOYMENT"] = deployment
    
    # WORKAROUND: Set OpenAI API key to Azure API key to make LiteLLM work
    # This is necessary because LiteLLM still looks for OPENAI_API_KEY in some cases
    os.environ["OPENAI_API_KEY"] = api_key
    
    # Set OpenAI base URL to Azure endpoint using LiteLLM expected format
    os.environ["OPENAI_API_BASE"] = endpoint
    os.environ["OPENAI_API_VERSION"] = api_version
    os.environ["OPENAI_API_TYPE"] = "azure"
    
    # Print debug info
    print(f"Azure OpenAI configuration set up successfully")
    print(f"API Base: {endpoint}")
    print(f"API Version: {api_version}")
    print(f"Deployment: {deployment}")
    
    # Configure model for command line arguments - prepend azure/ to model name
    # This is what LiteLLM expects for Azure OpenAI models
    return f"azure/{deployment}"


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
- Created adult cancer staging module with CrewAI agents using Azure OpenAI
- Processed medical notes and extracted cancer type and staging information
- Applied AJCC 8th Edition staging system to medical notes
- Generated staging reports with clinical and pathologic stage explanations
- Saved results to CSV file at: {results_csv_path}
- Saved detailed markdown report with complete notes at: {results_md_path}

## Current Status
- The staging module has successfully processed the provided cancer medical notes
- Results are available in both CSV and markdown formats
- The detailed markdown report includes full patient information, disease category, extracted stage, AI-determined stages, and complete medical notes
- The project now uses Azure OpenAI API instead of OpenAI API

## Next Steps
- Evaluate staging accuracy with clinical experts
- Extend the module to handle more complex medical notes
- Improve error handling and robustness
- Develop a user interface for easier interaction

"""
    else:
        status_content = f"""# Adult Cancer Staging Project Status

## Completed Steps
- Created adult cancer staging module with CrewAI agents using Azure OpenAI
- Attempted to process cancer medical notes but encountered errors

## Current Status
- The staging module encountered issues during processing
- Results were not generated successfully
- The project now uses Azure OpenAI API instead of OpenAI API

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
    
    # Set up Azure OpenAI API
    model_name = setup_azure_openai_api()
    
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
        model=model_name,
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