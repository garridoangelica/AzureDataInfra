# Azure Key Vault + Microsoft Fabric Connectivity Scripts

This collection of PowerShell scripts helps configure Azure Key Vault firewall rules for Microsoft Fabric connectivity when Fabric is not using Managed Private Endpoints. This is for establishing connection from Spark notebooks to AKV behind a firewall. 

## 📋 Prerequisites

- **PowerShell 5.1 or later**
- **Azure CLI** installed and configured (`az login`)
- **Azure Key Vault** with network restrictions enabled
- **Azure Service Tags JSON file** (download latest from Microsoft)
- **Permissions**: Key Vault Contributor or Owner role

## 📁 Files Overview

| Script | Purpose | Status |
|--------|---------|---------|
| `Analyze-AzureRegion-Simple.ps1` | Analyze IP ranges for any Azure region | ✅ Ready |
| `Add-Major-Ranges-Region.ps1` | Add major infrastructure ranges to Key Vault | ✅ Ready |
| `Complete-KeyVault-Cleanup.ps1` | Clean up Key Vault firewall rules | ✅ Ready |
| `Extract-FabricUS-IPRanges.ps1` | Extract US PowerBI service tag ranges | ✅ Optional |

## 🚀 Quick Start

### 1. Download Azure Service Tags

First, download the latest Azure Service Tags file:

**Option A: Manual Download (Recommended)**
1. Visit: https://www.microsoft.com/en-us/download/details.aspx?id=56519
2. Download the latest "Azure IP Ranges and Service Tags – Public Cloud" JSON file
3. Rename it to `ServiceTags_Public.json` or use the full filename

**Option B: PowerShell (Direct Download)**
```powershell
# Working URL for December 8, 2025 version (tested)
Invoke-WebRequest -Uri "https://download.microsoft.com/download/7/1/d/71d86715-5596-4529-9b13-da13a5de5b63/ServiceTags_Public_20251208.json" -OutFile "ServiceTags_Public.json"

# For other dates, update the date in filename (format: YYYYMMDD)
# Invoke-WebRequest -Uri "https://download.microsoft.com/download/7/1/d/71d86715-5596-4529-9b13-da13a5de5b63/ServiceTags_Public_YYYYMMDD.json" -OutFile "ServiceTags_Public.json"
```

**Note**: Service tags are updated weekly. For the latest version, use Option A above.

### 2. Basic Usage Workflow

```powershell
# Step 1: Analyze your region's IP ranges
.\Analyze-AzureRegion-Simple.ps1 -ServiceTagsFile "ServiceTags_Public.json" -Region "eastus"

# Step 2: Preview what would be added (RECOMMENDED)
.\Add-Major-Ranges-Region.ps1 -ServiceTagsFile "ServiceTags_Public.json" -Region "eastus" -KeyVaultName "your-keyvault" -ResourceGroupName "your-rg" -WhatIf

# Step 3: Add the ranges to Key Vault
.\Add-Major-Ranges-Region.ps1 -ServiceTagsFile "ServiceTags_Public.json" -Region "eastus" -KeyVaultName "akv-dev-fabric" -ResourceGroupName "rg-ag-dev-msft-eastus-fabric"
```

## 📖 Detailed Script Documentation

### 🔍 Analyze-AzureRegion-Simple.ps1

**Purpose**: Analyze Azure infrastructure IP ranges for any region.

**Syntax**:
```powershell
.\Analyze-AzureRegion-Simple.ps1 -ServiceTagsFile <path> -Region <region>
```

**Parameters**:
- `-ServiceTagsFile`: Path to Azure Service Tags JSON file
- `-Region`: Azure region name (e.g., "eastus", "westus2", "northeurope")

**Examples**:
```powershell
# Analyze East US infrastructure
.\Analyze-AzureRegion-Simple.ps1 -ServiceTagsFile "ServiceTags_Public.json" -Region "eastus"

# Analyze West Europe infrastructure  
.\Analyze-AzureRegion-Simple.ps1 -ServiceTagsFile "ServiceTags_Public.json" -Region "westeurope"

# Check available regions (if you use wrong region name)
.\Analyze-AzureRegion-Simple.ps1 -ServiceTagsFile "ServiceTags_Public.json" -Region "invalid"
```

**Output**:
- Total IP ranges count
- Major infrastructure ranges (/15, /16, /17 networks)
- Sample IP ranges
- Usage recommendations

---

### ➕ Add-Major-Ranges-Region.ps1

**Purpose**: Add major Azure infrastructure ranges to Key Vault firewall rules.

**Syntax**:
```powershell
.\Add-Major-Ranges-Region.ps1 -ServiceTagsFile <path> -Region <region> -KeyVaultName <name> -ResourceGroupName <rg> [-WhatIf]
```

**Parameters**:
- `-ServiceTagsFile`: Path to Azure Service Tags JSON file
- `-Region`: Azure region name
- `-KeyVaultName`: Name of your Azure Key Vault
- `-ResourceGroupName`: Resource group containing the Key Vault
- `-WhatIf`: Preview mode (shows what would be added without making changes)

**Examples**:
```powershell
# ALWAYS preview first (recommended)
.\Add-Major-Ranges-Region.ps1 -ServiceTagsFile "ServiceTags_Public.json" -Region "eastus" -KeyVaultName "akv-dev-fabric" -ResourceGroupName "rg-dev-fabric" -WhatIf

# Add ranges to Key Vault (after preview)
.\Add-Major-Ranges-Region.ps1 -ServiceTagsFile "ServiceTags_Public.json" -Region "eastus" -KeyVaultName "akv-dev-fabric" -ResourceGroupName "rg-dev-fabric"

# Different region example
.\Add-Major-Ranges-Region.ps1 -ServiceTagsFile "ServiceTags_Public.json" -Region "westus2" -KeyVaultName "my-keyvault" -ResourceGroupName "my-rg" -WhatIf
```

