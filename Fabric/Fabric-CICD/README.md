# Fabric CI/CD Deployment Scripts

Python scripts for deploying Microsoft Fabric workspace items using the `fabric-cicd` library.

## Prerequisites

- Python 3.9-3.12 (fabric-cicd doesn't support Python 3.13+)
- Azure CLI (for CI/CD authentication)
- Fabric workspace access
- Target workspace must exist in Fabric before deployment

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Local Deployment (Interactive Authentication)

```bash
# Deploy to DEV environment (default)
python deploy.py

# Deploy to TEST environment
python deploy.py --environment TEST

# Deploy to PROD environment
python deploy.py --environment PROD
```

### CI/CD Deployment (Azure CLI Authentication)

```bash
az login --service-principal -u <client-id> -p <client-secret> --tenant <tenant-id>
python deploy.py --environment PROD --cli-auth
```

## Configuration

### config.yml
Located in `Fabric-CICD/config.yml`:
- **Core settings**: Environment-specific workspace names, repository path, item types
- **Publish settings**: Control which items to publish per environment
- **Unpublish settings**: Control orphan cleanup per environment
- **Features**: Enable experimental features like configuration-based deployment

### parameter.yml
Located in each workspace folder (e.g., `Workspaces/DataEngineeringWSDevCICD/parameter.yml`):
- Environment-specific value replacements (DEV, TEST, PROD)
- Find/replace patterns for IDs, connection strings, etc.
- JSONPath-based key/value replacements

### Environment Strategy
- **DEV**: Development workspace for testing and validation
- **TEST**: Pre-production testing environment
- **PROD**: Production workspace with stricter controls (no orphan cleanup)

## GitHub Actions

The `.github/workflows/fabric-deploy.yml` workflow automatically deploys on push to main branch.

Required secrets:
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
