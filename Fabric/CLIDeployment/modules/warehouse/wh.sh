#!/bin/bash

# Fabric CLI Warehouse Management Module
# Handles warehouse creation and management operations

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the logging functions
source "$SCRIPT_DIR/../utils/logfns.sh"

# Function to create or verify warehouse exists
create_warehouse() {
    local warehouse_name="$1"
    local workspace_name="$2"
    
    # Validate required parameters
    if [[ -z "$warehouse_name" || -z "$workspace_name" ]]; then
        log_error "Missing required parameters for warehouse creation"
        log_info "Usage: create_warehouse <warehouse_name> <workspace_name>"
        return 1
    fi

    log_info "Processing warehouse: '$warehouse_name' in workspace: '$workspace_name'"
    
    # Check if warehouse exists
    log_info "Checking if warehouse '$warehouse_name' exists..."

    local exists_result=$(fab exists "$workspace_name.Workspace/$warehouse_name.Warehouse" 2>/dev/null)
    if [[ "$exists_result" == "true" ]]; then
        log_info "Warehouse '$warehouse_name' already exists. Skipping creation."
        return 0
    else
        log_info "Creating warehouse '$warehouse_name' in workspace '$workspace_name'..."
        
        # Create a warehouse using the specified workspace with enableCaseInsensitive parameter
        if fab create "$workspace_name.Workspace/$warehouse_name.Warehouse" -P enableCaseInsensitive=true ; then
            log_success "Warehouse '$warehouse_name' created successfully"
            return 0
        else
            log_error "Failed to create warehouse '$warehouse_name'"
            return 1
        fi
    fi
}

# Function to delete warehouse
delete_warehouse() {
    local warehouse_name="$1"
    local workspace_name="$2"

    if [[ -z "$warehouse_name" || -z "$workspace_name" ]]; then
        log_error "Missing required parameters for warehouse deletion"
        log_info "Usage: delete_warehouse <warehouse_name> <workspace_name>"
        return 1
    fi

    log_info "Deleting warehouse: '$warehouse_name' from workspace: '$workspace_name'"

    local exists_result=$(fab exists "$workspace_name.Workspace/$warehouse_name.Warehouse" 2>/dev/null)
    if [[ "$exists_result" == "true" ]]; then
        if fab rm "$workspace_name.Workspace/$warehouse_name.Warehouse" --force; then
            log_success "Warehouse '$warehouse_name' deleted successfully"
            return 0
        else
            log_error "Failed to delete warehouse '$warehouse_name'"
            return 1
        fi
    else
        log_warning "Warehouse '$warehouse_name' does not exist in workspace '$workspace_name'"
        return 0
    fi
}

# Display usage information
usage() {
    echo "Usage: $0 <action> [parameters]"
    echo
    echo "Actions:"
    echo "  create <warehouse_name> <workspace_name> [enableSchemas]  - Create warehouse in workspace (enableSchemas default: true)"
    echo "  delete <warehouse_name> <workspace_name>                  - Delete warehouse from workspace"
    echo
    echo "Examples:"
    echo "  $0 create MyWarehouse MyWorkspace"
    echo "  $0 delete MyWarehouse MyWorkspace"

}

# Main warehouse management function
manage_warehouse() {
    local action="$1"
    local warehouse_name="$2"
    local workspace_name="$3"
    
    case "$action" in
        "create")
            create_warehouse "$warehouse_name" "$workspace_name" "$enableSchemas"
            ;;
        "delete")
            delete_warehouse "$warehouse_name" "$workspace_name"
            ;;
        *)
            log_error "Unknown action: $action"
            log_info "Supported actions: create, delete"
            return 1
            ;;
    esac
}

# Main script logic
main() {
    manage_warehouse "$@"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi