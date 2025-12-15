# Add Major Azure Infrastructure Ranges for Any Region
# This script adds the larger CIDR blocks (/15, /16, /17) for comprehensive coverage

param(
    [Parameter(Mandatory)]
    [string]$ServiceTagsFile,
    
    [Parameter(Mandatory)]
    [string]$KeyVaultName,
    
    [Parameter(Mandatory)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory)]
    [string]$Region,
    
    [switch]$WhatIf = $false
)

$serviceTagId = "AzureCloud.$($Region.ToLower())"
Write-Host "Analyzing major $serviceTagId infrastructure ranges..." -ForegroundColor Yellow

# Read the service tags file
$content = Get-Content $ServiceTagsFile -Raw | ConvertFrom-Json

# Find the specified Azure region service tag
$regionService = $content.values | Where-Object { $_.id -eq $serviceTagId }

if (-not $regionService) {
    Write-Host "Service tag '$serviceTagId' not found!" -ForegroundColor Red
    Write-Host "Available Azure regions:" -ForegroundColor Cyan
    
    $azureRegions = $content.values | Where-Object { $_.id -like "AzureCloud.*" -and $_.id -notlike "*.*.*" } | 
                    Sort-Object id | Select-Object -First 20
    
    foreach ($azureRegion in $azureRegions) {
        $regionName = $azureRegion.id -replace "AzureCloud\.", ""
        Write-Host "  $regionName" -ForegroundColor White
    }
    exit 1
}

# Get IPv4 ranges and filter for major ranges (/15, /16, /17)
$ipv4Ranges = $regionService.properties.addressPrefixes | Where-Object { $_ -notmatch ':' }
$majorRanges = $ipv4Ranges | Where-Object { 
    $_ -match '/1[567]$'  # Ends with /15, /16, or /17
} | Sort-Object

Write-Host "Region: $($regionService.properties.region)" -ForegroundColor White
Write-Host "Major infrastructure ranges found: $($majorRanges.Count)" -ForegroundColor Green

# Get current Key Vault rules
Write-Host "Getting current Key Vault rules..." -ForegroundColor Cyan
try {
    $currentRules = az keyvault network-rule list --name $KeyVaultName --resource-group $ResourceGroupName | ConvertFrom-Json
    $existingRanges = $currentRules.ipRules | ForEach-Object { $_.value }
} catch {
    Write-Host "Failed to get Key Vault rules: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Current rules: $($existingRanges.Count)" -ForegroundColor White
foreach ($rule in $existingRanges) {
    if ($rule -match '/32$') {
        Write-Host "  Individual IP: $rule" -ForegroundColor Yellow
    } else {
        Write-Host "  Infrastructure: $rule" -ForegroundColor Green
    }
}

# Identify new ranges to add
$newRanges = $majorRanges | Where-Object { $_ -notin $existingRanges }
$alreadyHave = $majorRanges | Where-Object { $_ -in $existingRanges }

Write-Host "`nMajor ranges analysis for ${serviceTagId}:" -ForegroundColor Magenta
Write-Host "  Already configured: $($alreadyHave.Count)" -ForegroundColor Green
foreach ($range in $alreadyHave) {
    Write-Host "    Already have: $range" -ForegroundColor Green
}

Write-Host "  Need to add: $($newRanges.Count)" -ForegroundColor Yellow
if ($newRanges.Count -le 10) {
    foreach ($range in $newRanges) {
        Write-Host "    Will add: $range" -ForegroundColor Yellow
    }
} else {
    $newRanges | Select-Object -First 10 | ForEach-Object {
        Write-Host "    Will add: $_" -ForegroundColor Yellow
    }
    Write-Host "    ... and $($newRanges.Count - 10) more ranges" -ForegroundColor Gray
}

if ($newRanges.Count -eq 0) {
    Write-Host "All major infrastructure ranges are already configured!" -ForegroundColor Green
    exit 0
}

if ($WhatIf) {
    Write-Host "`nWHAT-IF MODE: Would add $($newRanges.Count) ranges for ${serviceTagId}" -ForegroundColor Cyan
    exit 0
}

# Confirm before adding many ranges
if ($newRanges.Count -gt 20) {
    Write-Host "`nAbout to add $($newRanges.Count) IP ranges to Key Vault." -ForegroundColor Yellow
    $confirm = Read-Host "Continue? (y/N)"
    if ($confirm -ne 'y' -and $confirm -ne 'Y') {
        Write-Host "Operation cancelled." -ForegroundColor Gray
        exit 0
    }
}

# Add new ranges
Write-Host "`nAdding major infrastructure ranges for ${serviceTagId}..." -ForegroundColor Green

$successCount = 0
$failCount = 0

foreach ($range in $newRanges) {
    try {
        Write-Host "  Adding: $range..." -NoNewline -ForegroundColor White
        az keyvault network-rule add --name $KeyVaultName --resource-group $ResourceGroupName --ip-address $range --output none
        Write-Host " SUCCESS" -ForegroundColor Green
        $successCount++
    }
    catch {
        Write-Host " FAILED: $_" -ForegroundColor Red
        $failCount++
    }
}

# Final summary
Write-Host "`nSummary for ${serviceTagId}:" -ForegroundColor Cyan
Write-Host "  Successfully added: $successCount ranges" -ForegroundColor Green
Write-Host "  Failed: $failCount ranges" -ForegroundColor Red

if ($successCount -gt 0) {
    $totalMajorRanges = $majorRanges.Count
    $nowConfigured = $alreadyHave.Count + $successCount
    
    Write-Host "`nCoverage:" -ForegroundColor Yellow
    Write-Host "  Major ranges configured: $nowConfigured out of $totalMajorRanges" -ForegroundColor White
    Write-Host "  This should handle most Microsoft Fabric connectivity scenarios in $($regionService.properties.region)" -ForegroundColor Green
}

Write-Host "`nUsage Examples:" -ForegroundColor Cyan
Write-Host "  # Preview changes for West US 2:" -ForegroundColor Gray
Write-Host "  .\Add-Major-Ranges-Region.ps1 -ServiceTagsFile ServiceTags.json -Region westus2 -KeyVaultName your-kv -ResourceGroupName your-rg -WhatIf" -ForegroundColor Gray