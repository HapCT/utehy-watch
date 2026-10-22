# Creates a Windows scheduled task that runs watch.py every 2 hours and when you log in.
# Run:  powershell -ExecutionPolicy Bypass -File dat-lich.ps1
$python = Join-Path $PSScriptRoot '.venv\Scripts\pythonw.exe'
$script = Join-Path $PSScriptRoot 'watch.py'
if (-not (Test-Path $python)) { Write-Error "Khong thay $python. Hay cai dat theo README truoc."; exit 1 }

$action = New-ScheduledTaskAction -Execute $python -Argument "`"$script`"" -WorkingDirectory $PSScriptRoot
$every2h = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Hours 2)
$atLogon = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName 'UTEHY Watch' -Action $action -Trigger $every2h, $atLogon -Settings $settings `
    -Description 'Kiem tra cong thong tin UTEHY moi 2 tieng va khi dang nhap Windows.' -Force | Out-Null
Write-Host 'Da dat lich: UTEHY Watch chay moi 2 tieng va moi khi ban dang nhap Windows.'
