"""
Authentication module for Fabric deployment.
Supports both interactive and Azure CLI-based authentication.
"""
import os
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential, AzureCliCredential


def get_fabric_credential(use_cli=False):
    """
    Get Azure credential for Fabric authentication.
    
    Args:
        use_cli: If True, use Azure CLI authentication (for CI/CD).
                 If False, use interactive browser authentication (for local).
    
    Returns:
        Azure credential object
    """
    if use_cli or os.getenv("GITHUB_ACTIONS") == "true":
        print("Using Azure CLI authentication...")
        return AzureCliCredential()
    else:
        print("Using interactive browser authentication...")
        return InteractiveBrowserCredential()


def get_token(credential, scope="https://api.fabric.microsoft.com/.default"):
    """
    Get access token for Fabric API.
    
    Args:
        credential: Azure credential object
        scope: Authentication scope
    
    Returns:
        Access token string
    """
    token = credential.get_token(scope)
    return token.token
