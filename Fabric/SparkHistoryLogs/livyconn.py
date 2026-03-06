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

class LivyAPIConnector:
    """Livy API connector with flexible authentication"""
    
    def __init__(self, workspace_id=None, auth_method="auto"):
        self.workspace_id = workspace_id
        self.authenticator = FabricAuthenticator()
        self.auth_method = auth_method
        
        # Create output directory if it doesn't exist
        import os
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set consolidated file path in output directory
        filename = f"consolidated_spark_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.consolidated_file = os.path.join(self.output_dir, filename)
        self.consolidated_metadata = None
        
        # Initialize authentication
        self._authenticate()
    
    def _authenticate(self):
        """Initialize authentication based on specified method"""
        try:
            if self.auth_method == "service_principal":
                self.authenticator.authenticate_service_principal()
            elif self.auth_method == "interactive":
                self.authenticator.authenticate_interactive()
            elif self.auth_method == "cli":
                self.authenticator.authenticate_azure_cli()
                
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            print("💡 Try a different authentication method or check your credentials")
            raise
    
    def get_headers(self):
        """Get HTTP headers with authorization"""
        return self.authenticator.get_headers()
    
    def _build_url(self, base_type, workspace_id, item_id=None, job_id=None, 
                   item_type='Notebook', continuation_token=None):
        """Build API URLs for different endpoint types"""
        
        base_urls = {
            "items": f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items?type={item_type}",
            "notebook_id": f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/notebooks/{item_id}",
            "instances": f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/notebooks/{item_id}/jobs/instances",
            "livySessions": f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/notebooks/{item_id}/livySessions"
        }
        
        if base_type not in base_urls:
            raise ValueError(f"Unknown base_type: {base_type}")
        
        url = base_urls[base_type]
        
        if continuation_token:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}continuationToken={continuation_token}"
        
        return url

    def make_request(self, base_type, workspace_id, item_id=None, job_id=None,
                    item_type='Notebook', continuation_token=None):
        """Make API request with proper error handling"""
        
        url = self._build_url(base_type, workspace_id, item_id, job_id, 
                             item_type, continuation_token)
        
        print(f"* Making request to: {url}")
        
        try:
            headers = self.get_headers()
            response = requests.get(url, headers=headers, timeout=30)
            
            # Log response details
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                print("🔐 Authentication error - token may have expired")
                # Try to refresh authentication
                self._authenticate()
                headers = self.get_headers()
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code == 200:
                    return response.json()
            elif response.status_code == 403:
                print("🚫 Access forbidden - check workspace permissions")
            elif response.status_code == 404:
                print("❓ Resource not found - check workspace/item IDs")
            
            print(f"❌ Request failed: {response.text}")
            response.raise_for_status()
            
        except requests.exceptions.Timeout:
            print("⏱️ Request timed out")
            raise
        except requests.exceptions.RequestException as e:
            print(f"- Network error: {e}")
            raise
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            raise

    def get_workspaces(self):
        """Get all accessible workspaces"""
        print("* Getting workspaces...")
        url = "https://api.fabric.microsoft.com/v1/workspaces"
        
        try:
            headers = self.get_headers()
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                workspaces = response.json().get('value', [])
                print(f"+ Found {len(workspaces)} workspaces")
                return workspaces
            else:
                print(f"❌ Failed to get workspaces: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting workspaces: {e}")
            return []
        
    def get_notebooks(self, workspace_id=None):
        """Get all notebooks in a workspace"""
        workspace_id = workspace_id or self.workspace_id
        if not workspace_id:
            raise ValueError("workspace_id is required")
            
        print(f"* Getting notebooks from workspace: {workspace_id}")
        return self.make_request("items", workspace_id, item_type="Notebook")

    def get_livy_sessions(self, notebook_id, workspace_id=None):
        """Get Livy sessions for a specific notebook"""
        workspace_id = workspace_id or self.workspace_id
        if not workspace_id:
            raise ValueError("workspace_id is required")
            
        print(f"* Getting Livy sessions for notebook: {notebook_id}")
        return self.make_request("livySessions", workspace_id, notebook_id)

    def extract_session_info(self, livy_sessions):
        """Extract sparkApplicationId and livyId from livy sessions"""
        session_info = []
        
        if livy_sessions and 'value' in livy_sessions:
            for session in livy_sessions['value']:
                if 'sparkApplicationId' in session and 'livyId' in session:
                    info = {
                        'sparkApplicationId': session['sparkApplicationId'],
                        'livyId': session['livyId'],
                        'state': session.get('state', 'unknown'),
                        'name': session.get('name', 'unknown')
                    }
                    session_info.append(info)
                    print(f"📝 Found session - App ID: {info['sparkApplicationId']}, Livy ID: {info['livyId']}, State: {info['state']}")
        
        return session_info

    def download_logs_to_temp(self, notebook_id, spark_app_id, livy_id, notebook_name=None, workspace_name=None, workspace_id=None):
        """Download Livy, stdout, and stderr logs to a temporary directory"""
        workspace_id = workspace_id or self.workspace_id
        if not workspace_id:
            raise ValueError("workspace_id is required")
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix=f"spark_logs_{livy_id}_")
        temp_path = Path(temp_dir)
        
        print(f"+ Created temp directory: {temp_dir}")
        
        headers = self.get_headers()
        base_url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/notebooks/{notebook_id}/livySessions/{livy_id}/applications/{spark_app_id}/logs"
        
        logs_downloaded = []
        
        try:
            # 1. Download Livy logs
            print("* Downloading Livy logs...")
            livy_url = f"{base_url}?type=livy&isDownload=true"
            livy_response = requests.get(livy_url, headers=headers, timeout=60)
            
            if livy_response.status_code == 200:
                livy_file = temp_path / "livy_logs.txt"
                with open(livy_file, 'wb') as f:
                    f.write(livy_response.content)
                logs_downloaded.append(str(livy_file))
                print(f"+ Livy logs saved: {livy_file}")
            else:
                print(f"❌ Failed to download Livy logs: {livy_response.status_code}")
            
            # 2. Download stdout logs
            print("* Downloading stdout logs...")
            stdout_url = f"{base_url}?type=driver&fileName=stdout"
            stdout_response = requests.get(stdout_url, headers=headers, timeout=60)
            
            if stdout_response.status_code == 200:
                stdout_file = temp_path / "driver_stdout.log"
                with open(stdout_file, 'wb') as f:
                    f.write(stdout_response.content)
                logs_downloaded.append(str(stdout_file))
                print(f"+ Stdout logs saved: {stdout_file}")
            else:
                print(f"❌ Failed to download stdout logs: {stdout_response.status_code}")
            
            # 3. Download stderr logs
            print("* Downloading stderr logs...")
            stderr_url = f"{base_url}?type=driver&fileName=stderr"
            stderr_response = requests.get(stderr_url, headers=headers, timeout=60)
            
            if stderr_response.status_code == 200:
                stderr_file = temp_path / "driver_stderr.log"
                with open(stderr_file, 'wb') as f:
                    f.write(stderr_response.content)
                logs_downloaded.append(str(stderr_file))
                print(f"+ Stderr logs saved: {stderr_file}")
            else:
                print(f"❌ Failed to download stderr logs: {stderr_response.status_code}")
            
            # Create a summary file
            summary_file = temp_path / "log_summary.json"
            summary = {
                "spark_application_id": spark_app_id,
                "livy_id": livy_id,
                "app_url": f"https://app.powerbi.com/workloads/de-ds/sparkmonitor/{notebook_id}/{livy_id}?experience=power-bi",
                "notebook_id": notebook_id,
                "notebook_name": notebook_name or "unknown",
                "workspace_id": workspace_id,
                "workspace_name": workspace_name or "unknown",
                "temp_directory": temp_dir,
                "downloaded_files": logs_downloaded,
                "download_timestamp": datetime.now().isoformat()
            }
            
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            print(f"+ Log summary saved: {summary_file}")
            print(f"+ All logs saved to: {temp_dir}")
            
            # Append to consolidated file
            self.append_to_consolidated_file(summary)
            
            return {
                "temp_directory": temp_dir,
                "downloaded_files": logs_downloaded,
                "summary_file": str(summary_file)
            }
            
        except Exception as e:
            print(f"❌ Error downloading logs: {e}")
            return None
    
    def append_to_consolidated_file(self, log_summary):
        """Append a log summary to the consolidated file"""
        try:
            # Read current file
            if os.path.exists(self.consolidated_file):
                with open(self.consolidated_file, 'r') as f:
                    data = json.load(f)
            else:
                # If file doesn't exist, create initial structure
                data = self.consolidated_metadata or {
                    "metadata": {
                        "workspace_id": self.workspace_id,
                        "workspace_name": "unknown",
                        "consolidation_started": datetime.now().isoformat(),
                        "total_sessions_processed": 0
                    },
                    "log_summaries": []
                }
            
            # Append new summary
            data["log_summaries"].append(log_summary)
            data["metadata"]["total_sessions_processed"] = len(data["log_summaries"])
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # Write back to file
            with open(self.consolidated_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"+ Appended session to consolidated file ({len(data['log_summaries'])} total)")
            
        except Exception as e:
            print(f"❌ Failed to append to consolidated file: {e}")
    
    def finalize_consolidated_file(self, total_notebooks=0, notebooks_with_sessions=0, workspace_name=None):
        """Finalize the consolidated file with final statistics"""
        try:
            if os.path.exists(self.consolidated_file):
                with open(self.consolidated_file, 'r') as f:
                    data = json.load(f)
                
                data["metadata"].update({
                    "total_notebooks_processed": total_notebooks,
                    "notebooks_with_sessions": notebooks_with_sessions,
                    "consolidation_completed": datetime.now().isoformat()
                })
                
                # Update workspace_name if provided
                if workspace_name:
                    data["metadata"]["workspace_name"] = workspace_name
                
                with open(self.consolidated_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                print(f"+ Finalized consolidated file: {self.consolidated_file}")
                print(f"+ Final stats: {len(data['log_summaries'])} sessions from {notebooks_with_sessions} notebooks")
                return self.consolidated_file
        except Exception as e:
            print(f"❌ Failed to finalize consolidated file: {e}")
        
        return None