#!/bin/bash

# This is for importing notebooks into Fabric workspaces from a local directory
# It also supports exporting notebooks to a local directory
# It assumes that the workspace and lakehouse already exist

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the logging functions
source "$SCRIPT_DIR/../utils/logfns.sh"

# Import notebook
# fab import "$workspace_name.Workspace/$notebook_name.Notebook" -i $NOTEBOOK_DIR -f

import_notebook() {
    local workspace_name="$1"
    local notebook_name="$2"
    local notebook_dir="$3"
    local lakehouse_name="$4"

    log_info "Importing notebook '$notebook_name' into workspace '$workspace_name' from directory '$notebook_dir'"

    # Import the notebook
    fab import "$workspace_name.Workspace/$notebook_name.Notebook" -i "$notebook_dir" -f

    if [ $? -eq 0 ]; then
        log_success "Notebook '$notebook_name' imported successfully"
        # Get Ids
        lakehouse_id=$(fab get "$workspace_name.Workspace/$lakehouse_name.Lakehouse" -q id 2>/dev/null)
        workspace_id=$(fab get "$workspace_name.Workspace" -q id 2>/dev/null)

        # Set the lakehouse association
        fab set "$workspace_name.Workspace/$notebook_name.Notebook" -q lakehouse -i "{\"known_lakehouses\": [{\"id\": \"$lakehouse_id\"}],\"default_lakehouse\": \"$lakehouse_id\", \"default_lakehouse_name\": \"$lakehouse_name\",\"default_lakehouse_workspace_id\": \"$workspace_id\"}" -f
        
        if [ $? -eq 0 ]; then
            log_success "Default Lakehouse set successfully for notebook '$notebook_name'"
        else
            log_error "Failed to set lakehouse association for notebook '$notebook_name'"
            return 1
        fi

        return 0
    else
        log_error "Failed to import notebook '$notebook_name'"
        return 1
    fi
}

export_notebook() {
    local workspace_name="$1"
    local notebook_name="$2"
    local output_dir="$3"

    log_info "Exporting notebook '$notebook_name' from workspace '$workspace_name' to directory '$output_dir'"

    # Export the notebook
    fab export "$workspace_name.Workspace/$notebook_name.Notebook" -o "$output_dir" -f

    if [ $? -eq 0 ]; then
        log_success "Notebook '$notebook_name' exported successfully to '$output_dir'"
        return 0
    else
        log_error "Failed to export notebook '$notebook_name'"
        return 1
    fi
}

# Display usage information
usage() {
    echo "Usage: $0 <action> [parameters]"
    echo
    echo "Actions:"
    echo "  import notebooks from local directory to workspace"
    echo "  export notebooks from workspace to local directory"
    echo
    echo "Examples:"
    echo "  $0 import MyWorkspace MyNotebook /path/to/notebook/dir MyLakehouse"
    echo "  $0 export MyWorkspace MyNotebook /path/to/output/dir"

}

# Main notebook management function
manage_notebooks() {
    local action="$1"
    local workspace_name="$2"
    local notebook_name="$3"
    local directory="$4"
    local lakehouse_name="$5"

    case "$action" in
        "import")
            import_notebook "$workspace_name" "$notebook_name" "$directory" "$lakehouse_name"
            ;;
        "export")
            export_notebook "$workspace_name" "$notebook_name" "$directory"
            ;;
        *)
            log_error "Unknown action: $action"
            log_info "Supported actions: import, export"
            return 1
            ;;
    esac
}

# Main script logic
main() {
    manage_notebooks "$@"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi