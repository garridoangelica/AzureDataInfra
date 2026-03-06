"""
Fabric workspace deployment script.
Supports full deployment (all items) and selective feature releases (specific items).
Includes preflight validation to catch missing dependencies before deployment.
"""
import sys
import re
import json
import argparse
import tempfile
from pathlib import Path

import yaml
from fabric_cicd import deploy_with_config, append_feature_flag
from auth import get_fabric_credential


# ── Helpers ──────────────────────────────────────────────────────────────────

def build_item_exclude_regex(item_names: list) -> str:
    """
    Return a regex matching anything EXCEPT the supplied item names.
    Used to limit publishing to only the listed items during a feature release.
    """
    escaped = [re.escape(n.strip()) for n in item_names if n.strip()]
    if not escaped:
        return None
    return rf"^(?!(?:{'|'.join(escaped)})$).*"


def parse_parameter_item_refs(parameter_yml: Path) -> list[dict]:
    """
    Extract all $items.{Type}.{Name}.$id references from parameter.yml.
    Returns a list of dicts: [{"type": "Lakehouse", "name": "SilverLakehouse"}, ...]
    """
    if not parameter_yml.exists():
        return []

    with open(parameter_yml, encoding="utf-8") as fh:
        raw = fh.read()

    refs = []
    # Matches: $items.Lakehouse.SilverLakehouse.$id
    for m in re.finditer(r'\$items\.(\w+)\.(\w+)\.\$id', raw):
        refs.append({"type": m.group(1), "name": m.group(2)})
    return refs


def get_workspace_items_from_api(workspace_name: str, credential) -> list[dict]:
    """
    Fetch all items currently in the target Fabric workspace via REST API.
    Returns list of dicts with 'displayName' and 'type'.
    """
    import urllib.request
    import urllib.error

    # Acquire token for Fabric API
    token = credential.get_token("https://api.fabric.microsoft.com/.default").token

    # First resolve workspace name → ID
    url = "https://api.fabric.microsoft.com/v1/workspaces"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as resp:
            workspaces = json.loads(resp.read())["value"]
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Failed to list workspaces: {e.code} {e.reason}")

    ws = next((w for w in workspaces if w["displayName"] == workspace_name), None)
    if not ws:
        raise RuntimeError(
            f"Workspace '{workspace_name}' not found. "
            "Verify it exists and the SPN has access."
        )

    ws_id = ws["id"]

    # List items in the workspace
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{ws_id}/items"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())["value"]
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Failed to list workspace items: {e.code} {e.reason}")


