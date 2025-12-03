
#!/bin/bash

# Fabric CLI Workspace Management Module
# Handles workspace creation and management operations

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the logging functions
source "$SCRIPT_DIR/../utils/logfns.sh"

# Function to create or verify workspace exists
create_workspace() {
    local ws_name="$1"
    local capacity_name="$2"
    
    # Validate required parameters
    if [[ -z "$ws_name" || -z "$capacity_name" ]]; then
        log_error "Missing required parameters for workspace creation"
        log_info "Usage: create_workspace <workspace_name> <capacity_name>"
        return 1
    fi
    
    log_info "Processing workspace: '$ws_name' with capacity: '$capacity_name'"
    
    # Check if workspace exists
    log_info "Checking if workspace '$ws_name' exists..."
    
    local exists_result=$(fab exists "$ws_name.Workspace" 2>/dev/null)
    if [[ "$exists_result" == "true" ]]; then
        log_info "Workspace '$ws_name' already exists. Skipping creation."
        return 0
    else
        log_info "Creating workspace '$ws_name' with capacity '$capacity_name'..."
        
        # Create a workspace using the specified capacity
        if fab mkdir "$ws_name.Workspace" -P "capacityname=$capacity_name"; then
            log_success "Workspace '$ws_name' created successfully"
            return 0
        else
            log_error "Failed to create workspace '$ws_name'"
            return 1
        fi
    fi
}

# Function to delete workspace
delete_workspace() {
    local ws_name="$1"
    
    if [[ -z "$ws_name" ]]; then
        log_error "Missing workspace name for deletion"
        log_info "Usage: delete_workspace <workspace_name>"
        return 1
    fi
    
    log_info "Deleting workspace: '$ws_name'"
    
    local exists_result=$(fab exists "$ws_name.Workspace" 2>/dev/null)
    if [[ "$exists_result" == "true" ]]; then
        if fab rm "$ws_name.Workspace" --force; then
            log_success "Workspace '$ws_name' deleted successfully"
            return 0
        else
            log_error "Failed to delete workspace '$ws_name'"
            return 1
        fi
    else
        log_warning "Workspace '$ws_name' does not exist"
        return 0
    fi
}

# Function to list all workspaces
list_workspaces() {
    log_info "Listing all workspaces..."
    fab ls
}
# Display usage information
usage() {
    echo "Usage: $0 <action> [parameters]"
    echo
    echo "Actions:"
    echo "  create <workspace_name> <capacity_name>  - Create workspace with specified capacity"
    echo "  delete <workspace_name>                  - Delete workspace"
    echo "  list                                     - List all workspaces"
    echo
    echo "Examples:"
    echo "  $0 create MyWorkspace MyCapacity"
    echo "  $0 delete MyWorkspace"
    echo "  $0 list"
}


# Main workspace management function
manage_workspace() {
    local action="$1"
    local ws_name="$2"
    local capacity_name="$3"
    
    case "$action" in
        "create")
            create_workspace "$ws_name" "$capacity_name"
            ;;
        "delete")
            delete_workspace "$ws_name"
            ;;
        "list")
            list_workspaces
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
    manage_workspace "$@"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi