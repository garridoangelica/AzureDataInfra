param(
    [Parameter(Mandatory=$true)]
    [string]$ServiceTagsJsonPath
)

Write-Host "Extracting US-based Microsoft Fabric (PowerBI) IP ranges..." -ForegroundColor Green

try {
    # Read and parse the service tags JSON
    $serviceTagsContent = Get-Content -Path $ServiceTagsJsonPath -Raw
    $serviceTags = $serviceTagsContent | ConvertFrom-Json
    
    # Find all US PowerBI service tags
    $usPowerBITags = $serviceTags.values | Where-Object { 
        $_.name -match "PowerBI\.(Central|East|North|South|West).*US" -or 
        $_.name -eq "PowerBI.WestUS2" -or 
        $_.name -eq "PowerBI.WestUS3"
    }
    
    if ($usPowerBITags.Count -eq 0) {
        Write-Error "No US PowerBI service tags found"
        exit 1
    }
    
    Write-Host "Found $($usPowerBITags.Count) US PowerBI regions:" -ForegroundColor Cyan
    $usPowerBITags | ForEach-Object { 
        Write-Host "  $($_.name) - $($_.properties.addressPrefixes.Count) ranges" -ForegroundColor White
    }
    Write-Host ""
    
    # Collect all US IPv4 ranges
    $allUSRanges = @()
    $regionSummary = @()
    
    foreach ($tag in $usPowerBITags) {
        $ipv4Ranges = $tag.properties.addressPrefixes | Where-Object { $_ -notmatch ":" }
        $allUSRanges += $ipv4Ranges
        
        $regionSummary += [PSCustomObject]@{
            Region = $tag.name
            IPv4Count = $ipv4Ranges.Count
            IPv6Count = ($tag.properties.addressPrefixes.Count - $ipv4Ranges.Count)
        }
    }
    
    # Remove duplicates
    $uniqueUSRanges = $allUSRanges | Sort-Object | Get-Unique
    
    Write-Host "Total unique IPv4 ranges for US regions: $($uniqueUSRanges.Count)" -ForegroundColor Green
    Write-Host ""
    
    # Export files
    $timestamp = Get-Date -Format 'yyyyMMdd'
    $csvPath = "Fabric_US_IP_Ranges_$timestamp.csv"
    $txtPath = "Fabric_US_IP_Ranges_$timestamp.txt"
    $summaryPath = "Fabric_US_Summary_$timestamp.csv"
    
    # Create detailed CSV with region info
    $csvContent = @()
    $csvContent += "IP_Range,Region,Service"
    foreach ($tag in $usPowerBITags) {
        $ipv4Ranges = $tag.properties.addressPrefixes | Where-Object { $_ -notmatch ":" }
        $ipv4Ranges | ForEach-Object { 
            $csvContent += "$_,$($tag.name),Microsoft Fabric (PowerBI)" 
        }
    }
    $csvContent | Out-File -FilePath $csvPath -Encoding UTF8
    
    # Create simple text file with unique ranges
    $uniqueUSRanges | Out-File -FilePath $txtPath -Encoding UTF8
    
    # Create summary
    $regionSummary | Export-Csv -Path $summaryPath -NoTypeInformation -Encoding UTF8
    
    Write-Host "Files created:"
    Write-Host "  Detailed CSV: $csvPath" -ForegroundColor Cyan
    Write-Host "  Simple TXT: $txtPath" -ForegroundColor Cyan
    Write-Host "  Region Summary: $summaryPath" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "Region Summary:" -ForegroundColor Yellow
    $regionSummary | Format-Table -AutoSize
    
    Write-Host "First 20 IP ranges:" -ForegroundColor Yellow
    $uniqueUSRanges | Select-Object -First 20 | ForEach-Object { Write-Host "  $_" }
    if ($uniqueUSRanges.Count -gt 20) {
        Write-Host "  ... and $($uniqueUSRanges.Count - 20) more" -ForegroundColor Gray
    }
    
    Write-Host "`nTo configure Azure Key Vault firewall for US regions only:" -ForegroundColor Green
    Write-Host "1. Go to Azure Portal > Key Vault > Networking" -ForegroundColor White
    Write-Host "2. Under 'Firewalls and virtual networks', select 'Selected networks'" -ForegroundColor White
    Write-Host "3. Add the IP ranges from: $txtPath" -ForegroundColor White
    Write-Host "4. This will allow Fabric access from US regions only" -ForegroundColor White
    
} catch {
    Write-Error "Error processing service tags: $_"
}