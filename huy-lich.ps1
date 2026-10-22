# Removes the scheduled task created by dat-lich.ps1.
# Run:  powershell -ExecutionPolicy Bypass -File huy-lich.ps1
Unregister-ScheduledTask -TaskName 'UTEHY Watch' -Confirm:$false
Write-Host 'Da huy lich UTEHY Watch.'
