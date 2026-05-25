$pythonw = "C:\Users\Rv\.gemini\antigravity\scratch\jarvis-voice-agent\venv\Scripts\pythonw.exe"
$script  = "C:\Users\Rv\.gemini\antigravity\scratch\jarvis-voice-agent\watcher.py"
$action  = New-ScheduledTaskAction -Execute $pythonw -Argument "`"$script`"" -WorkingDirectory "C:\Users\Rv\.gemini\antigravity\scratch\jarvis-voice-agent"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit 0 -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Limited
Register-ScheduledTask -TaskName "JarvisWatcher" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force
Write-Host "JarvisWatcher task created successfully!"
