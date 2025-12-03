# Using the Microsoft Fabric CLI

The idea behind this project is to show how to leverage the Fabric CLI for Microsoft Fabric workspace management, exploring its advantages and limitations. I tried to make the code as functional as possible, separated into modules so that others can leverage similar functionality and understand how to approach a scalable deployment solution with the CLI.

## What This Does

Here's an example of how to run this Fabric CLI deployment:
```bash
./fabric-deploy.sh deploy DataEngineeringWSDevCICD FabricCLI-DEDev fsku2eastus SilverLakehouse GoldWarehouse SilverToGoldNotebook env
```

In this example we're creating a workspace, a lakehouse, a data warehouse with tables, importing a notebook and supporting 2 authentication methods: service principal and interactive.

## 🏗️ Architecture

The framework follows a modular architecture with separated concerns:

```
Fabric/CLIDeployment/
├── fabric-deploy.sh           # Main orchestration script
├── .env                       # Environment configuration
├── modules/
│   ├── authentication/        # Authentication handling
│   │   └── auth.sh
│   ├── workspace/            # Workspace management
│   │   └── ws.sh
│   ├── lakehouse/            # Lakehouse operations
│   │   └── lk.sh
│   ├── warehouse/            # Warehouse & table management
│   │   ├── wh.sh
│   │   └── whTables.sh
│   └── utils/                # Shared utilities
│       └── logfns.sh
└── Workspaces/              # Workspace definitions & artifacts
```

## 📦 Module Descriptions

### 🔐 Authentication Module (`modules/authentication/auth.sh`)
Handles multiple authentication methods for Fabric CLI:
- **Service Principal Authentication**: Automated authentication using Azure AD App Registration
- **Interactive Authentication**: Browser-based login for development scenarios
- **Environment Variable Loading**: Secure credential management via `.env` files
- **Authentication Status Checking**: Validates current login state

### 🏢 Workspace Module (`modules/workspace/ws.sh`)
Manages Fabric workspace lifecycle:
- **Workspace Creation**: Creates new workspaces with capacity assignment
- **Capacity Management**: Associates workspaces with Fabric capacities
- **Workspace Validation**: Checks workspace existence and accessibility
- **Configuration Management**: Handles workspace-specific settings

### 🏠 Lakehouse Module (`modules/lakehouse/lk.sh`)
Provides lakehouse management capabilities:
- **Lakehouse Creation**: Deploys new lakehouses with configurable settings
- **Schema Management**: Handles lakehouse schema configurations
- **Metadata Handling**: Manages lakehouse properties and dependencies

### 🏭 Warehouse Module (`modules/warehouse/`)
Comprehensive data warehouse management:
- **`wh.sh`**: Core warehouse creation and configuration
- **`whTables.sh`**: Automated table creation from DDL files
- **SQL Execution**: Direct SQL command execution via sqlcmd
- **Connection String Management**: Automated warehouse connection handling

### 🛠️ Utilities Module (`modules/utils/logfns.sh`)
Shared functionality across all modules:
- **Logging Functions**: Standardized logging with different severity levels
- **Error Handling**: Consistent error reporting and handling
- **Environment Management**: Shared environment variable functions

## 🔧 Requirements

### System Prerequisites
- **Operating System**: Windows with Git Bash (not PowerShell compatible)
- **Git Bash**: Required for script execution environment
- **Internet Connection**: Required for Fabric CLI API calls

## Requirements for Running Locally

**Note: This is written for Git Bash and not PowerShell**

You need this installed for executing SQL scripts in warehouse:
https://learn.microsoft.com/en-us/sql/tools/sqlcmd/sqlcmd-download-install?view=sql-server-ver17&tabs=windows

And the Fabric CLI - you can get it here or install via npm.

You need to create a `.env` file with service principal secrets, client id and tenant if you would like to use SPN to authenticate. Otherwise use interactive mode for authentication.

