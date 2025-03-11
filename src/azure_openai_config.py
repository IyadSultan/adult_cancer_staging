"""
Configuration module for Azure OpenAI integration.
"""

import os
from langchain.chat_models.azure_openai import AzureChatOpenAI

def get_azure_openai_llm(model_name="gpt-4o-mini", deployment_name=None):
    """
    Configure and return an Azure OpenAI LLM instance.
    
    Args:
        model_name (str): The name of the model to use
        deployment_name (str, optional): The deployment name to use. If None, will use AZURE_GPT4O_DEPLOYMENT.
    
    Returns:
        AzureChatOpenAI: The configured Azure OpenAI LLM
    """
    # Get Azure OpenAI settings from environment variables
    api_key = os.getenv("AZURE_API_KEY")
    api_version = os.getenv("AZURE_API_VERSION")
    endpoint = os.getenv("AZURE_ENDPOINT")
    
    if not deployment_name:
        deployment_name = os.getenv("AZURE_GPT4O_DEPLOYMENT")
    
    if not deployment_name:
        deployment_name = model_name
    
    # For CrewAI compatibility, also set OpenAI environment variables
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_API_BASE"] = endpoint
    os.environ["OPENAI_API_VERSION"] = api_version
    os.environ["OPENAI_API_TYPE"] = "azure"
    
    # Create Azure OpenAI LLM with the appropriate configuration
    llm = AzureChatOpenAI(
        model=model_name,
        api_version=api_version,
        api_key=api_key,
        base_url=endpoint,
        deployment_name=deployment_name,
        azure_deployment=deployment_name,  # Added for backward compatibility
    )
    
    return llm 