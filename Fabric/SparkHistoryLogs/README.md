# Spark Security Pipeline for Microsoft Fabric

A comprehensive tool for extracting and analyzing Spark session logs from Microsoft Fabric workspaces to identify security concerns, external connections, and potential data exfiltration risks.

## 📋 Project Overview

This project provides a unified pipeline that:
1. **Extracts** Spark session logs (Livy, stdout, stderr) from Microsoft Fabric notebooks
2. **Analyzes** logs for security concerns including:
   - External network connections (non-Microsoft services)
   - Pip package installations
   - Logging configuration changes
   - Potential data exfiltration patterns
3. **Generates** detailed security reports with actionable insights

The system distinguishes between trusted Microsoft Fabric/Azure services and truly external connections, helping security teams focus on genuine risks.

## 🔧 Prerequisites

### System Requirements
- **Python 3.7+** installed on your system
- **Azure CLI** installed and configured
- **Windows PowerShell** or **Bash** terminal support

### Microsoft Fabric Access
You must have **one of the following roles** in the target workspace:
- **Admin** - Full access to workspace and all notebooks
- **Member** - Can access notebooks they own or have been shared with
- **Contributor** - Can view and run notebooks
- **Viewer** - Read-only access (may have limited log access)

### Python Dependencies
Install required packages:
```bash
pip install requests azure-identity azure-cli pathlib
```

### Azure Authentication

**Option 1: Azure CLI (Recommended for development)**
Ensure you're authenticated with Azure CLI:
```bash
az login
```

**Option 2: Web Interactive (No Azure CLI required)**
Use browser-based authentication - no Azure CLI installation needed:
- The tool will open your default browser for authentication
- Sign in with your Microsoft Fabric account
- Perfect for users who don't want to install Azure CLI

**Option 3: Service Principal (Recommended for automation)**
Create a `.env` file in the project directory with your service principal credentials:
```env
FABRICSPN_CLIENTID="your-service-principal-client-id"
FABRICSPN_SECRET="your-service-principal-client-secret"
FABRICSPN_TENANTID="your-azure-tenant-id"
```

## 🚀 Quick Start Guide

### Running the Complete Security Pipeline

For new users, the easiest way to get started is with the main security pipeline:

**Using Azure CLI:**
```bash
python spark_security_pipeline.py --workspace-id YOUR-WORKSPACE-ID --auth-method cli --external-only --export-summary security_report.txt
```

**Using Web Interactive (No Azure CLI needed):**
```bash
python spark_security_pipeline.py --workspace-id YOUR-WORKSPACE-ID --auth-method web --external-only --export-summary security_report.txt
```

**Using Service Principal:**
```bash
python spark_security_pipeline.py --workspace-id YOUR-WORKSPACE-ID --auth-method spn --external-only --export-summary security_report.txt
```

**Required Parameters:**
- `--workspace-id`: Your Microsoft Fabric workspace ID (GUID format)
- `--auth-method`: Authentication method (`cli` for Azure CLI, `web` for browser login, `spn` for Service Principal)

**Optional Parameters:**
- `--external-only`: Only show sessions with external connections (recommended for security focus)
- `--export-summary`: Export results to a text file

### Finding Your Workspace ID

1. Go to your Microsoft Fabric workspace in the browser
2. Look at the URL: `https://app.fabric.microsoft.com/groups/YOUR-WORKSPACE-ID/...`
3. Copy the GUID between `/groups/` and the next `/`

## 📁 Project Structure

```
SparkHistoryNew/
├── spark_security_pipeline.py    # Main unified pipeline
├── getLivy.py                   # Log extraction module
├── analyzeLogs.py                # Security analysis module
├── livyconn.py                   # Fabric API connector
├── fabric_auth.py                # Authentication handler
├── .env                          # Service principal credentials
├── output/                       # Generated output files
│   ├── consolidated_spark_logs_*.json
│   └── security_reports_*.txt
└── README.md                     # This file
```

## 🔍 Usage Options

### Option 1: Complete Pipeline (Recommended)
Extracts logs and runs security analysis in one command:
```bash
# Using Azure CLI
python spark_security_pipeline.py --workspace-id YOUR-WORKSPACE-ID --auth-method cli --external-only --export-summary report.txt

# Using Web Interactive (No Azure CLI needed)
python spark_security_pipeline.py --workspace-id YOUR-WORKSPACE-ID --auth-method web --external-only --export-summary report.txt

# Using Service Principal
python spark_security_pipeline.py --workspace-id YOUR-WORKSPACE-ID --auth-method spn --external-only --export-summary report.txt
```

### Option 2: Extract Logs Only
Just download and consolidate logs:
```bash
# Using Azure CLI
python getLivy.py --workspace-id YOUR-WORKSPACE-ID --auth-method cli

# Using Web Interactive
python getLivy.py --workspace-id YOUR-WORKSPACE-ID --auth-method web

# Using Service Principal
python getLivy.py --workspace-id YOUR-WORKSPACE-ID --auth-method spn
```