In your `.env` put the following parameters (Note: do not enclose parameters in quotes):
```
FABRIC_CLIENT_ID=<clientid>
FABRIC_CLIENT_SECRET=<secret>  
FABRIC_TENANT_ID=<tenantid>
```

### Azure Permissions
- **Service Principal**: Requires Fabric capacity contributor permissions
- **Fabric Workspace**: Admin or contributor access
- **Capacity Access**: Proper capacity permissions in Fabric Admin Portal

## 🚀 Quick Start

1. **Clone and Navigate**:
   ```bash
   cd Fabric/CLIDeployment
   ```

2. **Configure Environment**:
   ```bash
   # Create .env file with your credentials
   cp .env.example .env
   # Edit .env with your values
   ```

3. **Run Deployment**:
   ```bash
   ./fabric-deploy.sh deploy WorkspaceName CapacityName LakehouseName WarehouseName NotebookName env
   ```

4. **Authentication Options**:
   ```bash
   # Service Principal (automated)
   ./fabric-deploy.sh auth-only
   
   # Interactive login
   ./fabric-deploy.sh auth-interactive
   ```

## ✅ What's Supported

### Core Fabric Items
- ✅ **Workspaces**: Creation with capacity assignment
- ✅ **Lakehouses**: Full lifecycle management with schema support
- ✅ **Warehouses**: Creation and configuration
- ✅ **Warehouse Tables**: Automated DDL execution from SQL files
- ✅ **Notebooks**: Import with metadata preservation
- ✅ **Authentication**: Service Principal and Interactive methods

### Advanced Features
- ✅ **Modular Architecture**: Reusable, composable modules
- ✅ **Error Handling**: Comprehensive error reporting and logging
- ✅ **Configuration Management**: Environment-based configuration
- ✅ **SQL Execution**: Direct warehouse table management via sqlcmd
- ✅ **CLI API Integration**: Support for advanced API operations

## What's Great About the CLI

- **Lots of flexibility** to create items the way you want
- For example, you can create code that would look at an existing workspace git repo and create code to go through each item and deploy. But it requires extra work to make this happen
- **Fast deployment** once you get it working
- **Scriptable and automatable** - great for CI/CD pipelines

## Issues I Ran Into

**Errors are not very detailed.** For example, when trying to create a workspace with an existing capacity, the error I was getting was:
```bash
fab mkdir 'FabricCLI-DEDev'.Workspace -P capacityname=fsku2eastus
x mkdir: [NotFound] The Capacity 'fsku2eastus.Capacity' could not be found
```
This is not very descriptive. When I went to the Fabric Rest API documentation (https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/create-workspace?tabs=HTTP) it states that SPN or caller need extra permissions on capacity and Fabric tenant. After permissions to SPN were provided then I was able to continue with workspace creation. This is not a stopper per say, but it can cause a bit of delay in troubleshooting. If I were to call this command from the rest api this is the message I get: "The calling principal has no sufficient permissions over the target capacity" and error code "InsufficientPermissionsOverCapacity". To fix this I had to go to capacity settings in admin portal, select Fabric capacity and add the security group where the service principal belongs to Contributor permissions. 

**My recommendation:** leverage the Fabric Rest API docs to validate permissions/requirements for the respective CLI command and further help you with troubleshooting. At the end of the day, the CLI is a wrapper on top of the APIs for faster development.

Yet **some other errors are very direct**, like I was unable to create lakehouse because of special characters in name:
```bash
[INFO] Creating lakehouse 'FabricCLI-BronzeLK' in workspace 'FabricCLI-DEDev'...
x create: [Special characters not supported for this item type] Lakehouse name 'FabricCLI-BronzeLK' contains unsupported special characters
[ERROR] Failed to create lakehouse 'FabricCLI-BronzeLK'
```

