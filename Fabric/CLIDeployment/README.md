# Using the Microsoft Fabric CLI

The idea behind this project is to show how to leverage the Fabric CLI for Microsoft Fabric workspace management, exploring its advantages and limitations. I tried to make the code as functional as possible, separated into modules so that others can leverage similar functionality and understand how to approach a scalable deployment solution with the CLI.

## What This Does

Here's an example of how to run this Fabric CLI deployment:
```bash
./fabric-deploy.sh deploy DataEngineeringWSDevCICD FabricCLI-DEDev fsku2eastus SilverLakehouse GoldWarehouse SilverToGoldNotebook env
```

In this example we're creating a workspace, a lakehouse, a data warehouse with tables, importing a notebook and supporting 2 authentication methods: service principal and interactive.

**Note:** The script assumes there's a workspace directory containing workspace objects (the second parameter `DataEngineeringWSDevCICD` in the example above). This directory should contain your Fabric items like notebooks, lakehouses, etc. If you don't want to leverage a source workspace directory, you can adjust the code to ignore this parameter.

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

## Module Descriptions

### Authentication (`modules/authentication/auth.sh`)
Handles Fabric CLI authentication with two methods:
- **Service Principal**: Uses `.env` file credentials for automation
- **Interactive**: Browser-based login for development
- Accepts `env` or `interactive` as parameters

### Workspace (`modules/workspace/ws.sh`)  
Creates and manages Fabric workspaces with capacity assignment

### Lakehouse (`modules/lakehouse/lk.sh`)
Creates lakehouses with schema configuration options

### Warehouse (`modules/warehouse/`)
- **`wh.sh`**: Creates data warehouses
- **`whTables.sh`**: Executes DDL files to create tables via sqlcmd

### Utilities (`modules/utils/logfns.sh`)
Shared logging and error handling functions

## 🔧 Requirements

### System Prerequisites
- **Operating System**: Windows with Git Bash (not PowerShell compatible)
- **Git Bash**: Required for script execution environment

## Requirements for Running Locally

**Note: This is written for Git Bash and not PowerShell**

You need:

1. **Python** - Python version 3.10, 3.11, or 3.12 is installed on your machine (required for Fabric CLI)

2. **Fabric CLI** - Follow this doc for installation instructions: https://microsoft.github.io/fabric-cli/

3. **SQL Command Line Tools** - For executing SQL scripts in warehouse:
   https://learn.microsoft.com/en-us/sql/tools/sqlcmd/sqlcmd-download-install?view=sql-server-ver17&tabs=windows

You need to create a `.env` file in the CLIDeployment folder with service principal secrets, client id and tenant if you would like to use SPN to authenticate. Otherwise use interactive mode for authentication.

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
   cat > .env << EOF
    FABRIC_CLIENT_ID=your-client-id
    FABRIC_CLIENT_SECRET=your-client-secret
    FABRIC_TENANT_ID=your-tenant-id
    EOF
   ```

3. **Run Deployment**:
   ```bash
   ./fabric-deploy.sh deploy <sourceWorkspaceName> <destWorkspaceName> <CapacityName >LakehouseName> <WarehouseName> <NotebookName> env
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

## What's Great About the Fabric CLI

- **Lots of flexibility** to create items the way you want. For example, you can create code that would look at an existing workspace git repo and create code to go through each item and deploy. But it requires extra work to make this happen
- **Fast deployment** you can perform operations directly from the ternminal without switching to the Fabric UI. It also does not require many installation tools to get it running locally. 
- **Scriptable and automatable** - great for CI/CD pipelines. It integrates well with automation tools. 

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
- You're already familiar with command-line tools
- You need repeatable, scriptable deployments  
- You're doing bulk, high level operations/items (creating multiple workspaces, lakehouses)
- You want to integrate with CI/CD pipelines easily

**Don't use the CLI when:**
- You need very detailed, granular configuration of items. You may have to leverage the API for further config 
- You need detailed error messages and troubleshooting capabilities
- You're not familiar with Fabric dependencies. You need to follow an order of deploying items to avoid dependency errors

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

## 🔧 Troubleshooting

### 🚨 **Common Issues & Solutions**

#### Permission Issues
- Verify service principal has capacity contributor permissions
- Check Fabric workspace access levels
- Validate Azure AD app registration configuration

#### CLI Installation
```bash
# Verify CLI installation
fab --version

pip install ms-fabric-cli
```

#### SQL Connection Issues  
```bash
# Test sqlcmd connectivity
sqlcmd -S "your-warehouse-connection-string" -d "warehouse_name" -G -C -Q  "SELECT 1"

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