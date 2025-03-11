from crewai import Agent
from typing import Dict, Any, List, Optional
from .azure_openai_config import get_azure_openai_llm
import os

class AdultCancerStagingAgents:
    """
    Provides agents for adult cancer staging tasks for all cancer types in AJCC 8th Edition.
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize the agent creator with the specified model.
        
        Args:
            model (str): The OpenAI model to use
        """
        self.model = model
        # Get the deployment name from environment variable
        self.deployment_name = os.getenv("AZURE_GPT4O_DEPLOYMENT", model)
        # Format model name for LiteLLM - azure/<deployment_name>
        self.azure_model = f"azure/{self.deployment_name}" 
        # Get Azure LLM for LangChain integration
        self.llm = get_azure_openai_llm(model_name=model, deployment_name=self.deployment_name)
    
    def create_cancer_identifier_agent(self) -> Agent:
        """
        Creates an agent specialized in identifying cancer types
        and extracting TNM values from medical notes.
        
        Returns:
            Agent: A CrewAI agent for cancer identification
        """
        return Agent(
            role="Oncology Specialist",
            goal="Identify the specific cancer type and any mentioned TNM values in medical notes, verifying the cancer exists in AJCC 8th Edition",
            backstory="""You are a specialist in oncology with extensive experience
            in diagnosing various types of cancers. Your expertise allows you to quickly 
            identify specific cancer subtypes from medical notes, pathology
            reports, and imaging studies, and extract any TNM staging information that may be mentioned.
            You also verify that the identified cancer type exists in the AJCC 8th Edition staging system
            before proceeding with staging.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            # For CrewAI direct integration - this is a fallback
            llm_config={"model": self.azure_model}
        )
    
    def create_criteria_analyzer_agent(self) -> Agent:
        """
        Creates an agent specialized in analyzing staging criteria for all cancer types
        using the AJCC 8th Edition staging system.
        
        Returns:
            Agent: A CrewAI agent for staging criteria analysis
        """
        return Agent(
            role="AJCC Cancer Staging Specialist",
            goal="Identify which staging criteria are present in the medical notes for a specific cancer type",
            backstory="""You are a specialist in cancer staging with deep knowledge
            of the AJCC 8th Edition staging system. Your expertise allows you to meticulously analyze
            medical notes and identify which specific staging criteria are present for a
            particular cancer type, distinguishing between clinical and pathologic findings.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            # For CrewAI direct integration - this is a fallback
            llm_config={"model": self.azure_model}
        )
    
    def create_stage_calculator_agent(self) -> Agent:
        """
        Creates an agent specialized in calculating the AJCC 8th Edition stage based on criteria.
        
        Returns:
            Agent: A CrewAI agent for stage calculation
        """
        return Agent(
            role="Cancer Stage Calculator",
            goal="Calculate the clinical and pathologic stages based on identified criteria using AJCC 8th Edition",
            backstory="""You are an expert in applying the AJCC 8th Edition staging system for 
            all cancer types. Your deep understanding of the staging system allows you
            to accurately determine both clinical and pathologic stages based on the criteria present in the
            medical notes. You are familiar with all the nuances of the TNM classification system
            and stage groupings specific to different cancer types.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            # For CrewAI direct integration - this is a fallback
            llm_config={"model": self.azure_model}
        )
    
    def create_report_generator_agent(self) -> Agent:
        """
        Creates an agent specialized in generating comprehensive staging reports.
        
        Returns:
            Agent: A CrewAI agent for report generation
        """
        return Agent(
            role="Cancer Staging Report Specialist",
            goal="Generate comprehensive and accurate staging reports for all cancer types",
            backstory="""You are a specialized report writer with expertise in cancer staging.
            Your reports are clear, concise, and follow standard medical documentation format. You can
            explain complex staging decisions in a way that is understandable to both specialists and
            non-specialists alike. You always include all the relevant TNM values, stage groupings,
            and explanations of how the stage was determined based on the AJCC 8th Edition criteria.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            # For CrewAI direct integration - this is a fallback
            llm_config={"model": self.azure_model}
        ) 