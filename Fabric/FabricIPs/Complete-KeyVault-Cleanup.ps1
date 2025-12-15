# Complete Key Vault Cleanup Script
# This script will remove ALL IP rules and add only essential ones

param(
    [Parameter(Mandatory)]
    [string]$KeyVaultName,
    
    [Parameter(Mandatory)]
    [string]$ResourceGroupName,
    
    [string]$UserIP = "99.137.14.9/32",
    [string]$AzureEastUSRange = "4.236.128.0/17"
)

Write-Host "Starting complete Key Vault firewall cleanup..." -ForegroundColor Yellow

# Get current rules
Write-Host "Getting current IP rules..." -ForegroundColor Cyan
$currentRules = az keyvault network-rule list --name $KeyVaultName --resource-group $ResourceGroupName | ConvertFrom-Json

$ipRulesCount = $currentRules.ipRules.Count
Write-Host "Found $ipRulesCount IP rules to remove" -ForegroundColor White

if ($ipRulesCount -gt 0) {
    Write-Host "Removing all existing IP rules..." -ForegroundColor Red
    
    # Remove each IP rule individually
    $removedCount = 0
    foreach ($rule in $currentRules.ipRules) {
        try {
            az keyvault network-rule remove --name $KeyVaultName --resource-group $ResourceGroupName --ip-address $rule.value
            $removedCount++
            Write-Host "  Removed: $($rule.value)" -ForegroundColor Gray
        }
        catch {
            Write-Host "  Failed to remove: $($rule.value)" -ForegroundColor Yellow
        }
    }
    Write-Host "Removed $removedCount IP rules" -ForegroundColor Green
}

# Add essential IP ranges
Write-Host "Adding essential IP ranges..." -ForegroundColor Green

try {
    az keyvault network-rule add --name $KeyVaultName --resource-group $ResourceGroupName --ip-address $UserIP
    Write-Host "  Added: Your IP ($UserIP)" -ForegroundColor Green
}
catch {
    Write-Host "  Failed to add your IP: $_" -ForegroundColor Yellow
}

try {
    az keyvault network-rule add --name $KeyVaultName --resource-group $ResourceGroupName --ip-address $AzureEastUSRange
    Write-Host "  Added: Azure East US Infrastructure ($AzureEastUSRange)" -ForegroundColor Green
}
catch {
    Write-Host "  Failed to add Azure range: $_" -ForegroundColor Yellow
}

# Verify final state
Write-Host "Final verification..." -ForegroundColor Cyan
$finalRules = az keyvault network-rule list --name $KeyVaultName --resource-group $ResourceGroupName | ConvertFrom-Json
$finalCount = $finalRules.ipRules.Count

Write-Host "Cleanup complete!" -ForegroundColor Green
Write-Host "Final IP rules count: $finalCount" -ForegroundColor White

if ($finalCount -eq 2) {
    Write-Host "Perfect! Only essential rules remain:" -ForegroundColor Green
    foreach ($rule in $finalRules.ipRules) {
        Write-Host "  $($rule.value)" -ForegroundColor White
    }
} else {
    Write-Host "Expected 2 rules but found $finalCount" -ForegroundColor Yellow
    Write-Host "Current rules:" -ForegroundColor White
    foreach ($rule in $finalRules.ipRules) {
        Write-Host "  $($rule.value)" -ForegroundColor Gray
    }
}