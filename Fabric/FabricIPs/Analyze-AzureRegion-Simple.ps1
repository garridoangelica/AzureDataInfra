# Analyze Azure Region Infrastructure Ranges (Simple Version)
# This script analyzes IPv4 ranges in any Azure region's service tag

param(
    [Parameter(Mandatory)]
    [string]$ServiceTagsFile,
    
    [Parameter(Mandatory)]
    [string]$Region
)

$serviceTagId = "AzureCloud.$($Region.ToLower())"
Write-Host "Analyzing $serviceTagId service tag..." -ForegroundColor Yellow

# Read the service tags file
$content = Get-Content $ServiceTagsFile -Raw | ConvertFrom-Json

# Find the specified Azure region service tag
$regionService = $content.values | Where-Object { $_.id -eq $serviceTagId }

if (-not $regionService) {
    Write-Host "Service tag '$serviceTagId' not found!" -ForegroundColor Red
    Write-Host "Available Azure regions (first 20):" -ForegroundColor Cyan
    
    $azureRegions = $content.values | Where-Object { $_.id -like "AzureCloud.*" -and $_.id -notlike "*.*.*" } | 
                    Sort-Object id | Select-Object -First 20
    
    foreach ($azureRegion in $azureRegions) {
        $regionName = $azureRegion.id -replace "AzureCloud\.", ""
        Write-Host "  $regionName" -ForegroundColor White
    }
    exit 1
}

$addressPrefixes = $regionService.properties.addressPrefixes

# Filter only IPv4 ranges (exclude IPv6)
$ipv4Ranges = $addressPrefixes | Where-Object { $_ -notmatch ':' }
$ipv6Ranges = $addressPrefixes | Where-Object { $_ -match ':' }

# Get major ranges (/15, /16, /17)
$majorRanges = $ipv4Ranges | Where-Object { $_ -match '/1[567]$' } | Sort-Object

Write-Host "$serviceTagId Summary:" -ForegroundColor Green
Write-Host "  Region: $($regionService.properties.region)" -ForegroundColor White
Write-Host "  Total IP ranges: $($addressPrefixes.Count)" -ForegroundColor White
Write-Host "  IPv4 ranges: $($ipv4Ranges.Count)" -ForegroundColor White
Write-Host "  IPv6 ranges: $($ipv6Ranges.Count)" -ForegroundColor White
Write-Host "  Major ranges (/15,/16,/17): $($majorRanges.Count)" -ForegroundColor Cyan

Write-Host "`nFirst 10 IPv4 ranges:" -ForegroundColor Cyan
$ipv4Ranges | Select-Object -First 10 | ForEach-Object {
    Write-Host "  $_" -ForegroundColor Gray
}

Write-Host "`nMajor Infrastructure Ranges (first 15):" -ForegroundColor Yellow
$majorRanges | Select-Object -First 15 | ForEach-Object {
    Write-Host "  $_" -ForegroundColor White
}
if ($majorRanges.Count -gt 15) {
    Write-Host "  ... and $($majorRanges.Count - 15) more major ranges" -ForegroundColor Gray
}

Write-Host "`nUsage Examples:" -ForegroundColor Cyan
Write-Host "  # Analyze West US 2:" -ForegroundColor Gray
Write-Host "  .\Analyze-AzureRegion-Simple.ps1 -ServiceTagsFile ServiceTags.json -Region westus2" -ForegroundColor Gray
Write-Host "  # Test with the region-flexible add script:" -ForegroundColor Gray  
Write-Host "  .\Add-Major-Ranges-Region.ps1 -ServiceTagsFile ServiceTags.json -Region $Region -KeyVaultName your-kv -ResourceGroupName your-rg -WhatIf" -ForegroundColor Gray