@echo off
echo ============================================
echo         JARVIS - Deactivate Watcher
echo ============================================
echo.
echo Stopping background Watcher process...
taskkill /F /IM pythonw.exe 2>nul
echo.
echo Removing JARVIS Watcher from Windows Startup...
powershell -Command "Remove-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'JarvisWatcher' -ErrorAction SilentlyContinue"
echo.
echo JARVIS Watcher has been fully deactivated.
echo It is no longer listening and will not start on boot.
echo.
pause
