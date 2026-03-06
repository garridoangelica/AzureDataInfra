# Add the source directory to the sys.path If I'm doing local dev with no launch.json
# import sys
# src_path = 'C:\\Users\\agarrido\\GitRepos\\AZUREDATAINFRA\\Fabric\\SparkHistoryServer'
# sys.path.insert(0, src_path)
################################################################

import time
from datetime import datetime,timedelta
from dateutil.parser import isoparse  
import requests
import os
import json
import tempfile
from pathlib import Path
from azure.identity import ClientSecretCredential, InteractiveBrowserCredential,AzureCliCredential
from fabric_auth import FabricAuthenticator
from livyconn import LivyAPIConnector
from console_utils import *

class SparkLogExtractor:
    """Class to extract Spark logs from all notebooks in a workspace"""
    
    def __init__(self, workspace_id: str, auth_method: str = "cli"):
        """
        Initialize the log extractor
        
        Args:
            workspace_id: Microsoft Fabric workspace ID
            auth_method: Authentication method ('cli', 'interactive', 'service_principal')
        """
        self.workspace_id = workspace_id
        self.auth_method = auth_method
        self.connector = LivyAPIConnector(
            workspace_id=workspace_id,
            auth_method=auth_method
        )
        
    def extract_all_logs(self):
        """Extract logs from all notebooks in the workspace"""
        # Test 1: Get workspaces
        workspaces = self.connector.get_workspaces()
        workspace_name = "unknown"
        if workspaces:
            print_success(f"Successfully accessed {highlight(str(len(workspaces)))} workspaces")
            # Find the workspace name for our workspace_id
            for workspace in workspaces:
                if workspace.get('id') == self.workspace_id:
                    workspace_name = workspace.get('displayName', 'unknown')
                    break

        # Test 2: Get notebooks and process all of them
        notebooks = self.connector.get_notebooks()
        if notebooks and 'value' in notebooks:
            print_success(f"Found {highlight(str(len(notebooks['value'])))} notebooks")
            
            total_sessions_processed = 0
            notebooks_with_sessions = 0
            
            # Process each notebook
            for notebook_idx, notebook in enumerate(notebooks['value']):
                notebook_id = notebook['id']
                notebook_name = notebook['displayName']
                
                print_subheader(f"{Emoji.PROCESS} Processing notebook {notebook_idx + 1}/{len(notebooks['value'])}", 60)
                print(f"  {Colors.BRIGHT_CYAN}Name:{Colors.RESET} {highlight(notebook_name)}")
                print(f"  {Colors.BRIGHT_CYAN}ID:{Colors.RESET} {Colors.BRIGHT_WHITE}{notebook_id}{Colors.RESET}")
                
                try:
                    # Get Livy sessions for this notebook
                    livy_sessions = self.connector.get_livy_sessions(notebook_id)
                    
                    if livy_sessions and 'value' in livy_sessions and livy_sessions['value']:
                        # Extract session information
                        session_info = self.connector.extract_session_info(livy_sessions)
                        
                        if session_info:
                            notebooks_with_sessions += 1
                            print_info(f"Found {highlight(str(len(session_info)))} sessions for this notebook")
                            
                            # Download logs for each session
                            for i, session in enumerate(session_info):
                                print(f"\n{Colors.BRIGHT_BLUE}{Emoji.PROCESS} Processing session {i+1}/{len(session_info)}{Colors.RESET}")
                                print(f"{Colors.CYAN}App ID:{Colors.RESET} {highlight(session['sparkApplicationId'])}")
                                print(f"{Colors.CYAN}Livy ID:{Colors.RESET} {highlight(session['livyId'])}")
                                print(f"{Colors.CYAN}State:{Colors.RESET} {highlight(session['state'])}")
                                
                                # Download logs to temp directory
                                result = self.connector.download_logs_to_temp(
                                    notebook_id, 
                                    session['sparkApplicationId'], 
                                    session['livyId'],
                                    notebook_name=notebook_name,
                                    workspace_name=workspace_name
                                )
                                
                                if result:
                                    total_sessions_processed += 1
                                    print_success(f"Logs downloaded successfully!")
                                    print(f"  {Colors.BRIGHT_GREEN}Directory:{Colors.RESET} {result['temp_directory']}")
                                    print(f"  {Colors.BRIGHT_GREEN}Files:{Colors.RESET} {highlight(str(len(result['downloaded_files'])))} files")
                                else:
                                    print_error(f"Failed to download logs for this session")
                        else:
                            print_info(f"No active sessions found with sparkApplicationId and livyId")
                    else:
                        print_info(f"No Livy sessions found for this notebook")
                        
                except Exception as e:
                    print_error(f"Error processing notebook {notebook_name}: {e}")
                    continue
            
            # Finalize the consolidated file with final statistics
            consolidated_file_path = self.connector.finalize_consolidated_file(
                total_notebooks=len(notebooks['value']),
                notebooks_with_sessions=notebooks_with_sessions,
                workspace_name=workspace_name
            )
            
            # Summary
            print_header(f"{Emoji.CHART} SUMMARY", 60)
            print(f"📚 Total notebooks processed: {len(notebooks['value'])}")
            print(f"* Notebooks with active sessions: {notebooks_with_sessions}")
            print(f"* Total sessions processed: {total_sessions_processed}")
            if consolidated_file_path:
                print(f"+ Consolidated log file: {consolidated_file_path}")
            print(f"{'='*60}")
            
            return consolidated_file_path
        else:
            print("❌ No notebooks found in workspace")
            return None


