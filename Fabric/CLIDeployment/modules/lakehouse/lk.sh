
#!/bin/bash

# Fabric CLI Lakehouse Management Module
# Handles lakehouse creation and management operations

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the logging functions
source "$SCRIPT_DIR/../utils/logfns.sh"

# Function to create or verify lakehouse exists
create_lakehouse() {
    local lakehouse_name="$1"
    local workspace_name="$2"
    local enableSchemas="$3"
    
    # Validate required parameters
    if [[ -z "$lakehouse_name" || -z "$workspace_name" ]]; then
        log_error "Missing required parameters for lakehouse creation"
        log_info "Usage: create_lakehouse <lakehouse_name> <workspace_name>"
        return 1
    fi

    log_info "Processing lakehouse: '$lakehouse_name' in workspace: '$workspace_name'"
    # Check if lakehouse exists
    log_info "Checking if lakehouse '$lakehouse_name' exists..."

    local exists_result=$(fab exists "$workspace_name.Workspace/$lakehouse_name.Lakehouse" 2>/dev/null)
    if [[ "$exists_result" == "true" ]]; then
        log_info "Lakehouse '$lakehouse_name' already exists. Skipping creation."
        return 0
    else
        log_info "Creating lakehouse '$lakehouse_name' in workspace '$workspace_name'..."
        
        # Create a lakehouse using the specified workspace
        if fab create "$workspace_name.Workspace/$lakehouse_name.Lakehouse" -P enableSchemas="$enableSchemas"; then
            log_success "Lakehouse '$lakehouse_name' created successfully"
            return 0
        else
            log_error "Failed to create lakehouse '$lakehouse_name'"
            return 1
        fi
    fi
}

# Function to delete lakehouse
delete_lakehouse() {
    local lakehouse_name="$1"
    local workspace_name="$2"

    if [[ -z "$lakehouse_name" || -z "$workspace_name" ]]; then
        log_error "Missing required parameters for lakehouse deletion"
        log_info "Usage: delete_lakehouse <lakehouse_name> <workspace_name>"
        return 1
    fi

    log_info "Deleting lakehouse: '$lakehouse_name'"

    local exists_result=$(fab exists "$workspace_name.Workspace/$lakehouse_name.Lakehouse" 2>/dev/null)
    if [[ "$exists_result" == "true" ]]; then
        if fab rm "$workspace_name.Workspace/$lakehouse_name.Lakehouse" --force; then
            log_success "Lakehouse '$lakehouse_name' deleted successfully"
            return 0
        else
            log_error "Failed to delete lakehouse '$lakehouse_name'"
            return 1
        fi
    else
        log_warning "Lakehouse '$lakehouse_name' does not exist"
        return 0
    fi
}

# Display usage information
usage() {
    echo "Usage: $0 <action> [parameters]"
    echo
    echo "Actions:"
    echo "  create <workspace_name> <capacity_name>  - Create workspace with specified capacity"
    echo "  delete <workspace_name>                  - Delete workspace"
    echo "  list                                     - List all lakehouses"
    echo
    echo "Examples:"
    echo "  $0 create Lakehouse1 MyWorkspace"
    echo "  $0 delete Lakehouse1 MyWorkspace"
}

# Main lakehouse management function
manage_lakehouse() {
    local action="$1"
    local lakehouse_name="$2"
    local workspace_name="$3"
    local enableSchemas="${4:-true}"
    
    case "$action" in
        "create")
            create_lakehouse "$lakehouse_name" "$workspace_name" "$enableSchemas"
            ;;
        "delete")
            delete_lakehouse "$lakehouse_name" "$workspace_name"
            ;;
        *)
            log_error "Unknown action: $action"
            log_info "Supported actions: create, delete, info, list"
            return 1
            ;;
    esac
}

# Main script logic
main() {
    manage_lakehouse "$@"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi