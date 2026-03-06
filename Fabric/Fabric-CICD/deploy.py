"""
Fabric workspace deployment script.
Supports full deployment (all items) and selective feature releases (specific items).
"""
import sys
import re
import argparse
import tempfile
from pathlib import Path

import yaml
from fabric_cicd import deploy_with_config, append_feature_flag
from auth import get_fabric_credential


def build_item_exclude_regex(item_names: list) -> str:
    """
    Return a regex that matches anything EXCEPT the supplied item names.
    The fabric-cicd library uses exclude_regex to skip matching items,
    so inverting it limits deployment to only the listed names.
    """
    escaped = [re.escape(n.strip()) for n in item_names if n.strip()]
    if not escaped:
        return None
    alternation = "|".join(escaped)
    return rf"^(?!(?:{alternation})$).*"


def deploy_workspace_items(
    config_file: str,
    environment: str = "DEV",
    use_cli_auth: bool = False,
    items: list = None,
):
    """
    Deploy workspace items to Fabric.

    Args:
        config_file:   Path to config.yml
        environment:   Target environment (DEV, TEST, PROD)
        use_cli_auth:  Use Azure CLI / OIDC authentication (CI/CD)
        items:         Optional list of item names to deploy (feature release).
                       When None or empty, all in-scope items are deployed.
    """
    config_path = Path(config_file).resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    credential = get_fabric_credential(use_cli=use_cli_auth)

    # Enable required feature flags
    append_feature_flag("enable_experimental_features")
    append_feature_flag("enable_config_deploy")

    mode = "Feature Release" if items else "Full Deployment"
    print(f"\n{'='*60}")
    print(f"Deployment Mode  : {mode}")
    print(f"Environment      : {environment}")
    print(f"Config           : {config_path}")
    if items:
        print(f"Items            : {', '.join(items)}")
    print(f"{'='*60}\n")

    if items:
        # --- Feature release: patch config so only the selected items are published ---
        include_regex = build_item_exclude_regex(items)
        with open(config_path, "r", encoding="utf-8") as fh:
            cfg = yaml.safe_load(fh)

        # Limit publishing to the selected items only
        cfg.setdefault("publish", {})["exclude_regex"] = include_regex

        # Disable orphan cleanup during selective releases to avoid removing
        # items that simply weren't included in this release
        cfg.setdefault("unpublish", {})["skip"] = {
            "DEV": True,
            "TEST": True,
            "PROD": True,
        }

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".yml",
            delete=False,
            dir=config_path.parent,
            encoding="utf-8",
        ) as tmp:
            yaml.dump(cfg, tmp, allow_unicode=True)
            tmp_path = Path(tmp.name)

        try:
            deploy_with_config(
                config_file_path=str(tmp_path),
                environment=environment,
                token_credential=credential,
            )
        finally:
            tmp_path.unlink(missing_ok=True)

    else:
        # --- Full deployment: use original config as-is ---
        deploy_with_config(
            config_file_path=str(config_path),
            environment=environment,
            token_credential=credential,
        )

    print(f"\n{'='*60}")
    print("Deployment completed successfully!")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="Deploy Fabric workspace items",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full deployment to TEST
  python deploy.py --environment TEST --cli-auth

  # Feature release: one pipeline to PROD
  python deploy.py --environment PROD --cli-auth --items "OrchestrateSilverToGoldPipeline"

  # Feature release: multiple items to PROD
  python deploy.py --environment PROD --cli-auth --items "PipelineA,SilverToGoldNotebook"
""",
    )
    parser.add_argument(
        "--config",
        default="config.yml",
        help="Path to config.yml (default: config.yml)",
    )
    parser.add_argument(
        "--environment",
        choices=["DEV", "TEST", "PROD"],
        default="DEV",
        help="Target environment (default: DEV)",
    )
    parser.add_argument(
        "--cli-auth",
        action="store_true",
        help="Use Azure CLI / OIDC authentication (for CI/CD)",
    )
    parser.add_argument(
        "--items",
        default="",
        help=(
            "Comma-separated item names to deploy (feature release). "
            "When omitted all in-scope items are deployed."
        ),
    )

    args = parser.parse_args()
    item_list = (
        [i.strip() for i in args.items.split(",") if i.strip()]
        if args.items
        else None
    )

    try:
        deploy_workspace_items(
            args.config,
            environment=args.environment,
            use_cli_auth=args.cli_auth,
            items=item_list,
        )
    except Exception as e:
        print(f"\nDeployment failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