def main():
    """Original main function for backwards compatibility"""
    workspace_id = ""
    auth_method = "cli"
    
    extractor = SparkLogExtractor(workspace_id, auth_method)
    return extractor.extract_all_logs()
    
if __name__ == "__main__":
    main()


################################## Old code snippets for reference ##################################
def _get_livy_sessions_simple():
    def _get_token(type):
        """
        Get an access token using a service principal.
        """
        tenant_id =  ""

        if type == 'spn':
            # Use environment variables for security - never hardcode secrets!
            client_id = os.getenv('FABRICSPN_CLIENTID', "your-client-id-here")
            client_secret = os.getenv('FABRICSPN_SECRET', "your-client-secret-here")
            credential = ClientSecretCredential(tenant_id, client_id, client_secret)
            token = credential.get_token("https://api.fabric.microsoft.com/.default").token
            return token
        
        elif type == 'interactive':
            # credential = ClientSecretCredential(tenant_id, client_id, client_secret)
            credential = AzureCliCredential()#InteractiveBrowserCredential(tenant_id=tenant_id)
            token = credential.get_token("https://api.fabric.microsoft.com/.default").token
            return token
    def _get_headers(type):
        headers = {
        "Authorization": f"Bearer {_get_token(type)}",
        "Content-Type": "application/json"
        }
        return headers

    workspace_id = ""
    notebook_id = ''

    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/notebooks/{notebook_id}/livySessions"
    sessions_dict = requests.get(url, headers=_get_headers('interactive')).json()
    # print(sessions_dict['value'])
    app_id = sessions_dict['value'][0]['sparkApplicationId']
    livy_id = sessions_dict['value'][0]['livyId']

    # Get Livy Logs
    url= f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/notebooks/{notebook_id}/livySessions/{livy_id}/applications/{app_id}/logs?type=livy&isDownload=true"
    app_logs = requests.get(url, headers=_get_headers('interactive'))

    # Get Driver StdOut Logs
    filename = "stdout"
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/notebooks/{notebook_id}/livySessions/{livy_id}/applications/{app_id}/logs?type=driver&fileName={filename}"
    driver_stdout_logs = requests.get(url, headers=_get_headers('interactive'))

    print(driver_stdout_logs.content)
    # Get Driver stderr logs 
    filename = "stderr"
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/notebooks/{notebook_id}/livySessions/{livy_id}/applications/{app_id}/logs?type=driver&fileName={filename}"
    driver_stderr_logs = requests.get(url, headers=_get_headers('interactive'))