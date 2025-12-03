#!/bin/bash

# Fabric CLI Deployment Script
# Uses the authentication module to login and deploy Fabric resources

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# echo "Script Directory: $SCRIPT_DIR"
#Get the base directory (assuming this script is in Fabric/CLIDeployment/)
BASE_DIR="$(cd "$(dirname "$SCRIPT_DIR")/" && pwd)"
# echo "Base Directory: $BASE_DIR"
# Source modules
modules=("$SCRIPT_DIR/modules/workspace/ws.sh" "$SCRIPT_DIR/modules/authentication/auth.sh" "$SCRIPT_DIR/modules/lakehouse/lk.sh" \
         "$SCRIPT_DIR/modules/warehouse/wh.sh" "$SCRIPT_DIR/modules/warehouse/whTables.sh" "$SCRIPT_DIR/modules/notebook/nb.sh")

for module in "${modules[@]}"; 
    do source "$module"
done

# Main deployment function
deploy_fabric() {
    ## Variables
    local source_workspace="$1"
    local workspace_name="$2"
    local capacity_name="$3"
    local lakehouse_name="$4"
    local warehouse_name="$5"
    local notebook_name="$6"
    local auth_method="$7"

    # Directory for Tables DDL files in a workspace
    TABLES_DIR="$BASE_DIR/Workspaces/$source_workspace/$warehouse_name.Warehouse/dbo/Tables/"
    # Directory for Notebook
    NOTEBOOK_DIR="$BASE_DIR/Workspaces/$source_workspace/$notebook_name.Notebook"
    TMP_DIR="$BASE_DIR/CLIDeployment/tmp/"

    log_info "Starting Fabric CLI deployment..."
    
    # Authenticate using the auth module
    log_info "Authenticating to Fabric CLI..."
    if ! fabric_auth "$auth_method"; then
        log_error "Authentication failed. Deployment aborted."
        return 1
    fi
    
    # Create Workspace
    manage_workspace "create" "$workspace_name" "$capacity_name"
    # Create Lakehouse
    manage_lakehouse "create" "$lakehouse_name" "$workspace_name" "true"
    # Create Warehouse
    manage_warehouse "create" "$warehouse_name" "$workspace_name"
    # Create Warehouse Tables
    manage_warehouse_tables "create" "$warehouse_name" "$workspace_name" "$TABLES_DIR"
    # Import Notebook
    manage_notebooks "import" "$workspace_name" "$notebook_name" "$NOTEBOOK_DIR" "$lakehouse_name"
    # Export Notebook
    manage_notebooks "export" "$workspace_name" "$notebook_name" "$TMP_DIR"

    log_success "Deployment completed successfully"

    return 0
}

# Main script execution
manage_deployment() {
    local action=$1
    local source_workspace=${2:-"DataEngineeringWSDevCICD"}
    local workspace_name=${3:-"FabricCLI-DEDev"}
    local capacity_name=${4:-"fsku2eastus"}
    local lakehouse_name=${5:-"SilverLakehouse"}
    local warehouse_name=${6:-"GoldWarehouse"}
    local notebook_name=${7:-"SilverToGoldNotebook"}
    local auth_method=${8:-"env"}

    case "$action" in
        "deploy")
            deploy_fabric "$source_workspace" "$workspace_name" "$capacity_name" "$lakehouse_name" "$warehouse_name" "$notebook_name" "$auth_method"
            ;;
            "help"|"-h"|"--help")
                echo "Usage: $0 [action] [options]"
                echo ""
                echo "Actions:"
                echo "  deploy              Deploy Fabric resources (default)"
                echo "  help, -h, --help    Show this help message"
                echo ""
                echo "Options (for deploy action):"
                echo "  source_workspace    Source workspace name (default: DataEngineeringWSDevCICD)"
                echo "  workspace_name      Target workspace name (default: FabricCLI-DEDev)"
                echo "  capacity_name       Capacity name (default: fsku2eastus)"
                echo "  lakehouse_name      Lakehouse name (default: SilverLakehouse)"
                echo "  warehouse_name      Warehouse name (default: GoldWarehouse)"
                echo "  notebook_name       Notebook name (default: SilverToGoldNotebook)"
                echo "  auth_method         Authentication method (default: env)"
                echo ""
                echo "Example:"
                echo "  $0 deploy DataEngineeringWSDevCICD FabricCLI-DEDev fsku2eastus"
                return 0
                ;;
        *)
            log_error "Unknown command: $action"
            log_info "Supported command: deploy"
            return 1
            ;;
    esac
}

main() {
    local action="${1:-deploy}"
    manage_deployment "$action" "${@:2}"
}
# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi