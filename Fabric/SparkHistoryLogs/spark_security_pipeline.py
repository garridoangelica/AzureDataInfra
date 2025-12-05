#!/usr/bin/env python3
"""
Spark Security Pipeline - Combined Log Extraction and Security Analysis

This script calls getLivy.py to extract logs and then analyzeLogs.py to analyze them.

Usage:
    python spark_security_pipeline.py --workspace-id <workspace_id> --auth-method <method>
    
Example:
    python spark_security_pipeline.py --workspace-id dfeef225-5614-4404-b47a-3fbaecefac22 --auth-method cli
"""

import argparse
import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path
import glob
from console_utils import *


def extract_logs_for_workspace(workspace_id: str, auth_method: str = "cli") -> str:
    """
    Extract logs using the getLivy.py SparkLogExtractor class
    
    Returns:
        str: Path to the consolidated JSON file
    """
    print_header(f"{Emoji.FOLDER} PHASE 1: LOG EXTRACTION", 70)
    
    try:
        from getLivy import SparkLogExtractor
        
        print_process(f"Starting log extraction...")
        print(f"  {Colors.BRIGHT_CYAN}▶{Colors.RESET} Workspace ID: {highlight(workspace_id)}")
        print(f"  {Colors.BRIGHT_CYAN}▶{Colors.RESET} Auth method: {highlight(auth_method)}")
        
        # Use the SparkLogExtractor class
        extractor = SparkLogExtractor(workspace_id, auth_method)
        consolidated_file_path = extractor.extract_all_logs()
        
        if consolidated_file_path:
            print_success(f"Log extraction completed!")
            print(f"  {Colors.BRIGHT_GREEN}▶{Colors.RESET} Consolidated file: {highlight(os.path.basename(consolidated_file_path))}")
            return consolidated_file_path
        else:
            print_error(f"Log extraction failed - no consolidated file created")
            return None
                
    except Exception as e:
        print_error(f"Log extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_logs_from_file(consolidated_file_path: str, external_only: bool = False, export_summary: str = None) -> bool:
    """
    Analyze logs using analyzeLogs.py via subprocess
    
    Args:
        consolidated_file_path: Path to consolidated JSON file
        
    Returns:
        bool: True if analysis completed successfully
    """
    print_header(f"{Emoji.SHIELD} PHASE 2: SECURITY ANALYSIS", 70)
    
    if not consolidated_file_path or not os.path.exists(consolidated_file_path):
        print_error("No consolidated file available for analysis")
        return False
    
    try:
        print_process(f"Running security analysis on: {highlight(os.path.basename(consolidated_file_path))}")
        
        # Generate timestamp for reports
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)
        
        # Prepare command arguments
        cmd_args = [sys.executable, "analyzeLogs.py", consolidated_file_path]
        
        if external_only:
            cmd_args.append("--external-only")
            
        if export_summary:
            # If export_summary doesn't include a path, put it in output folder
            if not os.path.dirname(export_summary):
                export_summary = os.path.join("output", export_summary)
            cmd_args.extend(["--export-summary", export_summary])
        elif external_only:
            # Default external report if external-only is specified but no export file given
            external_report_file = os.path.join("output", f"pipeline_external_report_{timestamp}.txt")
            cmd_args.extend(["--export-summary", external_report_file])
        
        print(f"  > Running analysis with command: {' '.join(cmd_args[2:])}")
        result = subprocess.run(cmd_args, capture_output=True, text=True, cwd=os.getcwd())
        
        
        if result.returncode == 0:
            print_success(f"Analysis completed successfully")
            if export_summary:
                print(f"  {Colors.BRIGHT_GREEN}▶{Colors.RESET} Report exported to: {highlight(export_summary)}")
            
            # Show the analysis output
            if result.stdout:
                print("\n=== ANALYSIS RESULTS ===")
                print(result.stdout)
                
        else:
            print_error(f"Analysis failed: {result.stderr}")
            if result.stdout:
                print("Output:", result.stdout)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"- Security analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_complete_pipeline(workspace_id: str, auth_method: str = "cli", external_only: bool = False, export_summary: str = None) -> bool:
    """
    Run the complete pipeline: extract logs then analyze them
    
    Returns:
        bool: True if entire pipeline completed successfully
    """
    print("*** Starting Spark Security Pipeline ***")
    print(f"  > Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  > Workspace ID: {workspace_id}")
    print(f"  > Auth Method: {auth_method}")
    
    # Phase 1: Extract logs
    consolidated_file = extract_logs_for_workspace(workspace_id, auth_method)
    if not consolidated_file:
        print("\n- Pipeline failed at log extraction phase")
        return False
    
    # Phase 2: Analyze logs  
    analysis_success = analyze_logs_from_file(consolidated_file, external_only, export_summary)
    if not analysis_success:
        print("\n- Pipeline failed at security analysis phase")
        return False
    
    print("\n" + "="*70)
    print("*** PIPELINE COMPLETED SUCCESSFULLY! ***")
    print("="*70)
    print("+ Logs extracted from all notebooks in workspace")
    print("+ Security analysis completed")
    print("+ Reports generated")
    print(f"  > Working directory: {os.getcwd()}")
    print(f"  > Consolidated logs: {consolidated_file}")
    
    return True


