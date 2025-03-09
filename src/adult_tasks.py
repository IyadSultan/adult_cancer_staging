from crewai import Task
from typing import Dict, Any, List

class AdultCancerStagingTasks:
    """
    Provides tasks for adult cancer staging workflow for all cancer types in AJCC 8th Edition.
    """
    
    @staticmethod
    def identify_cancer_type(agent, medical_note: str, staging_data: Dict[str, Any], 
                            available_categories: List[str] = None, 
                            disease_mapping: Dict[str, str] = None) -> Task:
        """
        Creates a task to identify the cancer type and TNM values from medical notes,
        and verify the cancer exists in the AJCC8.json file.
        
        Args:
            agent: The agent to assign this task to
            medical_note: The medical note content
            staging_data: AJCC 8th Edition staging system data
            available_categories: List of available cancer categories in AJCC8
            disease_mapping: Mapping of disease names to their AJCC8 categories
            
        Returns:
            Task: A CrewAI task for cancer identification
        """
        # Use provided categories or extract them if not provided
        if available_categories is None:
            try:
                if isinstance(staging_data, dict):
                    available_categories = list(staging_data.keys())
                elif isinstance(staging_data, list):
                    available_categories = [item.get('name', '') for item in staging_data if isinstance(item, dict) and 'name' in item]
                else:
                    available_categories = []
            except:
                available_categories = ["Cancer categories could not be loaded from staging data"]
        
        # Prepare disease mapping information
        mapping_examples = ""
        if disease_mapping:
            # Take a subset of mapping examples to show the agent
            mapping_sample = list(disease_mapping.items())[:20]  # Show first 20 as examples
            mapping_examples = "\n".join([f"- '{key}' maps to category '{value}'" 
                                         for key, value in mapping_sample])
        
        # General guidance for disease identification
        special_guidance = """
        IMPORTANT NOTES FOR DISEASE IDENTIFICATION:
        - The cancer type you identify must be properly mapped to an AJCC category to enable staging
        - If you identify a specific cancer type, check if it's in the available categories or maps to one of them
        - Many cancers may be described in different ways but belong to specific AJCC categories
        - Use the disease mapping examples as a guide for how different terms map to official categories
        - If the identified cancer is not found in the mapping or categories, mark it as 'Not in AJCC 8th Edition'
        - Only proceed with staging when there's a clear match to an AJCC category
        """
        
        return Task(
            description=f"""
            Analyze the provided medical note carefully to identify the specific cancer type 
            from the AJCC 8th Edition staging system.
            
            If multiple cancer types are mentioned, select the one that appears to be the primary diagnosis.
            
            Also extract any TNM values mentioned in the note (e.g., T2N1M0). If no TNM values are mentioned, 
            indicate 'Not provided'.
            
            IMPORTANT: After identifying the cancer type, verify that it exists in one of the AJCC 8th Edition 
            cancer categories. If the identified cancer does not belong to any of these categories, indicate 
            'Not in AJCC 8th Edition' and do not proceed with staging.
            
            Be aware that diseases may appear under different names but belong to specific categories.
            Always look for the broader category a specific cancer might belong to.
            
            {special_guidance}
            
            Medical Note:
            {medical_note}
            
            Available Cancer Categories in AJCC 8th Edition:
            {', '.join(available_categories)}
            
            Disease Mapping Examples:
            {mapping_examples}
            
            Your response should follow this format:
            Cancer Type: [Identified cancer type]
            Cancer Category: [The AJCC category it belongs to, or 'Not in AJCC 8th Edition']
            TNM Values: [Extracted TNM values or 'Not provided']
            Proceed with Staging: [Yes/No] (Only 'Yes' if the cancer exists in AJCC 8th Edition)
            """,
            expected_output="Identification of specific cancer type, its category, TNM values, and whether to proceed with staging",
            agent=agent
        )
    
    @staticmethod
    def analyze_staging_criteria(agent, medical_note: str, cancer_type: str, cancer_category: str, tnm_values: str, staging_data: Dict[str, Any]) -> Task:
        """
        Creates a task to analyze which staging criteria are present for a specific cancer type.
        
        Args:
            agent: The agent to assign this task to
            medical_note: The medical note content
            cancer_type: The identified cancer type
            cancer_category: The AJCC category the cancer belongs to
            tnm_values: TNM values extracted from the note
            staging_data: AJCC 8th Edition staging data
            
        Returns:
            Task: A CrewAI task for criteria analysis
        """
        # Get clinical and pathologic criteria for the specific cancer type
        try:
            clinical_criteria = staging_data.get(cancer_category, {}).get(cancer_type, {}).get("clinical", {})
            pathologic_criteria = staging_data.get(cancer_category, {}).get(cancer_type, {}).get("pathologic", {})
        except:
            clinical_criteria = {}
            pathologic_criteria = {}
        
        return Task(
            description=f"""
            Carefully analyze the provided medical note to identify which staging criteria 
            for {cancer_type} (in the {cancer_category} category) are present, according to the AJCC 8th Edition staging system.
            
            Distinguish between clinical criteria (based on physical exam, imaging, and pre-surgical findings) 
            and pathologic criteria (based on surgical findings and pathology reports).
            
            Medical Note:
            {medical_note}
            
            TNM Values (if provided): {tnm_values}
            
            Clinical Criteria to check for {cancer_type}:
            {clinical_criteria}
            
            Pathologic Criteria to check for {cancer_type}:
            {pathologic_criteria}
            
            Your analysis should include:
            1. Evidence for specific T category (tumor size, extent, invasion)
            2. Evidence for specific N category (lymph node involvement)
            3. Evidence for specific M category (distant metastasis)
            4. Any other relevant staging factors (if applicable)
            
            For each criterion, specify whether it is a clinical finding or a pathologic finding, 
            and cite the exact text from the medical note that supports this.
            """,
            expected_output="Detailed analysis of present clinical and pathologic staging criteria with supporting evidence from the medical note",
            agent=agent
        )
    
    @staticmethod
    def calculate_stage(agent, medical_note: str, cancer_type: str, cancer_category: str, tnm_values: str, criteria_analysis: str, staging_data: Dict[str, Any]) -> Task:
        """
        Creates a task to calculate the clinical and pathologic stages based on criteria.
        
        Args:
            agent: The agent to assign this task to
            medical_note: The medical note content
            cancer_type: The identified cancer type
            cancer_category: The AJCC category the cancer belongs to
            tnm_values: TNM values extracted from the note
            criteria_analysis: The detailed analysis of present staging criteria
            staging_data: AJCC 8th Edition staging data
            
        Returns:
            Task: A CrewAI task for stage calculation
        """
        # Get clinical and pathologic stage groupings for the specific cancer type
        try:
            clinical_stage_groupings = staging_data.get(cancer_category, {}).get(cancer_type, {}).get("clinical", {}).get("Stage_Groupings", {})
            pathologic_stage_groupings = staging_data.get(cancer_category, {}).get(cancer_type, {}).get("pathologic", {}).get("Stage_Groupings", {})
        except:
            clinical_stage_groupings = {}
            pathologic_stage_groupings = {}
        
        return Task(
            description=f"""
            Based on the identified criteria and the AJCC 8th Edition staging system for {cancer_type} (in the {cancer_category} category), 
            determine both the clinical stage and pathologic stage (if sufficient information is available).
            
            Medical Note:
            {medical_note}
            
            TNM Values (if provided): {tnm_values}
            
            Criteria Analysis:
            {criteria_analysis}
            
            Clinical Stage Groupings for {cancer_type}:
            {clinical_stage_groupings}
            
            Pathologic Stage Groupings for {cancer_type}:
            {pathologic_stage_groupings}
            
            Your response should follow this format:
            Clinical Stage: [Determined stage or 'Insufficient information']
            Pathologic Stage: [Determined stage or 'Insufficient information']
            Explanation: [Detailed explanation of how you determined the stage based on the present criteria]
            """,
            expected_output="Determination of clinical and pathologic stages with detailed explanation",
            agent=agent
        )
    
    @staticmethod
    def generate_report(agent, medical_note: str, cancer_type: str, cancer_category: str, clinical_stage: str, 
                         pathologic_stage: str, tnm_values: str, criteria_analysis: str, explanation: str) -> Task:
        """
        Creates a task to generate a comprehensive staging report.
        
        Args:
            agent: The agent to assign this task to
            medical_note: The medical note content
            cancer_type: The identified cancer type
            cancer_category: The AJCC category the cancer belongs to
            clinical_stage: The determined clinical stage
            pathologic_stage: The determined pathologic stage
            tnm_values: TNM values extracted from the note
            criteria_analysis: The detailed analysis of present staging criteria
            explanation: The explanation for the stage determination
            
        Returns:
            Task: A CrewAI task for report generation
        """
        return Task(
            description=f"""
            Generate a comprehensive and professionally formatted cancer staging report 
            based on the analysis of the medical note. The report should be suitable for inclusion 
            in a patient's medical record.
            
            Patient Information:
            [Extract relevant non-identifying patient information from the medical note]
            
            Diagnosis: {cancer_type} (Category: {cancer_category})
            
            TNM Values: {tnm_values}
            
            Clinical Stage: {clinical_stage}
            
            Pathologic Stage: {pathologic_stage}
            
            Criteria Analysis Summary:
            {criteria_analysis}
            
            Stage Determination:
            {explanation}
            
            Your report should include:
            1. A brief summary of the case
            2. The TNM classification (clinical and/or pathologic as applicable)
            3. The overall stage (clinical and/or pathologic as applicable)
            4. Key findings that determined the stage
            5. Any important prognostic factors
            6. Any limitations or uncertainties in the staging determination
            
            Format the report in a clear, professional manner suitable for medical documentation.
            """,
            expected_output="Comprehensive, professionally formatted cancer staging report",
            agent=agent
        ) 