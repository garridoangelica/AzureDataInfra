"""
Fabric workspace deployment script.
Deploys items from a workspace folder to Microsoft Fabric using configuration-based deployment.
"""
import sys
import argparse
from pathlib import Path
from fabric_cicd import deploy_with_config, append_feature_flag
from auth import get_fabric_credential


def deploy_workspace_items(config_file, environment="DEV", use_cli_auth=False):
    """
    Deploy all items from workspace folder to Fabric using configuration file.
    
    Args:
        config_file: Path to config.yml file
        environment: Target environment (DEV, TEST, PROD)
        use_cli_auth: Use Azure CLI authentication instead of interactive
    """
    # Resolve absolute path to config file
    config_path = Path(config_file).resolve()
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    # Authenticate
    credential = get_fabric_credential(use_cli=use_cli_auth)
    
    print(f"\n{'='*60}")
    print(f"Configuration-based Deployment")
    print(f"Environment: {environment}")
    print(f"Config: {config_path}")
    print(f"{'='*60}\n")
    
    # Enable required feature flags
    append_feature_flag("enable_experimental_features")
    append_feature_flag("enable_config_deploy")
    
    # Deploy using configuration file
    deploy_with_config(
        config_file_path=str(config_path),
        environment=environment,
        token_credential=credential
    )
    
    print(f"\n{'='*60}")
    print("Deployment completed successfully!")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="Deploy Fabric workspace items")
    parser.add_argument(
        "--config",
        default="config.yml",
        help="Path to config.yml file (default: config.yml)"
    )
    parser.add_argument(
        "--environment",
        choices=["DEV", "TEST", "PROD"],
        default="DEV",
        help="Target environment (default: DEV)"
    )
    parser.add_argument(
        "--cli-auth",
        action="store_true",
        help="Use Azure CLI authentication (for CI/CD)"
    )
    
    args = parser.parse_args()
    
    try:
        deploy_workspace_items(
            args.config,
            environment=args.environment,
            use_cli_auth=args.cli_auth
        )
    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
