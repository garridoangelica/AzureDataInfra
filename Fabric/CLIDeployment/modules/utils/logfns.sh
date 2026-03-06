# set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Fabric CLI is available
check_fabric_cli() {
    log_info "Checking Fabric CLI availability..."
    
    if fab --version &> /dev/null; then
        log_success "Fabric CLI is available"
        fab --version
        return 0
    else
        log_error "Fabric CLI not found. Please ensure the conda environment is activated."
        log_info "Try: conda activate fabricclideployment"
        # return 1
    fi
}


# Load environment variables from .env file
load_env_file() {
    # .env file is in CLIDeployment folder (2 levels up from auth.sh)
    local env_file="$SCRIPT_DIR/../../.env"
    
    if [[ -f "$env_file" ]]; then
        log_info "Loading environment variables from: $env_file"
        
        # Export variables from .env file, ignoring comments and empty lines
        set -a  # automatically export all variables
        source "$env_file"
        set +a  # stop automatically exporting
        
        log_success "Environment variables loaded successfully"
        return 0
    else
        log_error "Environment file not found: $env_file"
        log_info "Expected location: CLIDeployment/.env"
        return 1
    fi
}