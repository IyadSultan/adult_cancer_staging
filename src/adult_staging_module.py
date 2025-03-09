import json
import os
import csv
import datetime
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from pathlib import Path
from crewai import Crew, Process

from .adult_agents import AdultCancerStagingAgents
from .adult_tasks import AdultCancerStagingTasks

class AdultCancerStaging:
    """
    A module for analyzing medical notes and determining adult cancer staging
    using the AJCC 8th Edition system for all cancer types.
    """
    
    def __init__(self, staging_data_path: str, model: str = "gpt-4o-mini", mapping_csv_path: str = "disease_mappings.csv"):
        """
        Initialize the staging module.
        
        Args:
            staging_data_path: Path to the AJCC staging JSON file
            model: The OpenAI model to use
            mapping_csv_path: Path to the disease mappings CSV file
        """
        self.model = model
        self.mapping_csv_path = mapping_csv_path
        self.staging_data = self._load_staging_data(staging_data_path)
        self.agents = AdultCancerStagingAgents(model=model)
        
    def _load_staging_data(self, staging_data_path: str) -> Dict[str, Any]:
        """
        Load the AJCC staging data from a JSON file.
        
        Args:
            staging_data_path: Path to the AJCC staging JSON file
            
        Returns:
            Dict: The staging data as a dictionary
        """
        try:
            with open(staging_data_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Load the JSON data
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                # Attempt to fix common JSON syntax errors
                content = self._fix_json_syntax(content)
                data = json.loads(content)
            
            # Create disease mapping for better matching
            self._create_disease_mapping(data)
            
            return data
                
        except Exception as e:
            print(f"Error loading staging data: {e}")
            raise
    
    def _fix_json_syntax(self, content: str) -> str:
        """
        Fix common JSON syntax errors in the content.
        
        Args:
            content: JSON content with potential syntax errors
            
        Returns:
            str: Fixed JSON content
        """
        # Fix specific JSON issues in AJCC8.json
        # Property keys must be doublequoted
        content = content.replace("{ N:", '{ "N":')
        content = content.replace("{ M:", '{ "M":')
        content = content.replace("{ T:", '{ "T":')
        
        # Fix trailing commas
        content = content.replace(",\n        },", "\n        },")
        
        # Remove trailing commas before closing brackets
        content = content.replace("},}", "}}")
        content = content.replace("},]", "}]")
        
        return content
    
    def _create_disease_mapping(self, data: List[Dict[str, Any]]) -> None:
        """
        Create a mapping of disease names and their variations to their 
        official categories in the AJCC8 data using the CSV file.
        
        Args:
            data: The loaded AJCC8 staging data
        """
        self.disease_mapping = {}
        self.available_categories = []
        
        # Extract categories from staging data
        if isinstance(data, list):
            # Handle data as a list of items
            for item in data:
                if isinstance(item, dict) and 'name' in item:
                    disease_name = item['name']
                    self.available_categories.append(disease_name)
        elif isinstance(data, dict):
            # Handle data as a dictionary
            for category in data.keys():
                self.available_categories.append(category)
        
        # Load mappings from CSV file
        try:
            if os.path.exists(self.mapping_csv_path):
                mappings_df = pd.read_csv(self.mapping_csv_path, comment='#')
                print(f"Loaded {len(mappings_df)} disease mappings from {self.mapping_csv_path}")
                
                # Convert CSV to dictionary
                for _, row in mappings_df.iterrows():
                    disease_variation = row['disease_variation'].lower()
                    canonical_category = row['canonical_category']
                    self.disease_mapping[disease_variation] = canonical_category
                    
                    # Check if category is not in available_categories
                    if canonical_category not in self.available_categories:
                        self.available_categories.append(canonical_category)
            else:
                print(f"Warning: Disease mappings file not found at {self.mapping_csv_path}")
                # Fallback to basic mapping if file doesn't exist
                self._create_basic_mappings()
        except Exception as e:
            print(f"Error loading disease mappings from CSV: {e}")
            # Fallback to basic mapping if there's an error
            self._create_basic_mappings()
        
        print(f"Created disease mapping with {len(self.disease_mapping)} entries")
        print(f"Available categories: {len(self.available_categories)}")
        
        # Print some examples of the mapping
        laryngeal_mappings = {k: v for k, v in self.disease_mapping.items() if "laryn" in k or "glott" in k}
        if laryngeal_mappings:
            print("Some laryngeal cancer mappings:")
            for k, v in list(laryngeal_mappings.items())[:5]:
                print(f"  - '{k}' → '{v}'")
    
    def _create_basic_mappings(self) -> None:
        """
        Create basic disease mappings as a fallback if the CSV file isn't available.
        This is only used if the CSV mapping file cannot be loaded.
        """
        # Check if there are any categories available
        if not self.available_categories:
            print("Warning: No disease categories available for basic mapping")
            return
            
        # If we have no categories, we can't create any mappings
        if len(self.available_categories) == 0:
            return
            
        # Find typical cancer categories in available_categories
        common_cancers = {
            "breast": ["breast cancer", "breast carcinoma", "mammary carcinoma"],
            "lung": ["lung cancer", "lung carcinoma", "bronchogenic carcinoma"],
            "colorectal": ["colon cancer", "rectal cancer", "colorectal carcinoma"],
            "prostate": ["prostate cancer", "prostatic carcinoma", "prostatic adenocarcinoma"],
            "melanoma": ["malignant melanoma", "skin melanoma", "cutaneous melanoma"],
            "leukemia": ["acute leukemia", "chronic leukemia", "aml", "cll"],
            "lymphoma": ["hodgkin lymphoma", "non-hodgkin lymphoma", "lymphoma"]
        }
        
        # For each common cancer type, check if we have a matching category
        for key_term, variations in common_cancers.items():
            matching_category = None
            
            # Try to find a matching category
            for category in self.available_categories:
                if key_term in category.lower():
                    matching_category = category
                    break
                    
            # If we found a match, add all variations
            if matching_category:
                for variation in variations:
                    self.disease_mapping[variation] = matching_category
    
    def _match_cancer_to_category(self, cancer_type: str) -> str:
        """
        Match the identified cancer type to its correct category in AJCC8.
        
        Args:
            cancer_type: The cancer type identified by the agent
            
        Returns:
            str: The matched category or "Not in AJCC 8th Edition" if not found
        """
        # First, try direct matching
        cancer_lower = cancer_type.lower()
        
        # Try direct lookup in disease_mapping
        if cancer_lower in self.disease_mapping:
            return self.disease_mapping[cancer_lower]
        
        # Try partial matches
        for disease_name, category in self.disease_mapping.items():
            if disease_name in cancer_lower or cancer_lower in disease_name:
                # Calculate match score based on overlap
                overlap_score = len(set(disease_name.split()) & set(cancer_lower.split())) / max(len(disease_name.split()), len(cancer_lower.split()))
                if overlap_score > 0.5:  # If more than 50% of words match
                    return category
        
        # Look for keyword-based matches with common cancer terms
        keywords = {
            "breast": ["mammary", "ductal", "lobular"],
            "lung": ["pulmonary", "bronch", "respiratory"],
            "colon": ["colorectal", "rectal", "bowel", "intestinal"],
            "stomach": ["gastric", "gastroesophageal"],
            "liver": ["hepatic", "hepatocellular", "hepato"],
            "pancreas": ["pancreatic", "islet cell"],
            "kidney": ["renal", "nephro"],
            "prostate": ["prostatic", "psa"],
            "bladder": ["urothelial", "transitional cell"],
            "brain": ["cerebral", "glio", "neural", "cns"],
            "lymphoma": ["lymphatic", "hodgkin", "non-hodgkin"],
            "leukemia": ["myeloid", "lymphoblastic", "hematologic"],
            "melanoma": ["skin cancer", "dermal", "cutaneous"],
            "thyroid": ["thyroidal", "papillary", "follicular"]
        }
        
        # Check for keyword matches
        for key_term, related_terms in keywords.items():
            if key_term in cancer_lower or any(term in cancer_lower for term in related_terms):
                # Find categories that might match this keyword
                matching_categories = []
                for disease_name, category in self.disease_mapping.items():
                    if key_term in disease_name.lower() or any(term in disease_name.lower() for term in related_terms):
                        matching_categories.append(category)
                
                if matching_categories:
                    # Return the most common category
                    from collections import Counter
                    return Counter(matching_categories).most_common(1)[0][0]
        
        # If no match found
        return "Not in AJCC 8th Edition"
    
    def _read_medical_note(self, note_path: str) -> str:
        """
        Read a medical note from a file.
        
        Args:
            note_path: Path to the medical note file
            
        Returns:
            str: The content of the medical note
        """
        try:
            with open(note_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading medical note: {e}")
            raise
    
    def process_medical_note(self, note_path: str) -> Tuple[str, str, str, str, str, str, bool]:
        """
        Process a single medical note to determine cancer type and stage.
        
        Args:
            note_path: Path to the medical note file
            
        Returns:
            Tuple: (cancer_type, cancer_category, clinical_stage, pathologic_stage, tnm_values, explanation, report, proceed_with_staging)
        """
        # Read the medical note
        medical_note = self._read_medical_note(note_path)
        
        # Create agents
        cancer_identifier = self.agents.create_cancer_identifier_agent()
        criteria_analyzer = self.agents.create_criteria_analyzer_agent()
        stage_calculator = self.agents.create_stage_calculator_agent()
        report_generator = self.agents.create_report_generator_agent()
        
        # Create tasks with improved category information
        identify_task = AdultCancerStagingTasks.identify_cancer_type(
            agent=cancer_identifier,
            medical_note=medical_note,
            staging_data=self.staging_data,
            available_categories=self.available_categories,
            disease_mapping=self.disease_mapping
        )
        
        # Create a crew for the first task
        identify_crew = Crew(
            agents=[cancer_identifier],
            tasks=[identify_task],
            process=Process.sequential,
            verbose=True
        )
        
        # Execute the first task to identify the cancer type
        identify_result = identify_crew.kickoff()

        # Get the result using the raw attribute (with minimal debugging)
        cancer_type_result = identify_result.raw

        # Check if raw is None or not a string, and handle accordingly
        if cancer_type_result is None:
            print("Warning: Using alternative methods to extract task result")
            try:
                # Try tasks_output if it exists
                if hasattr(identify_result, 'tasks_output') and identify_result.tasks_output:
                    cancer_type_result = identify_result.tasks_output[0].raw
                else:
                    # Last resort: try to get anything we can from the result
                    cancer_type_result = str(identify_result)
            except Exception as e:
                print(f"Error extracting task output: {e}")
                cancer_type_result = "Error extracting result"

        # Ensure cancer_type_result is a string
        if not isinstance(cancer_type_result, str):
            cancer_type_result = str(cancer_type_result)

        # Parse the cancer type result
        try:
            cancer_type_lines = cancer_type_result.split('\n')
            cancer_type = None
            cancer_category = "Not in AJCC 8th Edition"
            tnm_values = "Not provided"
            proceed_with_staging = False
            
            for line in cancer_type_lines:
                if line.startswith("Cancer Type:"):
                    cancer_type = line.replace("Cancer Type:", "").strip()
                elif line.startswith("Cancer Category:"):
                    cancer_category = line.replace("Cancer Category:", "").strip()
                elif line.startswith("TNM Values:"):
                    tnm_values = line.replace("TNM Values:", "").strip()
                elif line.startswith("Proceed with Staging:"):
                    proceed_with_staging = line.replace("Proceed with Staging:", "").strip().lower() == "yes"
            
            if not cancer_type:
                raise ValueError("Cancer type not identified in the result")

            # Apply additional matching logic if cancer was not categorized properly
            if cancer_category == "Not in AJCC 8th Edition" and cancer_type:
                # Try our custom matching logic
                matched_category = self._match_cancer_to_category(cancer_type)
                if matched_category != "Not in AJCC 8th Edition":
                    print(f"Successfully matched '{cancer_type}' to category '{matched_category}' using custom logic")
                    cancer_category = matched_category
                    proceed_with_staging = True

            # If the cancer does not exist in AJCC 8th Edition or we should not proceed with staging,
            # return with default values and don't proceed with further staging
            if not proceed_with_staging or cancer_category == "Not in AJCC 8th Edition":
                return (cancer_type, cancer_category, "Not applicable", "Not applicable", tnm_values, 
                        "This cancer type is not included in the AJCC 8th Edition staging system.", 
                        "Staging not applicable for this cancer type.", False)
                
        except Exception as e:
            print(f"Error parsing cancer identifier result: {e}")
            print(f"Original result: {cancer_type_result}")
            raise
            
        # Create analyze criteria task
        analyze_task = AdultCancerStagingTasks.analyze_staging_criteria(
            agent=criteria_analyzer,
            medical_note=medical_note,
            cancer_type=cancer_type,
            cancer_category=cancer_category,
            tnm_values=tnm_values,
            staging_data=self.staging_data
        )
        
        # Create a crew for the analyze task
        analyze_crew = Crew(
            agents=[criteria_analyzer],
            tasks=[analyze_task],
            process=Process.sequential,
            verbose=True
        )
        
        # Execute the analysis task
        analyze_result = analyze_crew.kickoff()
        criteria_analysis = analyze_result.raw
        
        # Check if raw is None or not a string, and handle accordingly
        if criteria_analysis is None:
            print("Warning: Using alternative methods to extract criteria analysis")
            try:
                # Try tasks_output if it exists
                if hasattr(analyze_result, 'tasks_output') and analyze_result.tasks_output:
                    criteria_analysis = analyze_result.tasks_output[0].raw
                else:
                    # Last resort: try to get anything we can from the result
                    criteria_analysis = str(analyze_result)
            except Exception as e:
                print(f"Error extracting criteria analysis output: {e}")
                criteria_analysis = "Error extracting criteria analysis"

        # Ensure criteria_analysis is a string
        if not isinstance(criteria_analysis, str):
            criteria_analysis = str(criteria_analysis)

        # Create stage calculation task
        calculate_task = AdultCancerStagingTasks.calculate_stage(
            agent=stage_calculator,
            medical_note=medical_note,
            cancer_type=cancer_type,
            cancer_category=cancer_category,
            tnm_values=tnm_values,
            criteria_analysis=criteria_analysis,
            staging_data=self.staging_data
        )
        
        # Create a crew for the calculate task
        calculate_crew = Crew(
            agents=[stage_calculator],
            tasks=[calculate_task],
            process=Process.sequential,
            verbose=True
        )
        
        # Execute the calculation task
        calculate_result = calculate_crew.kickoff()
        stage_result = calculate_result.raw
        
        # Check if raw is None or not a string, and handle accordingly
        if stage_result is None:
            print("Warning: Using alternative methods to extract stage calculation")
            try:
                # Try tasks_output if it exists
                if hasattr(calculate_result, 'tasks_output') and calculate_result.tasks_output:
                    stage_result = calculate_result.tasks_output[0].raw
                else:
                    # Last resort: try to get anything we can from the result
                    stage_result = str(calculate_result)
            except Exception as e:
                print(f"Error extracting stage calculation output: {e}")
                stage_result = "Error extracting stage calculation"

        # Ensure stage_result is a string
        if not isinstance(stage_result, str):
            stage_result = str(stage_result)

        # Parse the stage result
        try:
            stage_lines = stage_result.split('\n')
            clinical_stage = "Not determined"
            pathologic_stage = "Not determined"
            explanation = ""
            
            for i, line in enumerate(stage_lines):
                if line.startswith("Clinical Stage:"):
                    clinical_stage = line.replace("Clinical Stage:", "").strip()
                elif line.startswith("Pathologic Stage:"):
                    pathologic_stage = line.replace("Pathologic Stage:", "").strip()
                elif line.startswith("Explanation:"):
                    # Get all the remaining lines as the explanation
                    explanation = '\n'.join(stage_lines[i:]).replace("Explanation:", "").strip()
                    break
                    
        except Exception as e:
            print(f"Error parsing stage calculation result: {e}")
            print(f"Original result: {stage_result}")
            raise
            
        # Create report generation task
        report_task = AdultCancerStagingTasks.generate_report(
            agent=report_generator,
            medical_note=medical_note,
            cancer_type=cancer_type,
            cancer_category=cancer_category,
            clinical_stage=clinical_stage,
            pathologic_stage=pathologic_stage,
            tnm_values=tnm_values,
            criteria_analysis=criteria_analysis,
            explanation=explanation
        )
        
        # Create a crew for the report task
        report_crew = Crew(
            agents=[report_generator],
            tasks=[report_task],
            process=Process.sequential,
            verbose=True
        )
        
        # Execute the report task
        report_result = report_crew.kickoff()
        report = report_result.raw
        
        # Check if raw is None or not a string, and handle accordingly
        if report is None:
            print("Warning: Using alternative methods to extract report")
            try:
                # Try tasks_output if it exists
                if hasattr(report_result, 'tasks_output') and report_result.tasks_output:
                    report = report_result.tasks_output[0].raw
                else:
                    # Last resort: try to get anything we can from the result
                    report = str(report_result)
            except Exception as e:
                print(f"Error extracting report output: {e}")
                report = "Error extracting report"

        # Ensure report is a string
        if not isinstance(report, str):
            report = str(report)

        return cancer_type, cancer_category, clinical_stage, pathologic_stage, tnm_values, explanation, report, True
    
    def _generate_markdown_report(self, data: List[Dict], medical_note_content: str) -> str:
        """
        Generate a markdown report from the staging results.
        
        Args:
            data: List of dictionaries containing staging results
            medical_note_content: Content of the medical note
            
        Returns:
            str: Markdown report content
        """
        markdown = "# Cancer Staging Report\n\n"
        markdown += f"**Date of Extraction:** {data[0]['Date of Extraction']}\n\n"
        
        # Add explanation of cancer staging terminology
        markdown += "## Understanding Cancer Staging Terminology\n\n"
        markdown += "This report uses the following terms for cancer staging:\n\n"
        markdown += "- **TNM Values**: The raw TNM classification notation (T=Tumor size/extent, N=Node involvement, M=Metastasis) directly extracted from the medical note. Prefixes like 'c' indicate clinical staging, 'p' indicates pathologic staging.\n\n"
        markdown += "- **Extracted Stage**: The exact staging information as written in the original medical note, representing how the healthcare provider documented the stage.\n\n"
        markdown += "- **AI Stage Determination**: The system's interpretation based on AJCC 8th Edition guidelines, consisting of:\n"
        markdown += "  - **Clinical Stage**: Full stage interpretation including TNM values and formal stage grouping based on examinations and imaging\n"
        markdown += "  - **Pathologic Stage**: Stage determination based on surgical/pathological findings (when available)\n\n"
        
        markdown += "## Patient Information and Staging Results\n\n"
        
        for item in data:
            markdown += f"### Medical Note: {item['Medical Note']}\n\n"
            markdown += f"**Disease:** {item['Disease']}\n\n"
            markdown += f"**Category:** {item['Category']}\n\n"
            markdown += f"**System:** {item['System']}\n\n"
            markdown += f"**TNM Values:** {item['TNM Values']}\n\n"
            markdown += f"**Extracted Stage:** {item['Extracted Stage']}\n\n"
            markdown += f"**AI Stage Determination:**\n\n"
            markdown += f"- Clinical Stage: {item['Clinical Stage']}\n"
            markdown += f"- Pathologic Stage: {item['Pathologic Stage']}\n\n"
            markdown += f"**Detailed Explanation:**\n\n{item['Explanation']}\n\n"
            
            # Process the report to remove the signature block
            report = item['Report']
            signature_block_text = "This report is generated for inclusion in the patient's medical records and should be reviewed in conjunction with all other clinical information available for comprehensive care planning."
            if signature_block_text in report:
                # Find the position where the signature block starts
                pos = report.find(signature_block_text)
                # Trim the report to exclude the signature block
                report = report[:pos].strip()
            
            markdown += f"**Staging Report:**\n\n{report}\n\n"
        
        markdown += "## Complete Medical Note\n\n"
        markdown += "```\n"
        markdown += medical_note_content
        markdown += "\n```\n"
        
        return markdown

    def process_single_note(self, note_path: str, output_csv: str) -> None:
        """
        Process a single medical note and save the results to CSV and markdown files.
        
        Args:
            note_path: Path to the medical note file
            output_csv: Path to save the CSV output
        """
        try:
            # Create results directory if it doesn't exist
            results_dir = os.path.dirname(output_csv)
            if results_dir and not os.path.exists(results_dir):
                os.makedirs(results_dir)
            
            # Get current timestamp for filenames
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Adjust output paths to include timestamp
            output_base = os.path.splitext(output_csv)[0]
            csv_output = f"{output_base}_{timestamp}.csv"
            md_output = f"{output_base}_{timestamp}.md"
            
            # Get current date for extraction date
            extraction_date = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Read the full medical note content
            with open(note_path, 'r', encoding='utf-8') as f:
                medical_note_content = f.read()
            
            # Process the medical note
            cancer_type, cancer_category, clinical_stage, pathologic_stage, tnm_values, explanation, report, proceed_with_staging = self.process_medical_note(note_path)
            
            # Remove signature block from report
            signature_block_text = "This report is generated for inclusion in the patient's medical records and should be reviewed in conjunction with all other clinical information available for comprehensive care planning."
            if signature_block_text in report:
                # Find the position where the signature block starts
                pos = report.find(signature_block_text)
                # Trim the report to exclude the signature block
                report = report[:pos].strip()
            
            # Create a list for the CSV
            data = [
                {
                    'Medical Note': os.path.basename(note_path),
                    'Date of Extraction': extraction_date,
                    'Disease': cancer_type,
                    'Category': cancer_category,
                    'System': 'AJCC8 system',
                    'TNM Values': tnm_values,
                    'Extracted Stage': tnm_values,  # The TNM values from the note
                    'Clinical Stage': clinical_stage,
                    'Pathologic Stage': pathologic_stage,
                    'AI Stage': f"Clinical: {clinical_stage}, Pathologic: {pathologic_stage}",
                    'Proceed with Staging': "Yes" if proceed_with_staging else "No",
                    'Explanation': explanation,
                    'Report': report
                }
            ]
            
            # Create a DataFrame
            df = pd.DataFrame(data)
            
            # Save to CSV
            df.to_csv(csv_output, index=False)
            print(f"CSV results saved to: {csv_output}")
            
            # Generate and save markdown report
            markdown_content = self._generate_markdown_report(data, medical_note_content)
            with open(md_output, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"Markdown report saved to: {md_output}")
            
        except Exception as e:
            print(f"Error processing note {note_path}: {e}")
            raise
    
    def process_multiple_notes(self, note_dir: str, output_csv: str) -> None:
        """
        Process multiple medical notes and save the results to CSV and markdown files.
        
        Args:
            note_dir: Directory containing medical notes
            output_csv: Path to save the CSV output
        """
        try:
            # Create results directory if it doesn't exist
            results_dir = os.path.dirname(output_csv)
            if results_dir and not os.path.exists(results_dir):
                os.makedirs(results_dir)
            
            # Get current timestamp for filenames
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Adjust output paths to include timestamp
            output_base = os.path.splitext(output_csv)[0]
            csv_output = f"{output_base}_{timestamp}.csv"
            md_output = f"{output_base}_{timestamp}.md"
            
            # Find all text files in the directory
            note_files = list(Path(note_dir).glob('*.txt'))
            
            if not note_files:
                print(f"No .txt files found in {note_dir}")
                return
                
            # Get current date for extraction date
            extraction_date = datetime.datetime.now().strftime("%Y-%m-%d")
                
            # Process each note and collect results
            all_data = []
            all_notes_content = {}
            
            for note_file in note_files:
                print(f"Processing {note_file.name}...")
                
                # Read the full medical note content
                with open(note_file, 'r', encoding='utf-8') as f:
                    medical_note_content = f.read()
                all_notes_content[note_file.name] = medical_note_content
                
                cancer_type, cancer_category, clinical_stage, pathologic_stage, tnm_values, explanation, report, proceed_with_staging = self.process_medical_note(str(note_file))
                
                # Remove signature block from report
                signature_block_text = "This report is generated for inclusion in the patient's medical records and should be reviewed in conjunction with all other clinical information available for comprehensive care planning."
                if signature_block_text in report:
                    # Find the position where the signature block starts
                    pos = report.find(signature_block_text)
                    # Trim the report to exclude the signature block
                    report = report[:pos].strip()
                
                # Add to data list
                all_data.append({
                    'Medical Note': note_file.name,
                    'Date of Extraction': extraction_date,
                    'Disease': cancer_type,
                    'Category': cancer_category,
                    'System': 'AJCC8 system',
                    'TNM Values': tnm_values,
                    'Extracted Stage': tnm_values,  # The TNM values from the note
                    'Clinical Stage': clinical_stage,
                    'Pathologic Stage': pathologic_stage,
                    'AI Stage': f"Clinical: {clinical_stage}, Pathologic: {pathologic_stage}",
                    'Proceed with Staging': "Yes" if proceed_with_staging else "No",
                    'Explanation': explanation,
                    'Report': report
                })
                
            # Create a DataFrame
            df = pd.DataFrame(all_data)
            
            # Save to CSV
            df.to_csv(csv_output, index=False)
            print(f"CSV results saved to: {csv_output}")
            
            # Generate a comprehensive markdown report
            markdown = "# Cancer Staging Report - Multiple Notes\n\n"
            markdown += f"**Date of Extraction:** {extraction_date}\n\n"
            markdown += f"**Number of Notes Processed:** {len(all_data)}\n\n"
            
            # Add explanation of cancer staging terminology
            markdown += "## Understanding Cancer Staging Terminology\n\n"
            markdown += "This report uses the following terms for cancer staging:\n\n"
            markdown += "- **TNM Values**: The raw TNM classification notation (T=Tumor size/extent, N=Node involvement, M=Metastasis) directly extracted from the medical note. Prefixes like 'c' indicate clinical staging, 'p' indicates pathologic staging.\n\n"
            markdown += "- **Extracted Stage**: The exact staging information as written in the original medical note, representing how the healthcare provider documented the stage.\n\n"
            markdown += "- **AI Stage Determination**: The system's interpretation based on AJCC 8th Edition guidelines, consisting of:\n"
            markdown += "  - **Clinical Stage**: Full stage interpretation including TNM values and formal stage grouping based on examinations and imaging\n"
            markdown += "  - **Pathologic Stage**: Stage determination based on surgical/pathological findings (when available)\n\n"
            
            # Add summary section
            markdown += "## Summary of Results\n\n"
            markdown += "| Medical Note | Disease | Category | Clinical Stage | Pathologic Stage |\n"
            markdown += "|-------------|---------|----------|----------------|------------------|\n"
            
            for item in all_data:
                markdown += f"| {item['Medical Note']} | {item['Disease']} | {item['Category']} | {item['Clinical Stage']} | {item['Pathologic Stage']} |\n"
            
            markdown += "\n## Detailed Results\n\n"
            
            # Add detailed section for each note
            for item in all_data:
                markdown += f"### Medical Note: {item['Medical Note']}\n\n"
                markdown += f"**Disease:** {item['Disease']}\n\n"
                markdown += f"**Category:** {item['Category']}\n\n"
                markdown += f"**System:** {item['System']}\n\n"
                markdown += f"**TNM Values:** {item['TNM Values']}\n\n"
                markdown += f"**Extracted Stage:** {item['Extracted Stage']}\n\n"
                markdown += f"**AI Stage Determination:**\n\n"
                markdown += f"- Clinical Stage: {item['Clinical Stage']}\n"
                markdown += f"- Pathologic Stage: {item['Pathologic Stage']}\n\n"
                markdown += f"**Detailed Explanation:**\n\n{item['Explanation']}\n\n"
                
                # Process the report to remove the signature block
                report = item['Report']
                signature_block_text = "This report is generated for inclusion in the patient's medical records and should be reviewed in conjunction with all other clinical information available for comprehensive care planning."
                if signature_block_text in report:
                    # Find the position where the signature block starts
                    pos = report.find(signature_block_text)
                    # Trim the report to exclude the signature block
                    report = report[:pos].strip()
                
                markdown += f"**Staging Report:**\n\n{report}\n\n"
            
            # Add complete medical notes section
            markdown += "## Complete Medical Notes\n\n"
            for note_name, note_content in all_notes_content.items():
                markdown += f"### {note_name}\n\n"
                markdown += "```\n"
                markdown += note_content
                markdown += "\n```\n\n"
            
            # Save markdown report
            with open(md_output, 'w', encoding='utf-8') as f:
                f.write(markdown)
            print(f"Markdown report saved to: {md_output}")
            
        except Exception as e:
            print(f"Error processing notes in {note_dir}: {e}")
            raise 