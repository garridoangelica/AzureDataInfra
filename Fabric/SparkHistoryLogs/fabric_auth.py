"""
Microsoft Fabric API Authentication Module
Supports multiple authentication methods for your own credentials
"""

import os
import json
import requests
from datetime import datetime
from azure.identity import (
    ClientSecretCredential, 
    InteractiveBrowserCredential, 
    AzureCliCredential,
)
from dotenv import load_dotenv


class FabricAuthenticator:
    """Handles various authentication methods for Microsoft Fabric API"""
    
    def __init__(self):
        self.token = None
        self.credential = None
        self.tenant_id = None
        
        # Load environment variables
        script_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(script_dir, '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
    
    def authenticate_service_principal(self, client_id=None, client_secret=None, tenant_id=None):
        """
        Authenticate using Service Principal credentials
        
        Args:
            client_id: Azure AD application client ID (optional, can use env var)
            client_secret: Azure AD application client secret (optional, can use env var)
            tenant_id: Azure AD tenant ID (optional, can use env var)
        """
        # Use provided credentials or fall back to environment variables
        client_id = client_id or os.getenv('FABRICSPN_CLIENTID') or os.getenv('AZURE_CLIENT_ID')
        client_secret = client_secret or os.getenv('FABRICSPN_SECRET') or os.getenv('AZURE_CLIENT_SECRET')
        tenant_id = tenant_id or os.getenv('FABRICSPN_TENANTID') or os.getenv('AZURE_TENANT_ID')
        
        if not all([client_id, client_secret, tenant_id]):
            missing = []
            if not client_id: missing.append('client_id')
            if not client_secret: missing.append('client_secret')
            if not tenant_id: missing.append('tenant_id')
            raise ValueError(f"Missing credentials: {', '.join(missing)}")
        
        print("🔐 Authenticating with Service Principal...")
        self.credential = ClientSecretCredential(tenant_id, client_id, client_secret)
        self.tenant_id = tenant_id
        
        return self._get_token()
    
    def authenticate_interactive(self, tenant_id=None):
        """
        Authenticate using interactive browser login
        
        Args:
            tenant_id: Azure AD tenant ID (optional)
        """
        tenant_id = tenant_id or os.getenv('FABRICSPN_TENANTID') or os.getenv('AZURE_TENANT_ID')
        
        print("🌐 Opening browser for interactive authentication...")
        if tenant_id:
            self.credential = InteractiveBrowserCredential(tenant_id=tenant_id)
        else:
            self.credential = InteractiveBrowserCredential()
        
        self.tenant_id = tenant_id
        return self._get_token()
    
    def authenticate_azure_cli(self):
        """
        Use Azure CLI credentials (requires 'az login' to be run first)
        """
        print("* Using Azure CLI credentials...")
        self.credential = AzureCliCredential()
        return self._get_token()
       
    def _get_token(self):
        """Get access token for Fabric API"""
        if not self.credential:
            raise ValueError("No credential configured. Call an authenticate_* method first.")
        
        try:
            # Try Power BI scope first (recommended for Fabric)
            scopes_to_try = [
                # "https://analysis.windows.net/powerbi/api/.default",
                "https://api.fabric.microsoft.com/.default"
            ]
            
            for scope in scopes_to_try:
                try:
                    print(f"* Requesting token with scope: {scope}")
                    token_response = self.credential.get_token(scope)
                    self.token = token_response.token
                    expires_at = datetime.fromtimestamp(token_response.expires_on)
                    print(f"+ Token acquired successfully!")
                    print(f"   Expires at: {expires_at}")
                    return self.token
                except Exception as e:
                    print(f"❌ Failed with scope {scope}: {str(e)[:100]}")
                    continue
            
            raise Exception("Failed to acquire token with any scope")
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            raise
    
    def get_headers(self):
        """Get HTTP headers with authorization token"""
        if not self.token:
            self._get_token()
        
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

if __name__ == "__main__":
    print()