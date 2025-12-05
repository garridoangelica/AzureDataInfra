import re
import sys
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import argparse
from pathlib import Path
from urllib.parse import urlparse
from console_utils import *


class SparkLogAnalyzer:
    """Analyzes Spark driver logs for external connection calls, pip installs, and logging status"""
    
    # Patterns to identify external connections
    CONNECTION_PATTERNS = [
        r'jdbc:.*?://([^:]+):(\d+)',  # JDBC connections
        r'https?://([^\s:]+):?(\d+)?',  # HTTP/HTTPS connections
        r'connecting to ([^\s]+):(\d+)',  # Generic connection logs
        r'established connection to ([^\s]+):(\d+)',  # Established connections
        r'remote address[:\s]+([^\s:]+):(\d+)',  # Remote address logs
        r'destination[:\s]+([^\s:]+):(\d+)',  # Destination logs
        r'target[:\s]+([^\s:]+):(\d+)',  # Target logs
        r's3[a]?://([^\s/]+)',  # S3 connections
        r'wasbs?://([^\s@]+)@([^\s.]+)',  # Azure Blob Storage
        r'gs://([^\s/]+)',  # Google Cloud Storage
        r'mongodb://([^\s:]+):?(\d+)?',  # MongoDB connections
        r'kafka[:\s]+([^\s:]+):(\d+)',  # Kafka connections
        r'ftp://([^\s:]+):?(\d+)?',  # FTP connections
        r'sftp://([^\s:]+):?(\d+)?',  # SFTP connections
        r'([a-zA-Z0-9]+)\.dfs\.core\.windows\.net',  # Azure Data Lake Storage Gen2
        r'([a-zA-Z0-9]+)\.blob\.core\.windows\.net',  # Azure Blob Storage
        r'([a-zA-Z0-9]+)\.table\.core\.windows\.net',  # Azure Table Storage
        r'([a-zA-Z0-9]+)\.queue\.core\.windows\.net',  # Azure Queue Storage
        r'abfss?://[^@]+@([^\s.]+)\.dfs\.core\.windows\.net',  # ABFS protocol
    ]
    
    # Default trusted domains/services (Microsoft Fabric/Azure internal services)
    DEFAULT_TRUSTED_DOMAINS = [
        'pbidedicated.windows.net',
        'analysis.windows.net',
        'api.fabric.microsoft.com',
        'exec.eastus.notebook.windows.net',
        'exec.westus.notebook.windows.net',
        'exec.northeurope.notebook.windows.net',
        'exec.westeurope.notebook.windows.net',
        'onelake.dfs.fabric.microsoft.com',
        'sparkui.fabric.microsoft.com',
        'storage.azure.com',
        'tokenservice1.eastus.trident.azuresynapse.net',
        'tokenservice1.westus.trident.azuresynapse.net',
        'tokenservice1.northeurope.trident.azuresynapse.net',
        'tokenservice1.westeurope.trident.azuresynapse.net',
        'operation-service',  # Internal service
        'vm-',  # Internal VM hostnames pattern
        'localhost',
        '127.0.0.1',
        '::1',
    ]
    
    # Patterns to identify pip installs
    PIP_PATTERNS = [
        r'pip install ([^\s]+)',
        r'pip3 install ([^\s]+)',
        r'python -m pip install ([^\s]+)',
        r'python3 -m pip install ([^\s]+)',
        r'Installing collected packages: ([^\n]+)',
        r'Successfully installed ([^\n]+)',
    ]
    
    # Patterns to identify logging configuration
    LOGGING_PATTERNS = [
        r'log4j|logging\.(?:disable|off|level)',
        r'rootLogger|logger\.level',
        r'spark\.sql\.adaptive\.logLevel',
        r'spark\.log\.level',
    ]
    
    def __init__(self, consolidated_file_path: str = None, trusted_domains: List[str] = None):
        self.consolidated_file_path = consolidated_file_path
        self.session_results = []  # Results for each session
        self.trusted_domains = trusted_domains or self.DEFAULT_TRUSTED_DOMAINS.copy()
        self.compiled_connection_patterns = [re.compile(pattern, re.IGNORECASE) 
                                           for pattern in self.CONNECTION_PATTERNS]
        self.compiled_pip_patterns = [re.compile(pattern, re.IGNORECASE) 
                                    for pattern in self.PIP_PATTERNS]
        self.compiled_logging_patterns = [re.compile(pattern, re.IGNORECASE) 
                                        for pattern in self.LOGGING_PATTERNS]
    
    def is_trusted_host(self, host: str) -> bool:
        """Check if a host is in the trusted domains list"""
        # Clean and extract actual hostname from the input
        actual_host = self._extract_hostname(host)
        
        if not actual_host:
            return False
        
        host_lower = actual_host.lower()
        
        # Special check for workspace-based temp storage patterns
        # This handles ABFS URLs like abfss://workspace-id@hostname.dfs.core.windows.net
        import re
        uuid_pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
        
        if '.dfs.core.windows.net' in host_lower and '@' in host_lower:
            container_part = host_lower.split('@')[0]
            hostname_part = host_lower.split('@')[-1]
            
            # Clean the container part of protocol prefixes
            clean_container = container_part.replace('abfss://', '').replace('abfs://', '')
            
            # Check if container is exactly a workspace ID pattern (UUID format: 8-4-4-4-12 characters)
            if re.match(uuid_pattern, clean_container):
                # This looks like a workspace-based temp storage, treat as trusted
                return True
                
        # Import regex at the top level to avoid repeated imports
        import re
                
        # Special pattern matching for Fabric and Azure storage identifiers
        # Handle both full hostnames and base hostnames (since CONNECTION_PATTERNS may extract just the base)
        hostname_base = host_lower
        if '.dfs.core.windows.net' in host_lower:
            hostname_base = host_lower.replace('.dfs.core.windows.net', '')
        
        # Pattern 1: spark*triprodeus hosts (like spark2triprodeus)
        if re.match(r'^spark\d+triprodeus$', hostname_base):
            return True
            
        # Pattern 2: Fabric temp storage identifiers (like olsblayjtsk9m43e910te)
        # These are typically random-looking 20-22 character alphanumeric strings
        # More restrictive pattern to avoid catching legitimate external storage accounts
        if len(hostname_base) >= 20 and re.match(r'^[a-z0-9]{20,22}$', hostname_base):
            # Additional check: should not contain obvious words (like "dev", "prod", "test", "msft")
            common_words = ['dev', 'prod', 'test', 'msft', 'east', 'west', 'central', 'stage', 'stag']
            if not any(word in hostname_base for word in common_words):
                return True
        
        for trusted_domain in self.trusted_domains:
            trusted_lower = trusted_domain.lower()
            
            # Exact match
            if host_lower == trusted_lower:
                return True
                
            # Domain suffix match (e.g., api.fabric.microsoft.com matches fabric.microsoft.com)
            if host_lower.endswith('.' + trusted_lower) or host_lower.endswith(trusted_lower):
                return True
                
            # Pattern match for VM hostnames (starts with vm-)
            if trusted_lower.endswith('-') and host_lower.startswith(trusted_lower):
                return True
        
        return False
    
    def _extract_hostname(self, host_input: str) -> str:
        """Extract the actual hostname from various input formats"""
        if not host_input:
            return ""
        
        # Remove leading/trailing whitespace and common punctuation
        host_input = host_input.strip(' ,()"\'')
        
        # If it looks like a URL, parse it
        if '://' in host_input:
            try:
                parsed = urlparse(host_input)
                return parsed.hostname or parsed.netloc.split(':')[0]
            except:
                # Fallback to manual extraction
                pass
        
        # Handle cases like "host.domain.com/path" without protocol
        if '/' in host_input:
            host_input = host_input.split('/')[0]
        
        # Handle cases like "host.domain.com?param=value"
        if '?' in host_input:
            host_input = host_input.split('?')[0]
        
        # Handle cases like "host.domain.com:port"
        if ':' in host_input and not host_input.count(':') > 1:  # Avoid IPv6
            host_input = host_input.split(':')[0]
        
        # Final cleanup - remove trailing dots and common punctuation
        host_input = host_input.strip(' ,()"\'.')
        
        return host_input
    
    def analyze_single_log_file(self, log_file_path: str) -> Dict:
        """Analyze a single log file for connections, pip installs, and logging config"""
        result = {
            'log_file': log_file_path,
            'connections': [],
            'external_connections': [],  # New: filtered external connections
            'trusted_connections': [],   # New: trusted connections
            'pip_installs': [],
            'logging_config': [],
            'file_exists': os.path.exists(log_file_path),
            'file_size': 0
        }
        
        if not result['file_exists']:
            return result
            
        try:
            result['file_size'] = os.path.getsize(log_file_path)
            
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_number, line in enumerate(f, 1):
                    # Check for connections
                    for pattern in self.compiled_connection_patterns:
                        match = pattern.search(line)
                        if match:
                            connection_info = {
                                'line_number': line_number,
                                'host': match.group(1),
                                'port': match.group(2) if len(match.groups()) > 1 else None,
                                'raw_line': line.strip(),
                                'pattern_matched': pattern.pattern
                            }
                            
                            # Add to all connections
                            result['connections'].append(connection_info)
                            
                            # Special check for workspace-based ABFS URLs before normal trusted host check
                            is_trusted = False
                            raw_line_lower = line.lower()
                            
                            # Check for ABFS URLs with workspace UUID containers
                            if 'abfs' in raw_line_lower and '@' in raw_line_lower and '.dfs.core.windows.net' in raw_line_lower:
                                import re
                                # Look for ABFS URLs in the format abfss://uuid@hostname.dfs.core.windows.net
                                abfs_pattern = r'abfss?://([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})@[a-zA-Z0-9]+\.dfs\.core\.windows\.net'
                                if re.search(abfs_pattern, raw_line_lower):
                                    is_trusted = True
                            
                            # If not already marked as trusted, check normal trusted host patterns
                            if not is_trusted:
                                is_trusted = self.is_trusted_host(connection_info['host'])
                            
                            # Categorize as trusted or external
                            if is_trusted:
                                result['trusted_connections'].append(connection_info)
                            else:
                                result['external_connections'].append(connection_info)
                    
                    # Check for pip installs
                    for pattern in self.compiled_pip_patterns:
                        match = pattern.search(line)
                        if match:
                            pip_info = {
                                'line_number': line_number,
                                'package': match.group(1),
                                'raw_line': line.strip(),
                                'pattern_matched': pattern.pattern
                            }
                            result['pip_installs'].append(pip_info)
                    
                    # Check for logging configuration
                    for pattern in self.compiled_logging_patterns:
                        match = pattern.search(line)
                        if match:
                            logging_info = {
                                'line_number': line_number,
                                'raw_line': line.strip(),
                                'pattern_matched': pattern.pattern
                            }
                            result['logging_config'].append(logging_info)
        
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    def analyze_consolidated_logs(self) -> List[Dict]:
        """Analyze all logs from consolidated JSON file"""
        if not self.consolidated_file_path:
            raise ValueError("No consolidated file path provided")
            
        print(f"Loading consolidated log file: {self.consolidated_file_path}")
        
        try:
            with open(self.consolidated_file_path, 'r') as f:
                consolidated_data = json.load(f)
        except FileNotFoundError:
            print(f"Error: Consolidated file not found: {self.consolidated_file_path}")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading consolidated file: {e}")
            sys.exit(1)
        
        log_summaries = consolidated_data.get('log_summaries', [])
        print(f"Found {len(log_summaries)} sessions to analyze")
        
        for i, session in enumerate(log_summaries):
            print(f"\n* Analyzing session {i+1}/{len(log_summaries)}")
            print(f"Notebook: {session.get('notebook_name', 'Unknown')}")
            print(f"Livy ID: {session.get('livy_id', 'Unknown')}")
            
            session_result = {
                'session_info': {
                    'notebook_name': session.get('notebook_name', 'Unknown'),
                    'notebook_id': session.get('notebook_id', 'Unknown'),
                    'workspace_name': session.get('workspace_name', 'Unknown'),
                    'workspace_id': session.get('workspace_id', 'Unknown'),
                    'spark_application_id': session.get('spark_application_id', 'Unknown'),
                    'livy_id': session.get('livy_id', 'Unknown'),
                    'app_url': session.get('app_url', 'Unknown'),
                    'temp_directory': session.get('temp_directory', 'Unknown'),
                    'download_timestamp': session.get('download_timestamp', 'Unknown')
                },
                'log_analyses': {}
            }
            
            # Analyze each log file for this session
            downloaded_files = session.get('downloaded_files', [])
            for log_file in downloaded_files:
                log_type = 'unknown'
                if 'livy_logs' in log_file:
                    log_type = 'livy'
                elif 'stdout' in log_file:
                    log_type = 'stdout'
                elif 'stderr' in log_file:
                    log_type = 'stderr'
                
                print(f"  > Analyzing {log_type}: {os.path.basename(log_file)}")
                analysis = self.analyze_single_log_file(log_file)
                session_result['log_analyses'][log_type] = analysis
            
            self.session_results.append(session_result)
        
        return self.session_results
    
    def get_sessions_with_external_connections(self) -> List[Dict]:
        """Get sessions that have truly external (non-trusted) connections"""
        sessions_with_external = []
        
        for session in self.session_results:
            has_external = False
            total_external = 0
            total_trusted = 0
            
            for log_type, analysis in session['log_analyses'].items():
                if analysis.get('external_connections'):
                    has_external = True
                    total_external += len(analysis['external_connections'])
                if analysis.get('trusted_connections'):
                    total_trusted += len(analysis['trusted_connections'])
            
            if has_external:
                session_summary = {
                    'notebook_name': session['session_info']['notebook_name'],
                    'notebook_id': session['session_info']['notebook_id'],
                    'livy_id': session['session_info']['livy_id'],
                    'workspace_name': session['session_info']['workspace_name'],
                    'app_url': session['session_info']['app_url'],
                    'total_external_connections': total_external,
                    'total_trusted_connections': total_trusted,
                    'external_connection_details': {},
                    'trusted_connection_details': {}
                }
                
                for log_type, analysis in session['log_analyses'].items():
                    if analysis.get('external_connections'):
                        session_summary['external_connection_details'][log_type] = analysis['external_connections']
                    if analysis.get('trusted_connections'):
                        session_summary['trusted_connection_details'][log_type] = analysis['trusted_connections']
                
                sessions_with_external.append(session_summary)
        
        return sessions_with_external
    
    def get_sessions_with_outbound_connections(self) -> List[Dict]:
        """Get sessions that have any outbound connections (includes both trusted and external)"""
        sessions_with_connections = []
        
        for session in self.session_results:
            has_connections = False
            total_connections = 0
            total_external = 0
            total_trusted = 0
            
            for log_type, analysis in session['log_analyses'].items():
                if analysis.get('connections'):
                    has_connections = True
                    total_connections += len(analysis['connections'])
                if analysis.get('external_connections'):
                    total_external += len(analysis['external_connections'])
                if analysis.get('trusted_connections'):
                    total_trusted += len(analysis['trusted_connections'])
            
            if has_connections:
                session_summary = {
                    'notebook_name': session['session_info']['notebook_name'],
                    'notebook_id': session['session_info']['notebook_id'],
                    'livy_id': session['session_info']['livy_id'],
                    'workspace_name': session['session_info']['workspace_name'],
                    'app_url': session['session_info']['app_url'],
                    'total_connections': total_connections,
                    'total_external_connections': total_external,
                    'total_trusted_connections': total_trusted,
                    'connection_details': {},
                    'external_connection_details': {},
                    'trusted_connection_details': {}
                }
                
                for log_type, analysis in session['log_analyses'].items():
                    if analysis.get('connections'):
                        session_summary['connection_details'][log_type] = analysis['connections']
                    if analysis.get('external_connections'):
                        session_summary['external_connection_details'][log_type] = analysis['external_connections']
                    if analysis.get('trusted_connections'):
                        session_summary['trusted_connection_details'][log_type] = analysis['trusted_connections']
                
                sessions_with_connections.append(session_summary)
        
        return sessions_with_connections
    
    def get_sessions_with_pip_installs(self) -> List[Dict]:
        """Get sessions that have pip installations"""
        sessions_with_pip = []
        
        for session in self.session_results:
            has_pip = False
            total_pip_installs = 0
            
            for log_type, analysis in session['log_analyses'].items():
                if analysis.get('pip_installs'):
                    has_pip = True
                    total_pip_installs += len(analysis['pip_installs'])
            
            if has_pip:
                session_summary = {
                    'notebook_name': session['session_info']['notebook_name'],
                    'notebook_id': session['session_info']['notebook_id'],
                    'livy_id': session['session_info']['livy_id'],
                    'workspace_name': session['session_info']['workspace_name'],
                    'total_pip_installs': total_pip_installs,
                    'pip_details': {}
                }
                
                for log_type, analysis in session['log_analyses'].items():
                    if analysis.get('pip_installs'):
                        session_summary['pip_details'][log_type] = analysis['pip_installs']
                
                sessions_with_pip.append(session_summary)
        
        return sessions_with_pip
    
    def get_logging_status_summary(self) -> Dict:
        """Get summary of logging configurations across all sessions"""
        logging_summary = {
            'sessions_with_logging_config': 0,
            'sessions_with_disabled_logs': 0,
            'details': []
        }
        
        for session in self.session_results:
            has_logging_config = False
            has_disabled_logs = False
            
            for log_type, analysis in session['log_analyses'].items():
                if analysis.get('logging_config'):
                    has_logging_config = True
                    # Check if logs are disabled
                    for log_config in analysis['logging_config']:
                        if any(keyword in log_config['raw_line'].lower() 
                               for keyword in ['disable', 'off', 'false']):
                            has_disabled_logs = True
            
            if has_logging_config:
                logging_summary['sessions_with_logging_config'] += 1
                session_detail = {
                    'notebook_name': session['session_info']['notebook_name'],
                    'livy_id': session['session_info']['livy_id'],
                    'has_disabled_logs': has_disabled_logs,
                    'logging_configs': {}
                }
                
                for log_type, analysis in session['log_analyses'].items():
                    if analysis.get('logging_config'):
                        session_detail['logging_configs'][log_type] = analysis['logging_config']
                
                logging_summary['details'].append(session_detail)
            
            if has_disabled_logs:
                logging_summary['sessions_with_disabled_logs'] += 1
        
        return logging_summary
    
    def print_comprehensive_summary(self):
        """Print comprehensive analysis summary"""
        print("\n" + "="*100)
        print("SPARK SESSION ANALYSIS - COMPREHENSIVE SUMMARY")
        print("="*100)
        
        # Overall statistics
        total_sessions = len(self.session_results)
        sessions_with_connections = self.get_sessions_with_outbound_connections()
        sessions_with_external = self.get_sessions_with_external_connections()
        sessions_with_pip = self.get_sessions_with_pip_installs()
        logging_status = self.get_logging_status_summary()
        
        print(f"\n=== OVERALL STATISTICS ===")
        print(f"   Total sessions analyzed: {total_sessions}")
        print(f"   Sessions with outbound connections (any): {len(sessions_with_connections)}")
        print(f"   Sessions with EXTERNAL connections: {len(sessions_with_external)}")
        print(f"   Sessions with pip installs: {len(sessions_with_pip)}")
        print(f"   Sessions with logging configuration: {logging_status['sessions_with_logging_config']}")
        print(f"   Sessions with disabled logs: {logging_status['sessions_with_disabled_logs']}")
        
        print(f"\n=== TRUSTED DOMAINS FILTER ===")
        print(f"   {len(self.trusted_domains)} trusted domains/patterns configured")
        print(f"   Example trusted domains: {', '.join(self.trusted_domains[:5])}...")
        
        # Sessions with EXTERNAL connections (most important)
        if sessions_with_external:
            print(f"\n!!! SESSIONS WITH EXTERNAL CONNECTIONS ({len(sessions_with_external)}) - SECURITY REVIEW NEEDED !!!")
            for session in sessions_with_external:
                print(f"   >> Notebook: {session['notebook_name']}")
                print(f"      Livy ID: {session['livy_id']}")
                print(f"   >> Workspace: {session['workspace_name']}")
                print(f"   >> External connections: {session['total_external_connections']}")
                print(f"   >> Trusted connections: {session['total_trusted_connections']}")
                print(f"   >> Monitor URL: {session['app_url']}")
                
                # Show unique EXTERNAL hosts for this session
                unique_external_hosts = set()
                for log_type, connections in session['external_connection_details'].items():
                    for conn in connections:
                        host_port = conn['host']
                        if conn.get('port'):
                            host_port += f":{conn['port']}"
                        unique_external_hosts.add(host_port)
                
                print(f"   >> External hosts: {', '.join(sorted(unique_external_hosts))}")
                print()
        else:
            print(f"\n+ EXTERNAL CONNECTIONS: No sessions found with external connections (all connections are to trusted services)")
        
        # Sessions with any connections (including trusted)
        if sessions_with_connections:
            print(f"\n{Emoji.globe} ALL OUTBOUND CONNECTIONS SUMMARY ({len(sessions_with_connections)}):")
            for session in sessions_with_connections:
                external_count = session.get('total_external_connections', 0)
                trusted_count = session.get('total_trusted_connections', 0)
                status = "! HAS EXTERNAL" if external_count > 0 else "+ TRUSTED ONLY"
                
                print(f"   > {session['notebook_name']} ({session['livy_id']}) - {status}")
                print(f"      External: {external_count}, Trusted: {trusted_count}")
        else:
            print(f"\n+ OUTBOUND CONNECTIONS: No sessions found with outbound connections")
        
        # Sessions with pip installs
        if sessions_with_pip:
            print(f"\n=== SESSIONS WITH PIP INSTALLS ({len(sessions_with_pip)}) ===")
            for session in sessions_with_pip:
                print(f"   >> {session['notebook_name']}")
                print(f"      Livy ID: {session['livy_id']}")
                print(f"      Workspace: {session['workspace_name']}")
                print(f"      Total pip installs: {session['total_pip_installs']}")
                print()
        else:
            print(f"\n+ PIP INSTALLS: No sessions found with pip installations")
        
        # Logging status
        if logging_status['details']:
            print(f"\n📋 LOGGING CONFIGURATION SUMMARY:")
            print(f"   Sessions with logging config: {logging_status['sessions_with_logging_config']}")
            print(f"   Sessions with disabled logs: {logging_status['sessions_with_disabled_logs']}")
            
            for detail in logging_status['details']:
                status = "🔴 DISABLED" if detail['has_disabled_logs'] else "🟢 ENABLED"
                print(f"   >> {detail['notebook_name']} - {status}")
                print(f"   └─ 🆔 Livy ID: {detail['livy_id']}")
        else:
            print(f"\n📋 LOGGING: No explicit logging configuration found")
    

    
    def export_to_json(self, output_file: str):
        """Export detailed results to JSON file"""
        try:
            export_data = {
                'analysis_timestamp': datetime.now().isoformat(),
                'total_sessions': len(self.session_results),
                'sessions_with_outbound_connections': self.get_sessions_with_outbound_connections(),
                'sessions_with_pip_installs': self.get_sessions_with_pip_installs(),
                'logging_status_summary': self.get_logging_status_summary(),
                'detailed_session_results': self.session_results
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            print(f"\n+ Detailed results exported to: {output_file}")
        
        except Exception as e:
            print(f"- Error exporting results: {e}")
    
    def export_summary_to_text(self, output_file: str):
        """Export summary results to text file focusing on external connections"""
        try:
            # If output file doesn't include a path, put it in output folder
            export_path = output_file
            if not os.path.dirname(export_path):
                os.makedirs("output", exist_ok=True)
                export_path = os.path.join("output", export_path)
            
            sessions_with_external = self.get_sessions_with_external_connections()
            sessions_with_all = self.get_sessions_with_outbound_connections()
            
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write("SPARK SESSION ANALYSIS - EXTERNAL CONNECTIONS SUMMARY\n")
                f.write("="*80 + "\n\n")
                
                f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Sessions Analyzed: {len(self.session_results)}\n")
                f.write(f"Sessions with ANY Outbound Connections: {len(sessions_with_all)}\n")
                f.write(f"Sessions with EXTERNAL Connections: {len(sessions_with_external)}\n")
                f.write(f"Trusted Domains Configured: {len(self.trusted_domains)}\n\n")
                
                f.write("TRUSTED DOMAINS/PATTERNS:\n")
                f.write("-" * 30 + "\n")
                for domain in sorted(self.trusted_domains):
                    f.write(f"  • {domain}\n")
                f.write("\n")
                
                if sessions_with_external:
                    f.write("!!! SESSIONS WITH EXTERNAL CONNECTIONS (SECURITY REVIEW NEEDED) !!!\n")
                    f.write("="*70 + "\n")
                    
                    for i, session in enumerate(sessions_with_external, 1):
                        f.write(f"\n{i}. Notebook: {session['notebook_name']}\n")
                        f.write(f"   Livy ID: {session['livy_id']}\n")
                        f.write(f"   Workspace: {session['workspace_name']}\n")
                        f.write(f"   External Connections: {session['total_external_connections']}\n")
                        f.write(f"   Trusted Connections: {session['total_trusted_connections']}\n")
                        f.write(f"   Monitor URL: {session['app_url']}\n")
                        
                        # List unique EXTERNAL hosts only
                        unique_external_hosts = set()
                        for log_type, connections in session['external_connection_details'].items():
                            for conn in connections:
                                host_port = conn['host']
                                if conn.get('port'):
                                    host_port += f":{conn['port']}"
                                unique_external_hosts.add(host_port)
                        
                        if unique_external_hosts:
                            f.write(f"   !!! EXTERNAL HOSTS: {', '.join(sorted(unique_external_hosts))}\n")
                        f.write(f"   {'-' * 60}\n")
                else:
                    f.write("+ NO EXTERNAL CONNECTIONS FOUND\n")
                    f.write("All detected connections are to trusted Microsoft Fabric/Azure services.\n\n")
                
                # Summary of all connections for reference
                if sessions_with_all:
                    f.write("\n=== ALL SESSIONS SUMMARY (Including Trusted) ===\n")
                    f.write("-" * 50 + "\n")
                    for session in sessions_with_all:
                        external_count = session.get('total_external_connections', 0)
                        trusted_count = session.get('total_trusted_connections', 0)
                        status = "! HAS EXTERNAL" if external_count > 0 else "+ TRUSTED ONLY"
                        f.write(f"   {session['notebook_name']} ({session['livy_id']}) - {status}\n")
                        f.write(f"      External: {external_count}, Trusted: {trusted_count}\n")
            
            print_success(f"External connections summary exported to: {highlight(export_path)}")
        
        except Exception as e:
            print(f"- Error exporting summary: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze Spark session logs for outbound connections, pip installs, and logging status'
    )
    parser.add_argument(
        'consolidated_file',
        nargs='?',
        help='Path to the consolidated spark logs JSON file',
        default=None
    )
    parser.add_argument(
        '--export-json',
        help='Export detailed results to JSON file',
        default=None
    )
    parser.add_argument(
        '--export-summary',
        help='Export summary to text file',
        default=None
    )
    parser.add_argument(
        '--external-only',
        action='store_true',
        help='Show only sessions with EXTERNAL connections (excludes trusted domains)'
    )
    parser.add_argument(
        '--connections-only',
        action='store_true',
        help='Show only sessions with ANY outbound connections (includes trusted)'
    )
    parser.add_argument(
        '--add-trusted-domain',
        action='append',
        help='Add additional trusted domain/pattern (can be used multiple times)',
        default=[]
    )
    parser.add_argument(
        '--list-trusted-domains',
        action='store_true',
        help='List all configured trusted domains and exit'
    )
    
    args = parser.parse_args()
    
    # Handle trusted domains listing
    if args.list_trusted_domains:
        analyzer = SparkLogAnalyzer()  # Create analyzer just to get default domains
        if args.add_trusted_domain:
            analyzer.trusted_domains.extend(args.add_trusted_domain)
        
        print_header(f"{Emoji.SHIELD} CONFIGURED TRUSTED DOMAINS/PATTERNS", 50)
        for i, domain in enumerate(sorted(analyzer.trusted_domains), 1):
            print(f"{i:2d}. {domain}")
        print(f"\nTotal: {len(analyzer.trusted_domains)} trusted domains/patterns")
        sys.exit(0)
    
    # Find consolidated file if not provided
    consolidated_file = args.consolidated_file
    if not consolidated_file:
        # Look for consolidated files in output directory first, then current directory
        search_dirs = ['output', '.']
        consolidated_files = []
        
        for search_dir in search_dirs:
            if os.path.exists(search_dir):
                dir_files = [f for f in os.listdir(search_dir) if f.startswith('consolidated_spark_logs_') and f.endswith('.json')]
                # Add full path to files
                consolidated_files.extend([os.path.join(search_dir, f) for f in dir_files])
        
        if consolidated_files:
            consolidated_file = sorted(consolidated_files)[-1]  # Get the most recent one
            print_info(f"Auto-detected consolidated file: {highlight(os.path.basename(consolidated_file))}")
        else:
            print_error("No consolidated file found. Please specify the path or run your log collection script first.")
            print_info("Expected file pattern: consolidated_spark_logs_YYYYMMDD_HHMMSS.json")
            print_info("Looking in: output/ and current directory")
            sys.exit(1)
    
    # Create analyzer with additional trusted domains if specified
    additional_trusted = args.add_trusted_domain or []
    analyzer = SparkLogAnalyzer(consolidated_file)
    if additional_trusted:
        analyzer.trusted_domains.extend(additional_trusted)
        print(f"+ Added {len(additional_trusted)} additional trusted domains")
    
    print_header(f"{Emoji.MAGNIFY} COMPREHENSIVE SPARK SESSION ANALYSIS {Emoji.SHIELD}", 70)
    analyzer.analyze_consolidated_logs()
    
    # Print results based on user preference
    if args.external_only:
        sessions_with_external = analyzer.get_sessions_with_external_connections()
        print(f"\n!!! SESSIONS WITH EXTERNAL CONNECTIONS ({len(sessions_with_external)}) !!!")
        
        if sessions_with_external:
            for session in sessions_with_external:
                print(f"> {session['notebook_name']} (Livy ID: {session['livy_id']})")
                print(f"   Workspace: {session['workspace_name']}")
                print(f"   External: {session['total_external_connections']}, Trusted: {session['total_trusted_connections']}")
                print(f"   Monitor: {session['app_url']}")
                
                # Show external hosts
                unique_external_hosts = set()
                for log_type, connections in session['external_connection_details'].items():
                    for conn in connections:
                        host_port = conn['host']
                        if conn.get('port'):
                            host_port += f":{conn['port']}"
                        unique_external_hosts.add(host_port)
                
                if unique_external_hosts:
                    print(f"   {Emoji.TARGET} External hosts: {', '.join(sorted(unique_external_hosts))}")
                print()
        else:
            print(f"+ No sessions found with external connections (all connections are to trusted services)")
    
    elif args.connections_only:
        sessions_with_connections = analyzer.get_sessions_with_outbound_connections()
        print(f"\n{Emoji.globe} SESSIONS WITH ANY OUTBOUND CONNECTIONS ({len(sessions_with_connections)}):")
        
        if sessions_with_connections:
            for session in sessions_with_connections:
                external_count = session.get('total_external_connections', 0)
                trusted_count = session.get('total_trusted_connections', 0)
                status = f"{Emoji.warning} HAS EXTERNAL" if external_count > 0 else f"{Emoji.check_mark} TRUSTED ONLY"
                
                print(f"📒 {session['notebook_name']} (Livy ID: {session['livy_id']}) - {status}")
                print(f"   🏢 Workspace: {session['workspace_name']}")
                print(f"   {Emoji.warning} External: {external_count}, {Emoji.check_mark} Trusted: {trusted_count}")
                print(f"   🖥️  Monitor: {session['app_url']}")
                print()
        else:
            print("✅ No sessions found with outbound connections")
    else:
        analyzer.print_comprehensive_summary()
    
    # Export if requested
    if args.export_json:
        analyzer.export_to_json(args.export_json)
    
    if args.export_summary:
        analyzer.export_summary_to_text(args.export_summary)


if __name__ == '__main__':
    main()
 