**Features**:
- ✅ Validates region exists
- ✅ Shows current Key Vault rules
- ✅ Identifies new vs existing ranges
- ✅ Confirmation prompt for large additions
- ✅ Progress tracking
- ✅ Success/failure reporting

---

### 🧹 Complete-KeyVault-Cleanup.ps1

**Purpose**: Remove all existing Key Vault firewall rules and add only essential IPs.

**Syntax**:
```powershell
.\Complete-KeyVault-Cleanup.ps1 -KeyVaultName <name> -ResourceGroupName <rg> [-UserIP <ip>] [-AzureEastUSRange <range>]
```

**Parameters**:
- `-KeyVaultName`: Name of your Azure Key Vault
- `-ResourceGroupName`: Resource group containing the Key Vault
- `-UserIP`: Your management IP (default: 99.137.14.9/32)
- `-AzureEastUSRange`: Azure infrastructure range (default: 4.236.128.0/17)

**Examples**:
```powershell
# Basic cleanup (uses defaults)
.\Complete-KeyVault-Cleanup.ps1 -KeyVaultName "akv-dev-fabric" -ResourceGroupName "rg-dev-fabric"

# Custom IP addresses
.\Complete-KeyVault-Cleanup.ps1 -KeyVaultName "my-kv" -ResourceGroupName "my-rg" -UserIP "1.2.3.4/32" -AzureEastUSRange "10.0.0.0/16"
```

**⚠️ WARNING**: This script **removes ALL existing firewall rules** before adding the specified ones. Use with caution!

---

### 📊 Extract-FabricUS-IPRanges.ps1

**Purpose**: Extract US-only PowerBI service tag ranges (alternative approach).

**Syntax**:
```powershell
.\Extract-FabricUS-IPRanges.ps1 -ServiceTagsFile <path>
```

**Note**: This is an alternative to the major ranges approach. Most users should use `Add-Major-Ranges-Region.ps1` instead.

## 🎯 Recommended Workflow

### For New Setup:

1. **Analyze your region**:
   ```powershell
   .\Analyze-AzureRegion-Simple.ps1 -ServiceTagsFile "ServiceTags_Public.json" -Region "eastus"
   ```

2. **Preview changes**:
   ```powershell
   .\Add-Major-Ranges-Region.ps1 -ServiceTagsFile "ServiceTags_Public.json" -Region "eastus" -KeyVaultName "your-kv" -ResourceGroupName "your-rg" -WhatIf
   ```

3. **Apply changes**:
   ```powershell
   .\Add-Major-Ranges-Region.ps1 -ServiceTagsFile "ServiceTags_Public.json" -Region "eastus" -KeyVaultName "your-kv" -ResourceGroupName "your-rg"
   ```

4. **Test Fabric connectivity**:
   ```python
   # In your Microsoft Fabric notebook
   secret = notebookutils.credentials.getSecret('https://your-kv.vault.azure.net/', 'SecretName')
   ```

### For Cleanup:

```powershell
# Reset to minimal configuration
.\Complete-KeyVault-Cleanup.ps1 -KeyVaultName "your-kv" -ResourceGroupName "your-rg"

# Then re-add what you need
.\Add-Major-Ranges-Region.ps1 -ServiceTagsFile "ServiceTags_Public.json" -Region "eastus" -KeyVaultName "your-kv" -ResourceGroupName "your-rg"
```

## 🔧 Troubleshooting

### Common Issues:

**1. "AzureCloud.region not found"**
```powershell
# Check available regions
.\Analyze-AzureRegion-Simple.ps1 -ServiceTagsFile "ServiceTags_Public.json" -Region "invalid"
```

**2. "Failed to get Key Vault rules"**
```bash
# Ensure you're logged into Azure CLI
az login
az account show

# Check permissions
az keyvault show --name "your-kv" --resource-group "your-rg"
```

**3. "403 Forbidden from Fabric"**
- Your current IP range configuration may not cover all Fabric IPs
- Try adding major ranges for your region
- Check Fabric error logs for the specific IP being denied

**4. "Service Tags file not found"**
- **Solution**: Download latest from official Microsoft page:
- Visit: https://www.microsoft.com/en-us/download/details.aspx?id=56519
- Download "Azure IP Ranges and Service Tags – Public Cloud" JSON file
- Make sure the file path matches what you're using in the scripts

### Regional Coverage Comparison:

| Region | Total IPv4 | Major Ranges | Recommended For |
|--------|------------|--------------|-----------------|
| eastus | 471 | 95 | High Fabric usage |
| westus2 | 371 | 28 | Moderate usage |
| westeurope | ~400 | ~50 | EU workloads |

## 🔐 Security Considerations

- **Principle of Least Privilege**: Only add ranges for your Fabric region
- **Regular Updates**: Update service tags monthly
- **Monitoring**: Monitor Key Vault access logs
- **Documentation**: Document which ranges you've added and why

## 📝 Change Log

- **v1.2**: Added region flexibility to all scripts
- **v1.1**: Added major ranges approach (/15,/16,/17 only)
- **v1.0**: Initial PowerBI service tag extraction

## 🆘 Support

For issues with:
- **Scripts**: Check syntax and parameters in this README
- **Azure connectivity**: Verify Azure CLI login and permissions
- **Fabric connectivity**: Test with `notebookutils.credentials.getSecret()`
- **Key Vault access**: Check Azure portal firewall rules

---

**Last Updated**: December 2025  
**Compatible With**: Azure CLI 2.x, PowerShell 5.1+, Microsoft Fabric PSKU