**The CLI is used for creating higher level objects.** When trying to create a warehouse table, there wasn't an option. A workaround would be connecting directly to the SQL endpoint and executing the DDL commands. For this, you will have to obtain the connection string of the warehouse created and then leverage sqlcmd.

**Another thing I've encountered** is when importing notebooks into a workspace you need to keep in mind that you're importing all of the metadata information, meaning if a notebook has a defaulted lakehouse, environment, warehouse... You will have to change this either before import or after import. In this case, you need to do a post-processing of finding the respective ids of the lakehouses and workspaces and changing the properties of the notebook.

## When to Use the CLI vs When Not To

**Use the CLI when:**
- You want to quickly set up development/test environments
- You need repeatable, scriptable deployments  
- You're doing bulk operations (creating multiple workspaces)
- You want to integrate with CI/CD pipelines

**Don't use the CLI when:**
- You need very detailed, granular configuration of items
- You're working in production environments where you need extensive validation
- You need to create complex pipelines or dataflows with lots of activities
- You need detailed error messages and troubleshooting capabilities

## Advanced Scenarios with CLI API

Now in this case I imported a notebook but there might be scenarios where we will need to do more advanced automations. For example, you might want to create a data pipeline or an event stream with already defined activities. These type of operations can be done by leveraging the API functionality within the CLI. It allows you to do POST requests with the same authentication.

Let's say for example I have a pipeline that I would like to deploy. I would first have to convert the pipeline json definition to base64 and create a body like this:

```json
body = {
  "displayName": "DataPipeline 1",
  "description": "A data pipeline description",
  "definition": {
    "parts": [
      {
        "path": "pipeline-content.json",
        "payload": "ewogICAgInByb3***A==",
        "payloadType": "InlineBase64"
      },
      {
        "path": ".platform",
        "payload": "ZG90UGx****Jpbmc=",
        "payloadType": "InlineBase64"
      }
    ]
  }
}
```

Then you can call the Fabric CLI API function like this:
```bash
fab api workspaces
fab api workspaces/<workspaceid>/items -X post -H "content-type=application/json" -i '$body'
```

## Further Work

Some things I'd like to explore further with item definitions like creating pipelines with the CLI API functionality:

- **Pipeline deployment** using the API functions within the CLI
- **Dataflow creation** for more complex data transformation scenarios
- **Environment management** - creating and configuring Fabric environments
- **More robust error handling** and validation before deployment
- **Configuration files** to define entire workspace structures
- **Dependency management** between items (like notebooks that depend on specific lakehouses)

## 🔧 Troubleshooting

### 🚨 **Common Issues & Solutions**

#### Authentication Problems
```bash
# Check authentication status
./fabric-deploy.sh status

# Re-authenticate if needed  
./fabric-deploy.sh auth-interactive
```

#### Permission Issues
- Verify service principal has capacity contributor permissions
- Check Fabric workspace access levels
- Validate Azure AD app registration configuration

#### CLI Installation
```bash
# Verify CLI installation
fab --version

# Update to latest version
npm update -g @microsoft/fabric-cli
```

#### SQL Connection Issues  
```bash
# Test sqlcmd connectivity
sqlcmd -S "your-warehouse-connection-string" -G -Q "SELECT 1"

# Verify newer sqlcmd version
sqlcmd --version  # Should show v1.9.0 or later
```

### 📚 **Additional Resources**
- [Microsoft Fabric CLI Documentation](https://learn.microsoft.com/en-us/fabric/cicd/fabric-cli)
- [Fabric REST API Reference](https://learn.microsoft.com/en-us/rest/api/fabric/)
- [Fabric Capacity Management](https://learn.microsoft.com/en-us/fabric/enterprise/licenses)
- [Service Principal Setup Guide](https://learn.microsoft.com/en-us/fabric/security/service-principal-overview)

---

> **💡 Pro Tip**: Always test deployments in development environments first and maintain separate `.env` files for different environments to ensure secure and reliable deployments.