def preflight_validate(config_path: Path, environment: str, credential) -> bool:
    """
    Run preflight checks before deployment:
      1. Verify all source item folders exist locally.
      2. Verify all $items.X.Y.$id references in parameter.yml resolve to items
         that are either being deployed (present locally) or already exist in
         the target workspace.

    Returns True if all checks pass, False otherwise.
    """
    with open(config_path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    repo_dir = (config_path.parent / cfg["core"]["repository_directory"]).resolve()
    parameter_file = (config_path.parent / cfg["core"].get("parameter", "parameter.yml")).resolve()
    workspace_name = cfg["core"]["workspace"][environment]
    item_types_in_scope = cfg["core"].get("item_types_in_scope", [])

    errors = []
    warnings = []

    print(f"\n{'='*60}")
    print(f"Preflight Validation")
    print(f"Environment      : {environment}")
    print(f"Target Workspace : {workspace_name}")
    print(f"Source Directory : {repo_dir}")
    print(f"{'='*60}\n")

    # ── Check 1: source directory exists ────────────────────────────────────
    if not repo_dir.exists():
        errors.append(f"Source directory not found: {repo_dir}")
    else:
        print(f"[OK] Source directory exists: {repo_dir}")

        # ── Check 2: each in-scope item type has at least one folder ────────
        for item_type in item_types_in_scope:
            suffix = f".{item_type}"
            matches = [d for d in repo_dir.iterdir() if d.is_dir() and d.name.endswith(suffix)]
            if not matches:
                warnings.append(f"No '{item_type}' folders found in source directory")
            else:
                for m in matches:
                    platform_file = m / ".platform"
                    if not platform_file.exists():
                        errors.append(f"Missing .platform file in: {m.name}")
                    else:
                        print(f"[OK] {m.name}")

    # ── Check 3: parameter.yml dependency resolution ─────────────────────────
    refs = parse_parameter_item_refs(parameter_file)
    if refs:
        print(f"\nChecking {len(refs)} parameter.yml item reference(s) against target workspace...")
        try:
            existing_items = get_workspace_items_from_api(workspace_name, credential)
            existing = {(i["type"], i["displayName"]) for i in existing_items}

            # Also include items present locally (they will be deployed)
            local_items = set()
            if repo_dir.exists():
                for d in repo_dir.iterdir():
                    if d.is_dir():
                        parts = d.name.rsplit(".", 1)
                        if len(parts) == 2:
                            local_items.add((parts[1], parts[0]))

            for ref in refs:
                key = (ref["type"], ref["name"])
                if key in existing:
                    print(f"[OK] {ref['type']}.{ref['name']} exists in target workspace")
                elif key in local_items:
                    print(f"[OK] {ref['type']}.{ref['name']} will be deployed from source")
                else:
                    errors.append(
                        f"{ref['type']}.{ref['name']} is referenced in parameter.yml "
                        f"but does not exist in '{workspace_name}' and is not in the source folder"
                    )
        except RuntimeError as e:
            warnings.append(f"Could not check target workspace items: {e}")

    # ── Summary ──────────────────────────────────────────────────────────────
    print()
    if warnings:
        for w in warnings:
            print(f"[WARN] {w}")

    if errors:
        print()
        for e in errors:
            print(f"[FAIL] {e}")
        print(f"\nPreflight FAILED — {len(errors)} error(s) found. Fix them before deploying.\n")
        return False

    print("Preflight PASSED — all checks OK.\n")
    return True


# ── Deployment ────────────────────────────────────────────────────────────────

def deploy_workspace_items(
    config_file: str,
    environment: str = "DEV",
    use_cli_auth: bool = False,
    items: list = None,
    validate_only: bool = False,
):
    config_path = Path(config_file).resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    credential = get_fabric_credential(use_cli=use_cli_auth)

    # Always run preflight
    ok = preflight_validate(config_path, environment, credential)
    if not ok or validate_only:
        if not ok:
            sys.exit(1)
        return

    # Enable required feature flags
    append_feature_flag("enable_experimental_features")
    append_feature_flag("enable_config_deploy")

    mode = "Feature Release" if items else "Full Deployment"
    print(f"{'='*60}")
    print(f"Deployment Mode  : {mode}")
    print(f"Environment      : {environment}")
    print(f"Config           : {config_path}")
    if items:
        print(f"Items            : {', '.join(items)}")
    print(f"{'='*60}\n")

    if items:
        include_regex = build_item_exclude_regex(items)
        with open(config_path, encoding="utf-8") as fh:
            cfg = yaml.safe_load(fh)

        cfg.setdefault("publish", {})["exclude_regex"] = include_regex
        cfg.setdefault("unpublish", {})["skip"] = {"DEV": True, "TEST": True, "PROD": True}

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False,
            dir=config_path.parent, encoding="utf-8",
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
        deploy_with_config(
            config_file_path=str(config_path),
            environment=environment,
            token_credential=credential,
        )

    print(f"\n{'='*60}")
    print("Deployment completed successfully!")
    print(f"{'='*60}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Deploy Fabric workspace items",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate dependencies only (no deployment)
  python deploy.py --environment TEST --cli-auth --validate

  # Full deployment to TEST
  python deploy.py --environment TEST --cli-auth

  # Feature release: one pipeline to PROD
  python deploy.py --environment PROD --cli-auth --items "OrchestrateSilverToGoldPipeline"

  # Feature release: multiple items
  python deploy.py --environment PROD --cli-auth --items "PipelineA,SilverToGoldNotebook"
""",
    )
    parser.add_argument("--config", default="config.yml", help="Path to config.yml")
    parser.add_argument(
        "--environment", choices=["DEV", "TEST", "PROD"], default="DEV",
        help="Target environment (default: DEV)",
    )
    parser.add_argument(
        "--cli-auth", action="store_true",
        help="Use Azure CLI / OIDC authentication (for CI/CD)",
    )
    parser.add_argument(
        "--items", default="",
        help="Comma-separated item names to deploy (feature release). Omit for all items.",
    )
    parser.add_argument(
        "--validate", action="store_true",
        help="Run preflight validation only — do not deploy.",
    )

    args = parser.parse_args()
    item_list = (
        [i.strip() for i in args.items.split(",") if i.strip()] if args.items else None
    )

    try:
        deploy_workspace_items(
            args.config,
            environment=args.environment,
            use_cli_auth=args.cli_auth,
            items=item_list,
            validate_only=args.validate,
        )
    except Exception as e:
        print(f"\nDeployment failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