def main():
    """Main function to handle command line arguments and run the pipeline"""
    parser = argparse.ArgumentParser(
        description="Spark Security Pipeline - Extract logs and analyze for security concerns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    *** python spark_security_pipeline.py --workspace-id dfeef225-5614-4404-b47a-3fbaecefac22 --auth-method cli
    python spark_security_pipeline.py --workspace-id dfeef225-5614-4404-b47a-3fbaecefac22 --auth-method interactive
    
    # Full pipeline with external-only analysis and export summary
    python spark_security_pipeline.py --workspace-id dfeef225-5614-4404-b47a-3fbaecefac22 --auth-method cli --external-only --export-summary external_only_summary.txt

    # Full pipeline with just external-only (auto-generates timestamped report)
    python spark_security_pipeline.py --workspace-id dfeef225-5614-4404-b47a-3fbaecefac22 --auth-method cli --external-only

    # Full pipeline with custom export file (includes all connections, not just external)
    python spark_security_pipeline.py --workspace-id dfeef225-5614-4404-b47a-3fbaecefac22 --auth-method cli --export-summary full_analysis_report.txt

    # Analyze existing file with external-only and custom export
    python spark_security_pipeline.py --analyze-only consolidated_spark_logs_20251204_184606.json --external-only --export-summary external_only_summary.txt

    # Extract logs only
    python spark_security_pipeline.py --workspace-id dfeef225-5614-4404-b47a-3fbaecefac22 --auth-method cli --extract-only
        """
    )
    
    parser.add_argument(
        '--workspace-id', 
        required=True,
        help='Microsoft Fabric workspace ID'
    )
    
    parser.add_argument(
        '--auth-method',
        choices=['cli', 'interactive', 'service_principal'],
        default='cli',
        help='Authentication method: cli (Azure CLI), interactive (browser), service_principal (default: cli)'
    )
    
    parser.add_argument(
        '--extract-only',
        action='store_true',
        help='Only extract logs, skip analysis'
    )
    
    parser.add_argument(
        '--analyze-only',
        metavar='CONSOLIDATED_FILE',
        help='Only analyze logs from existing consolidated file'
    )
    parser.add_argument(
        '--external-only',
        action='store_true',
        help='Show only sessions with EXTERNAL connections (excludes trusted domains)'
    )
    parser.add_argument(
        '--export-summary',
        help='Export summary to text file'
    )
    
    args = parser.parse_args()
    
    # Validate workspace ID format (basic UUID check)
    if len(args.workspace_id) != 36 or args.workspace_id.count('-') != 4:
        print("❌ Invalid workspace ID format. Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        sys.exit(1)
    
    try:
        if args.analyze_only:
            # Only run analysis on existing file
            print(f"* Analyzing existing consolidated file: {args.analyze_only}")
            success = analyze_logs_from_file(args.analyze_only, args.external_only, args.export_summary)
        elif args.extract_only:
            # Only extract logs
            print(f"* Extracting logs only for workspace: {args.workspace_id}")
            consolidated_file = extract_logs_for_workspace(args.workspace_id, args.auth_method)
            success = consolidated_file is not None
            if success:
                print(f"+ Logs extracted to: {consolidated_file}")
        else:
            # Run full pipeline
            success = run_complete_pipeline(args.workspace_id, args.auth_method, args.external_only, args.export_summary)
        
        if success:
            print("\n*** Operation completed successfully! ***")
            sys.exit(0)
        else:
            print("\n- Operation failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n! Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n- Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()