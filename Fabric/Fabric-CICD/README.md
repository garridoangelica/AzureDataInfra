# Fabric CI/CD Deployment

Python scripts and GitHub Actions workflows for deploying Microsoft Fabric workspace items using the [`fabric-cicd`](https://github.com/microsoft/fabric-cicd) library.

## Repository layout

```
.github/
  workflows/
    fabric-deploy.yml           # Full pipeline: all items Dev → Test → Prod
    fabric-feature-release.yml  # Selective release: choose which items to deploy
Fabric/
  Fabric-CICD/
    deploy.py       # Deployment script (supports full & selective modes)
    config.yml      # Environment workspace names, item types, publish rules
    parameter.yml   # Find/replace rules for environment-specific IDs
    auth.py         # Authentication helper (interactive / CLI / OIDC)
    requirements.txt
  Workspaces/
    DataEngineeringWSDevCICD/   # Source workspace items committed to Git
      GoldWarehouse.Warehouse/
      OrchestrateSilverToGoldPipeline.DataPipeline/
      SilverLakehouse.Lakehouse/
      SilverToGoldNotebook.Notebook/
```

## Prerequisites

- Python 3.9–3.12 (`fabric-cicd` does not support 3.13+)
- Azure CLI (for local CLI auth or CI/CD)
- Service principal with Contributor access to the target Fabric workspaces
- Target workspaces must exist in Fabric before the first deployment

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

### config.yml

Controls what gets deployed and where.

| Section | Purpose |
|---------|---------|
| `core.workspace` | Maps `DEV / TEST / PROD` to Fabric workspace names |
| `core.repository_directory` | Path to workspace items folder (relative to config) |
| `core.item_types_in_scope` | Item types the deployer will touch |
| `publish.exclude_regex` | Items matching this regex are skipped during publish |
| `unpublish.skip` | Whether to remove orphaned items per environment |

### parameter.yml

Defines find/replace rules applied to item content during deployment so that
environment-specific IDs (workspace IDs, lakehouse IDs, etc.) are substituted
correctly in each target environment.

## GitHub Actions workflows

### 1. Full Deployment — `fabric-deploy.yml`

Deploys **all** in-scope items from Dev → Test → Prod.

**Triggers**
- Push to `main` (when files under `Fabric/` change)
- Manual dispatch (`workflow_dispatch`) with optional `skip_prod` flag

**Flow**

```
Push to main
    │
    ▼
Deploy to TEST  ──── (fabric-test environment, optional reviewers)
    │
    ▼  (waits for approval if fabric-prod environment has required reviewers)
Deploy to PROD  ──── (fabric-prod environment)
```

### 2. Feature Release — `fabric-feature-release.yml`

Deploys **selected items only**. Use this when some items are ready to ship
while others are still in progress.

**Triggers**
- Manual dispatch only (`workflow_dispatch`)

**Inputs**

| Input | Required | Description |
|-------|----------|-------------|
| `environment` | Yes | `TEST` or `PROD` |
| `items` | No | Comma-separated item names, e.g. `OrchestrateSilverToGoldPipeline,SilverToGoldNotebook`. Leave blank to deploy all. |
| `dry_run` | No | Print what would be deployed without actually deploying. |

**Example — deploy one pipeline to PROD**

1. Go to **Actions → Fabric - Feature Release → Run workflow**
2. Set `environment` = `PROD`
3. Set `items` = `OrchestrateSilverToGoldPipeline`
4. Click **Run workflow**

The workflow patches the config at runtime so only the listed items are
published. Orphan cleanup (`unpublish`) is automatically disabled during
feature releases to avoid removing items that weren't included in the selection.

## Running locally

```bash
# Full deployment to TEST (interactive browser auth)
python deploy.py --environment TEST

# Full deployment to PROD (Azure CLI auth)
python deploy.py --environment PROD --cli-auth

# Feature release — one item to PROD
python deploy.py --environment PROD --cli-auth --items "OrchestrateSilverToGoldPipeline"

# Feature release — multiple items to TEST
python deploy.py --environment TEST --cli-auth --items "PipelineA,SilverToGoldNotebook"
```

## Required GitHub secrets

| Secret | Description |
|--------|-------------|
| `AZURE_CLIENT_ID` | Service principal / managed identity client ID |
| `AZURE_TENANT_ID` | Azure AD tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |

Authentication uses OIDC (federated credentials) via `azure/login@v2` —
no client secret is stored in GitHub.

## Setting up environment protection rules

To enforce a manual approval gate before PROD deployments:

1. Go to **Repository → Settings → Environments**
2. Create environments named `fabric-test` and `fabric-prod`
3. On `fabric-prod`, add **Required reviewers** (your team leads or a release manager)

Every PROD deployment (full or feature release) will pause and wait for
approval before proceeding.
