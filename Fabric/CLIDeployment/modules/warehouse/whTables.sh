#!/bin/bash
# Fabric CLI Warehouse Tables Management Module
# Handles creation of tables in a specified warehouse

# Get the directory of this script
# Requirements Microsoft ODBC Driver 18 for SQL Server and sqlcmd tool installed
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the logging functions
source "$SCRIPT_DIR/../utils/logfns.sh"

## Create tables in warehouse from DDL files
create_wh_tables() {
    local warehouse_name="$1"
    local workspace_name="$2"
    local ddl_folder_path="$3"

	# Validate required parameters
    if [[ -z "$warehouse_name" || -z "$workspace_name" || -z "$ddl_folder_path" ]]; then
        echo "Usage: create_wh_tables <warehouse_name> <workspace_name> <ddl_folder_path>"
        return 1
    fi

	# Get Warehouse connection details
	log_info "Retrieving connection details for warehouse '$warehouse_name' in workspace '$workspace_name'"
	connection_string=$(fab get "$workspace_name.Workspace/$warehouse_name.Warehouse" -q properties.connectionString 2>/dev/null)
	
	echo $ddl_folder_path
	# Process each .sql file in the directory
	for sql_file in "$ddl_folder_path"/*.sql; do
		echo "Processing file: $(basename "$sql_file")"
		if [[ -f "$sql_file" ]]; then
			echo "Executing SQL file: $(basename "$sql_file")"
			
			# Read the SQL query from the file
			query=$(cat "$sql_file")
			# echo "SQL Query: $query"
			# echo "Connection String: $connection_string"
			# Execute the query
			output=$(sqlcmd -S "$connection_string" -d "$warehouse_name" -G -C -Q "$query" 2>/dev/null)
			
			if [[ $? -eq 0 ]]; then
				log_success "✓ Successfully executed: $(basename "$sql_file")"
				log_info "SQL execution output: $output"
			else
				log_error "✗ Failed to execute: $(basename "$sql_file")"
				log_error "SQL execution failed: $output"
				exit 1
			fi
			echo ""
		fi
	done
}

# Display usage information
usage() {
    echo "Usage: $0 <action> [parameters]"
    echo
    echo "Actions:"
    echo "  create warehouse tables"
    echo
    echo "Examples:"
    echo "  $0 create MyWarehouse MyWorkspace /path/to/ddl/files"

}

# Main warehouse management function
manage_warehouse_tables() {
    local action="$1"
    local warehouse_name="$2"
    local workspace_name="$3"
	local table_directory="$4"
    
    case "$action" in
        "create")
            create_wh_tables "$warehouse_name" "$workspace_name" "$table_directory"
            ;;
        *)
            log_error "Unknown action: $action"
            log_info "Supported actions: create"
            return 1
            ;;
    esac
}

# Main script logic
main() {
    manage_warehouse_tables "$@"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

# # Example usage
# BASE_DIR="$(cd "$(dirname "$SCRIPT_DIR")/../.." && pwd)"
# TABLES_DIR="$BASE_DIR/Workspaces/DataEngineeringWSDevCICD/GoldWarehouse.Warehouse/dbo/Tables/"

# workspace_name="FabricCLI-DEDev"
# warehouse_name="CLIWH"
# # echo $output
# create_wh_tables "$warehouse_name" "$workspace_name" "$TABLES_DIR"