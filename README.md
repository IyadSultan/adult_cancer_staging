# Adult Cancer Staging System

A system for automatically staging all cancer types using the AJCC 8th Edition staging system and CrewAI agents.

## Overview

This project implements an AI-powered system for analyzing medical notes related to all cancer types and determining the appropriate clinical and pathologic staging according to the American Joint Committee on Cancer (AJCC) 8th Edition staging system. The system uses CrewAI to create specialized agents that work together to identify cancer types, analyze staging criteria, calculate stages, and generate comprehensive reports.

## Features

- Automatic identification of cancer types from medical notes
- Verification that the identified cancer exists in the AJCC 8th Edition staging system
- Extraction of TNM values from medical notes
- Analysis of clinical and pathologic staging criteria
- Calculation of clinical and pathologic stages based on AJCC 8th Edition
- Generation of comprehensive staging reports
- Support for processing single or multiple medical notes
- Results saved to CSV format with comprehensive information
- Skip staging for cancer types not covered by AJCC 8th Edition
- Azure OpenAI integration for higher reliability and enterprise compliance

## Installation

1. Clone this repository:
```
git clone https://github.com/yourusername/adult_cancer_staging.git
cd adult_cancer_staging
```

2. Set up a virtual environment:
```
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```
uv pip install -r requirements.txt
```

4. Set up your Azure OpenAI credentials in the `.env` file:
```
AZURE_API_KEY=your_azure_api_key
AZURE_ENDPOINT=https://your-resource-name.openai.azure.com
AZURE_API_VERSION=2024-06-01
AZURE_GPT4O_DEPLOYMENT=your_deployment_name
```

## Usage

### Process a single medical note

```
python run_hn_staging.py --note path/to/your/note.txt --output results.csv
```

### Process multiple medical notes in a directory

```
python run_hn_staging.py --note_dir path/to/notes/directory --output results.csv
```

### Options

- `--note`: Path to a single medical note to process (default: hn_example.txt)
- `--note_dir`: Path to a directory containing multiple medical notes to process
- `--output`: Path to save the CSV results (default: results.csv)
- `--staging_data`: Path to the AJCC staging data file (default: AJCC8.json)
- `--model`: Azure OpenAI model deployment name (default: gpt-4o-mini)

## Project Structure

- `src/`: Source code directory
  - `adult_staging_module.py`: Main module for adult cancer staging
  - `adult_agents.py`: Definitions of CrewAI agents for cancer staging
  - `adult_tasks.py`: Definitions of CrewAI tasks for cancer staging
  - `azure_openai_config.py`: Azure OpenAI configuration for LangChain integration
- `AJCC8.json`: AJCC 8th Edition staging data
- `hn_example.txt`: Example cancer medical note
- `run_hn_staging.py`: Script to run the staging system
- `requirements.txt`: Required Python packages
- `project_status.md`: Current status of the project

## Model Provider Flexibility

This project now uses Azure OpenAI by default, but can be easily adapted to use other providers:

### Using Standard OpenAI API

To switch back to the standard OpenAI API:

1. Update the `.env` file:
```
OPENAI_API_KEY=your_openai_api_key
```

2. Modify `src/azure_openai_config.py` to use the standard OpenAI LLM from LangChain:
```python
from langchain_openai import ChatOpenAI

def get_openai_llm(model_name="gpt-4o-mini"):
    """Configure and return a standard OpenAI LLM instance."""
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Create standard OpenAI LLM
    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key,
    )
    
    return llm
```

### Using Other Model Providers

The system can be adapted to use other LLM providers supported by LangChain:

1. For Anthropic Claude:
```python
from langchain_anthropic import ChatAnthropic

def get_anthropic_llm(model_name="claude-3-opus-20240229"):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    llm = ChatAnthropic(
        model=model_name,
        anthropic_api_key=api_key
    )
    
    return llm
```

2. For local models (Ollama):
```python
from langchain_community.llms import Ollama

def get_ollama_llm(model_name="llama3"):
    llm = Ollama(model=model_name)
    return llm
```

See the [LangChain Model Integration documentation](https://python.langchain.com/v0.1/docs/integrations/llms/) for more provider options.

## How It Works

1. **Cancer Identification**: The system first analyzes the medical note to identify the specific cancer type and extract any TNM values. It verifies that the cancer exists in the AJCC 8th Edition before proceeding.
2. **Criteria Analysis**: If the cancer is supported, the system analyzes the note to identify which staging criteria are present for the identified cancer type.
3. **Stage Calculation**: Based on the identified criteria, the system calculates both the clinical and pathologic stages.
4. **Report Generation**: Finally, it generates a comprehensive staging report suitable for inclusion in a patient's medical record.

## CSV Output Fields

The system generates a CSV file with the following fields:
- Medical Note: The name of the processed note
- Date of Extraction: When the processing was performed
- Disease: The identified cancer type
- Category: The AJCC category the cancer belongs to
- System: "AJCC8 system"
- TNM Values: The TNM values extracted from the note
- Extracted Stage: The stage directly extracted from the note
- Clinical Stage: The calculated clinical stage
- Pathologic Stage: The calculated pathologic stage
- AI Stage: Combined representation of clinical and pathologic stages
- Proceed with Staging: Whether staging was performed (Yes/No)
- Explanation: Detailed explanation of how the stage was determined
- Report: Comprehensive staging report

## Dependencies

- Python 3.8+
- CrewAI
- LangChain
- Azure OpenAI API (or alternative LLM provider)
- pandas
- python-dotenv
- tqdm
- jsonschema
- colorama

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- American Joint Committee on Cancer (AJCC) for the staging system
- CrewAI for the agent framework
- Azure OpenAI for the language models
- LangChain for the LLM integration framework 