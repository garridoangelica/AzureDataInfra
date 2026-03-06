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


# ── Helpers ───────────────────────────────────────────────────────────────────

def build_item_exclude_regex(item_names: list) -> str:
    """Return a regex matching anything EXCEPT the supplied item names."""
    escaped = [re.escape(n.strip()) for n in item_names if n.strip()]
    if not escaped:
        return None
    return rf"^(?!(?:{'|'.join(escaped)})$).*"


def parse_parameter_item_refs(parameter_yml: Path) -> list:
    """Extract all $items.{Type}.{Name}.$id references from parameter.yml."""
    if not parameter_yml.exists():
        return []
    with open(parameter_yml, encoding="utf-8") as fh:
        raw = fh.read()
    refs = []
    for m in re.finditer(r'\$items\.(\w+)\.(\w+)\.\$id', raw):
        entry = {"type": m.group(1), "name": m.group(2)}
        if entry not in refs:
            refs.append(entry)
    return refs


def get_workspace_info(workspace_name: str, credential):
    """
    Resolve workspace name → ID and fetch all items currently in it.
    Returns (workspace_id, list_of_items).
    Raises RuntimeError if the workspace cannot be reached or found.
    """
    import urllib.request
    import urllib.error

    token = credential.get_token("https://api.fabric.microsoft.com/.default").token
    headers = {"Authorization": f"Bearer {token}"}

    def api_get(url):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"API error {e.code} calling {url}: {e.reason}")

    workspaces = api_get("https://api.fabric.microsoft.com/v1/workspaces")["value"]
    ws = next((w for w in workspaces if w["displayName"] == workspace_name), None)
    if not ws:
        raise RuntimeError(
            f"Workspace '{workspace_name}' not found. "
            "Verify it exists and the SPN has Contributor access."
        )

    items = api_get(
        f"https://api.fabric.microsoft.com/v1/workspaces/{ws['id']}/items"
    )["value"]
    return ws["id"], items


# ── Preflight ─────────────────────────────────────────────────────────────────

