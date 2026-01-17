# Fix RealSense Drivers Script
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "RealSense Driver Repair Script" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[ERROR] This script requires administrator privileges!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please:" -ForegroundColor Yellow
    Write-Host "1. Right-click PowerShell" -ForegroundColor Yellow
    Write-Host "2. Select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host "3. Navigate to: $PWD" -ForegroundColor Yellow
    Write-Host "4. Run: .\fix_drivers.ps1" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

Write-Host "[INFO] Running with administrator privileges..." -ForegroundColor Green
Write-Host ""

# Find all RealSense devices with issues
$realsenseDevices = Get-PnpDevice -FriendlyName "*RealSense*" | Where-Object { $_.Status -ne "OK" }

if ($realsenseDevices.Count -eq 0) {
    Write-Host "[OK] All RealSense devices are working!" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now run: python check_camera.py" -ForegroundColor Cyan
    exit 0
}

Write-Host "[FOUND] $($realsenseDevices.Count) RealSense device(s) with driver issues:" -ForegroundColor Yellow
Write-Host ""

foreach ($device in $realsenseDevices) {
    Write-Host "  - $($device.FriendlyName) [Status: $($device.Status)]" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[ACTION] Attempting to update drivers..." -ForegroundColor Cyan
Write-Host ""

$successCount = 0
$failCount = 0

foreach ($device in $realsenseDevices) {
    Write-Host "Updating: $($device.FriendlyName)..." -ForegroundColor White
    
    try {
        # Try to update the driver
        $result = pnputil /scan-devices
        
        # Disable and re-enable the device to force driver reload
        Disable-PnpDevice -InstanceId $device.InstanceId -Confirm:$false -ErrorAction Stop
        Start-Sleep -Seconds 2
        Enable-PnpDevice -InstanceId $device.InstanceId -Confirm:$false -ErrorAction Stop
        Start-Sleep -Seconds 2
        
        # Check if it worked
        $updatedDevice = Get-PnpDevice -InstanceId $device.InstanceId
        if ($updatedDevice.Status -eq "OK") {
            Write-Host "  [SUCCESS] $($device.FriendlyName) is now OK!" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "  [WARNING] $($device.FriendlyName) still has issues" -ForegroundColor Yellow
            $failCount++
        }
    }
    catch {
        Write-Host "  [ERROR] Failed to update: $($_.Exception.Message)" -ForegroundColor Red
        $failCount++
    }
    Write-Host ""
}

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Results:" -ForegroundColor Cyan
Write-Host "  Success: $successCount" -ForegroundColor Green
Write-Host "  Failed: $failCount" -ForegroundColor $(if ($failCount -gt 0) { "Yellow" } else { "Green" })
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

if ($failCount -gt 0) {
    Write-Host "[NEXT STEPS]" -ForegroundColor Yellow
    Write-Host "1. Try restarting your computer" -ForegroundColor White
    Write-Host "2. Or manually update drivers in Device Manager:" -ForegroundColor White
    Write-Host "   - Open Device Manager (devmgmt.msc)" -ForegroundColor White
    Write-Host "   - Find devices with yellow warning icons" -ForegroundColor White
    Write-Host "   - Right-click -> Update Driver -> Search automatically" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "[COMPLETE] You can now run: python check_camera.py" -ForegroundColor Green
    Write-Host ""
}

pause

