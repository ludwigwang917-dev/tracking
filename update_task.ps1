$action = New-ScheduledTaskAction -Execute "python" -Argument "D:\hermes\MODS\MOD004\query_all.py" -WorkingDirectory "D:\hermes\MODS\MOD004"
$trigger = New-ScheduledTaskTrigger -Daily -At 9am
Register-ScheduledTask -TaskName "MOD004_Daily" -Action $action -Trigger $trigger -Force
Write-Host "Task MOD004_Daily created — 每天 9:00 自动查三大船司"
