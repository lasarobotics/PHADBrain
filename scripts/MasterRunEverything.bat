@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem Admin check
net session >nul 2>&1
if %errorlevel% neq 0 (
  color 4F
  echo Administrator rights required. Re-run this script as admin.
  exit /b 1
)

color 0D
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%\.."

set "STAMP=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "STAMP=%STAMP: =0%"
set "LOG_DIR=%cd%\logs\%STAMP%"
set "LOG_FILE=%LOG_DIR%\run.log"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

set "PYTHON=python"

:menu
cls
echo ===========================================================================================
echo Master Run Everything Script
echo Logs: %LOG_FILE%
echo ===========================================================================================
echo Select an option:
echo [95m1[0m ^) Run vision_fusion.py
echo [95m2[0m ^) Run limelight_pose.py
echo [95m3[0m ^) Full Run (current order)
echo [95mQ[0m ^) Quit
echo ____________________________________________________________________________________________
choice /c 123Q /n /m "Select option: "
if errorlevel 4 goto end
if errorlevel 3 goto run_both
if errorlevel 2 goto run_lime
if errorlevel 1 goto run_vision

:run_vision
start "vision_fusion.py" powershell -NoProfile -Command ^
  "$OutputEncoding=[Console]::OutputEncoding;" ^
  "$python='%PYTHON%';" ^
  "$ts=Get-Date -Format 'yyyy-MM-dd HH:mm:ss';" ^
  "Write-Host \"[$ts] Running vision_fusion.py\";" ^
  " \"[$ts] Running vision_fusion.py\" | Tee-Object -FilePath '%LOG_FILE%' -Append;" ^
  "& $python 'brain\\processing\\fusion\\vision_fusion.py' 2>&1 | Tee-Object -FilePath '%LOG_FILE%' -Append;" ^
  "Write-Host \"Finished vision_fusion.py. Close this window when the code is done running.\";" ^ -ForegroundColor Red
  "cmd /k"
goto menu

:run_lime
start "limelight_pose.py" powershell -NoProfile -Command ^
  "$OutputEncoding=[Console]::OutputEncoding;" ^
  "$python='%PYTHON%';" ^
  "$ts=Get-Date -Format 'yyyy-MM-dd HH:mm:ss';" ^
  "Write-Host \"[$ts] Running limelight_pose.py\";" ^
  " \"[$ts] Running limelight_pose.py\" | Tee-Object -FilePath '%LOG_FILE%' -Append;" ^
  "& $python 'brain\\processing\\fusion\\limelight_pose.py' 2>&1 | Tee-Object -FilePath '%LOG_FILE%' -Append;" ^
  "Write-Host \"Finished limelight_pose.py. Close this window when is done running.\";" ^ -ForegroundColor Red
  "cmd /k"
goto menu

:run_both
set "TSMSG=[%date% %time%] Full run: vision_fusion.py and limelight_pose.py"
echo %TSMSG% >>"%LOG_FILE%"
start "vision_fusion.py" powershell -NoProfile -Command ^
  "$OutputEncoding=[Console]::OutputEncoding;" ^
  "$python='%PYTHON%';" ^
  "$ts=Get-Date -Format 'yyyy-MM-dd HH:mm:ss';" ^
  "Write-Host \"[$ts] Running vision_fusion.py\";" ^
  " \"[$ts] Running vision_fusion.py\" | Tee-Object -FilePath '%LOG_FILE%' -Append;" ^
  "& $python 'brain\\processing\\fusion\\vision_fusion.py' 2>&1 | Tee-Object -FilePath '%LOG_FILE%' -Append;" ^
  "Write-Host \"Finished vision_fusion.py. Close this window when ready.\";" ^
  "cmd /k"
start "limelight_pose.py" powershell -NoProfile -Command ^
  "$OutputEncoding=[Console]::OutputEncoding;" ^
  "$python='%PYTHON%';" ^
  "$ts=Get-Date -Format 'yyyy-MM-dd HH:mm:ss';" ^
  "Write-Host \"[$ts] Running limelight_pose.py\";" ^
  " \"[$ts] Running limelight_pose.py\" | Tee-Object -FilePath '%LOG_FILE%' -Append;" ^
  "& $python 'brain\\processing\\fusion\\limelight_pose.py' 2>&1 | Tee-Object -FilePath '%LOG_FILE%' -Append;" ^
  "Write-Host \"Finished limelight_pose.py. Close this window when ready.\";" ^
  "cmd /k"
goto menu

:end
popd
endlocal