### Option 3: Analyze Existing Logs
Analyze previously extracted logs:
```bash
# The tool automatically looks for files in the output folder
python analyzeLogs.py --external-only --export-summary analysis.txt

# Or specify the full path
python analyzeLogs.py output/consolidated_spark_logs_YYYYMMDD_HHMMSS.json --external-only --export-summary analysis.txt
```

## 📊 Output Files

All output files are automatically saved to the `output/` folder for better organization.

### Consolidated Logs
- **File**: `output/consolidated_spark_logs_YYYYMMDD_HHMMSS.json`
- **Contains**: All session metadata, file paths, and download information
- **Use**: Input for security analysis or future processing

### Security Reports
- **File**: `output/your-report-name.txt` (e.g., `output/security_report.txt`)
- **Contains**: 
  - Sessions with external connections
  - Trusted vs external domain classifications
  - Pip installation activities
  - Logging configuration changes

### Temporary Log Files
- **Location**: System temp directory (`C:\Users\USERNAME\AppData\Local\Temp\` on Windows)
- **Structure**: `spark_logs_LIVY-ID_RANDOM/`
  - `livy_logs.txt` - Livy session logs
  - `driver_stdout.log` - Standard output
  - `driver_stderr.log` - Error logs
  - `log_summary.json` - Session metadata

## 🛡️ Security Features

### Trusted Domain Filtering
The system automatically filters out connections to known Microsoft services:
- `api.fabric.microsoft.com`
- `*.notebook.windows.net`
- `onelake.dfs.fabric.microsoft.com`
- `storage.azure.com`
- `pbidedicated.windows.net`
- And 14+ other Microsoft service patterns

### External Connection Detection
Identifies potentially risky connections to:
- Public package repositories (PyPI, conda)
- Unknown web services
- External APIs and databases
- File sharing services

### Package Installation Monitoring
Tracks pip/conda commands that could indicate:
- Unauthorized package installations
- Potential malware or backdoors
- Policy violations

## 🔧 Advanced Configuration

### Authentication Methods
Currently supports:
- `cli` - Azure CLI credentials (recommended for development with Azure CLI installed)
- `web` - Interactive browser authentication (recommended for users without Azure CLI)
- `spn` - Service Principal authentication (recommended for automation/CI/CD)
- Future: Managed identity

### Analysis Modes
- `--external-only` - Focus on external connections only
- Default mode - Show all connections with trust classification

### Export Options
- `--export-summary` - Text file with executive summary
- Console output - Detailed analysis with visual formatting

## 🚨 Troubleshooting

### Common Issues

**1. "Access Denied" or "Unauthorized"**
- Verify you have appropriate workspace permissions
- **For Azure CLI**: Run `az account show` to confirm correct Azure account, try `az login --force-refresh`
- **For Web Interactive**: Ensure you're signing in with the correct Microsoft account that has Fabric access
- **For Service Principal**: Verify `.env` file exists with correct credentials, ensure SPN has Fabric workspace permissions

**2. "Workspace not found"**
- Double-check the workspace ID format (should be a GUID)
- Ensure the workspace exists and you have access
- Verify you're in the correct Azure tenant

**3. "No sessions found"**
- Confirm notebooks have been run recently
- Some sessions may be in different states (check without filters)
- Verify notebook permissions

**4. "Unicode encoding errors"**
- Ensure your terminal supports UTF-8 encoding
- On Windows, try running from PowerShell instead of Command Prompt

### Debug Mode
For detailed troubleshooting, check the console output for:
- Authentication token status
- API response codes
- File download progress
- Session processing details

## 📈 Example Scenarios

### Scenario 1: Security Audit (Interactive - Azure CLI)
```bash
# Extract and analyze all logs, export security summary
python spark_security_pipeline.py --workspace-id abc123... --auth-method cli --external-only --export-summary security_audit.txt
```

### Scenario 1b: Security Audit (Interactive - Browser)
```bash
# Same as above but using browser authentication (no Azure CLI needed)
python spark_security_pipeline.py --workspace-id abc123... --auth-method web --external-only --export-summary security_audit.txt
```

### Scenario 2: Development Monitoring
```bash
# Get all logs for development workspace
python getLivy.py --workspace-id dev456... --auth-method cli

# Later analyze for any issues
python analyzeLogs.py consolidated_spark_logs_20251204_143022.json
```

### Scenario 3: Automated Compliance Check (CI/CD)
```bash
# Using service principal for automated security scanning
python spark_security_pipeline.py --workspace-id prod789... --auth-method spn --external-only --export-summary compliance_report.txt
```

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify all prerequisites are met
3. Review console output for specific error messages
4. Ensure workspace permissions are correct

## 📝 Notes

- The tool processes **all notebooks** in the specified workspace
- Temporary files are automatically cleaned up after processing
- Reports focus on actionable security insights
- All connections to Microsoft Fabric services are filtered out by default
- Historical session data is preserved in consolidated JSON files

---

**Happy analyzing! 🔍**