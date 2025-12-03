#!/bin/bash

# Fabric CLI Authentication Module
# Supports both interactive login and service principal authentication

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the logging functions
source "$SCRIPT_DIR/../utils/logfns.sh"

# Interactive authentication
auth_interactive() {
    log_info "Starting interactive authentication..."
    
    # Clear any existing authentication
    fab auth logout 2>/dev/null || true
    
    # Start interactive login
    log_info "Opening browser for authentication..."
    fab auth login
    
    if [ $? -eq 0 ]; then
        log_success "Interactive authentication successful"
        return 0
    else
        log_error "Interactive authentication failed"
        return 1
    fi
}

# Service Principal authentication
auth_service_principal() {
    local client_id=$1
    local client_secret=$2
    local tenant_id=$3
    
    log_info "Starting service principal authentication..."
    
    # Validate required parameters
    if [[ -z "$client_id" || -z "$client_secret" || -z "$tenant_id" ]]; then
        log_error "Missing required parameters for service principal authentication"
        log_info "Usage: auth_service_principal <client_id> <client_secret> <tenant_id>"
        return 1
    fi
    
    # Clear any existing authentication
    fab auth logout 2>/dev/null || true
    # Authenticate with service principal
    log_info "Authenticating with service principal..."
    fab auth login -u $client_id -p $client_secret --tenant $tenant_id
    
    if [ $? -eq 0 ]; then
        log_success "Service principal authentication successful"
        return 0
    else
        log_error "Service principal authentication failed"
        return 1
    fi
}

# Service Principal with environment variables
auth_service_principal_env() {
    log_info "Using service principal authentication with environment variables..."
    
    # Try to load .env file from CLIDeployment folder
    if ! load_env_file; then
        log_warning "Could not load .env file, checking existing environment variables..."
    fi

    # Check for required environment variables
    if [[ -z ${FABRIC_CLIENT_ID} || -z ${FABRIC_CLIENT_SECRET} || -z ${FABRIC_TENANT_ID} ]]; then
        log_error "Missing required environment variables:"
        log_error "  FABRIC_CLIENT_ID"
        log_error "  FABRIC_CLIENT_SECRET" 
        log_error "  FABRIC_TENANT_ID"
        return 1
    fi
    
    log_info "Environment variables found:"
    log_info "  FABRIC_CLIENT_ID,FABRIC_TENANT_ID & FABRIC_CLIENT_SECRET"
    log_success "Ready for service principal authentication"
    
    auth_service_principal $FABRIC_CLIENT_ID $FABRIC_CLIENT_SECRET $FABRIC_TENANT_ID
}

# Check current authentication status
check_auth_status() {
    log_info "Checking authentication status..."
    
    # Try to get current user info to verify authentication
    if fab ls &> /dev/null; then
        log_success "Already authenticated to Fabric"
        return 0
    else
        log_warning "Not currently authenticated to Fabric"
        return 1
    fi
}

# Logout function
logout() {
    log_info "Logging out from Fabric CLI..."
    fab auth logout
    log_success "Logged out successfully"
}

# Display usage information
usage() {
    echo "Fabric CLI Authentication Script"
    echo
    echo "Usage:"
    echo "  $0 <auth_method> [options]"
    echo
    echo "Authentication Methods:"
    echo "  interactive                           - Browser-based interactive login (default)"
    echo "  service-principal <id> <secret> <tenant> - Service principal with parameters"  
    echo "  env                                   - Service principal with environment variables"
    echo
    echo "Other Commands:"
    echo "  status                               - Check current authentication status"
    echo "  logout                               - Logout from Fabric CLI"
    echo "  help                                 - Show this help message"
    echo
    echo "Environment Variables (for service principal):"
    echo "  FABRIC_CLIENT_ID      - Service principal client ID"
    echo "  FABRIC_CLIENT_SECRET  - Service principal client secret"
    echo "  FABRIC_TENANT_ID      - Azure tenant ID"
    echo
    echo "Examples:"
    echo "  $0 interactive"
    echo "  $0 service-principal abc-123 secret-456 def-789"
    echo "  export FABRIC_CLIENT_ID=abc-123 && export FABRIC_CLIENT_SECRET=secret-456 && export FABRIC_TENANT_ID=def-789 && $0 env"
}

# Main authentication function for external calls
fabric_auth() {
    local auth_method="${1:-env}"
    
    case "$auth_method" in
        "interactive"|"browser")
            auth_interactive
            ;;
        "service-principal"|"sp")
            if [[ -n "$2" && -n "$3" && -n "$4" ]]; then
                auth_service_principal "$2" "$3" "$4"
            else
                auth_service_principal_env
            fi
            ;;
        "env")
            auth_service_principal_env
            ;;
        "status")
            check_auth_status
            ;;
        "logout")
            logout
            ;;
        "help"|"-h"|"--help")
            usage
            ;;
        *)
            log_error "Unknown authentication method: $auth_method"
            log_info "Supported methods: interactive, service-principal, env, status, logout"
            return 1
            ;;
    esac
}

# Main script logic (for backward compatibility)
main() {
    fabric_auth "$@"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "${@:-env}"
fi