def preflight_validate(
    config_path: Path,
    environment: str,
    credential,
    items: list = None,         # selected items for feature release (None = full deploy)
) -> bool:
    """
    Preflight checks before deployment.

    1. Target workspace is reachable and the SPN has access.
    2. Source item folders exist with valid .platform files.
    3. All $items.X.Y.$id references in parameter.yml resolve to items that
       will be present in the target workspace after this deployment:
         - already exists in target workspace, OR
         - is included in the current deployment set (source folder + selected items filter)
    """
    with open(config_path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    repo_dir      = (config_path.parent / cfg["core"]["repository_directory"]).resolve()
    parameter_file = (config_path.parent / cfg["core"].get("parameter", "parameter.yml")).resolve()
    workspace_name = cfg["core"]["workspace"][environment]
    item_types     = cfg["core"].get("item_types_in_scope", [])

    errors   = []
    warnings = []

    print(f"\n{'='*60}")
    print(f"Preflight Validation")
    print(f"Mode             : {'Feature Release (' + ', '.join(items) + ')' if items else 'Full Deployment'}")
    print(f"Environment      : {environment}")
    print(f"Target Workspace : {workspace_name}")
    print(f"Source Directory : {repo_dir}")
    print(f"{'='*60}\n")

    # ── Check 1: Target workspace is reachable ────────────────────────────────
    print("[ 1 ] Checking target workspace accessibility...")
    target_items_existing = set()
    try:
        _, existing_items = get_workspace_info(workspace_name, credential)
        target_items_existing = {(i["type"], i["displayName"]) for i in existing_items}
        print(f"      [OK] Workspace '{workspace_name}' is reachable "
              f"({len(existing_items)} item(s) currently deployed)")
    except RuntimeError as e:
        errors.append(f"Cannot reach target workspace: {e}")
        print(f"      [FAIL] {e}")

    # ── Check 2: Source directory and item folder structure ───────────────────
    print("\n[ 2 ] Checking source item folders...")
    local_items = set()   # (type, name) pairs present in source folder

    if not repo_dir.exists():
        errors.append(f"Source directory not found: {repo_dir}")
        print(f"      [FAIL] Source directory not found: {repo_dir}")
    else:
        for item_type in item_types:
            suffix = f".{item_type}"
            matches = [d for d in repo_dir.iterdir() if d.is_dir() and d.name.endswith(suffix)]
            if not matches:
                warnings.append(f"No '{item_type}' folders found in source directory")
            for folder in matches:
                item_name = folder.name[: -len(suffix)]
                local_items.add((item_type, item_name))
                platform_file = folder / ".platform"
                if not platform_file.exists():
                    errors.append(f"Missing .platform file in: {folder.name}")
                    print(f"      [FAIL] Missing .platform in {folder.name}")
                else:
                    print(f"      [OK]   {folder.name}")

    # ── Check 3: Dependency resolution against TARGET workspace ───────────────
    refs = parse_parameter_item_refs(parameter_file)
    if refs:
        print(f"\n[ 3 ] Checking {len(refs)} parameter.yml dependency reference(s)...")

        # Items that WILL be in the target workspace after this deployment:
        #   a) already there, OR
        #   b) in the source AND (full deploy OR included in selected items list)
        def will_be_deployed(item_type: str, item_name: str) -> bool:
            # Already exists in target workspace
            if (item_type, item_name) in target_items_existing:
                return True
            # Present in source and will be deployed
            if (item_type, item_name) in local_items:
                if items is None:
                    # Full deployment — all local items are deployed
                    return True
                else:
                    # Feature release — only selected items are deployed
                    if item_name in items:
                        return True
            return False

        for ref in refs:
            t, n = ref["type"], ref["name"]
            if (t, n) in target_items_existing:
                print(f"      [OK]   {t}.{n} — already exists in target workspace")
            elif (t, n) in local_items and (items is None or n in (items or [])):
                print(f"      [OK]   {t}.{n} — will be deployed in this run")
            elif (t, n) in local_items and items is not None and n not in items:
                errors.append(
                    f"{t}.{n} is referenced in parameter.yml, exists locally but is NOT "
                    f"selected for this feature release and is NOT yet in '{workspace_name}'. "
                    f"Either add '{n}' to the items list or deploy it separately first."
                )
                print(f"      [FAIL] {t}.{n} — exists locally but excluded from this release "
                      f"and not yet in target workspace")
            else:
                errors.append(
                    f"{t}.{n} is referenced in parameter.yml but does not exist "
                    f"in '{workspace_name}' and is not in the source folder."
                )
                print(f"      [FAIL] {t}.{n} — not found in target workspace or source folder")
    else:
        print("\n[ 3 ] No parameter.yml dependency references found — skipping.")

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    for w in warnings:
        print(f"[WARN] {w}")

    if errors:
        print()
        for e in errors:
            print(f"[FAIL] {e}")
        print(f"\nPreflight FAILED — {len(errors)} error(s). Fix before deploying.\n")
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

    ok = preflight_validate(config_path, environment, credential, items=items)
    if not ok:
        sys.exit(1)
    if validate_only:
        return

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
  # Validate only (no deployment)
  python deploy.py --environment TEST --cli-auth --validate

  # Full deployment to TEST
  python deploy.py --environment TEST --cli-auth

  # Feature release: one pipeline to PROD
  python deploy.py --environment PROD --cli-auth --items "OrchestrateSilverToGoldPipeline"

  # Feature release: multiple items
  python deploy.py --environment PROD --cli-auth --items "PipelineA,SilverToGoldNotebook"
""",
    )
    parser.add_argument("--config", default="config.yml")
    parser.add_argument(
        "--environment", choices=["DEV", "TEST", "PROD"], default="DEV",
    )
    parser.add_argument("--cli-auth", action="store_true")
    parser.add_argument(
        "--items", default="",
        help="Comma-separated item names (feature release). Omit for all items.",
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
