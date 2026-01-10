@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%\.."

echo Running YOLOv8 training (train_yellow_ball.py)...
python models\code\train_yellow_ball.py
if %errorlevel% neq 0 (
  echo Training failed with exit code %errorlevel%.
  popd
  pause
  exit /b %errorlevel%
)

echo Running ONNX export (export_onnx.py)...
python models\code\export_onnx.py
if %errorlevel% neq 0 (
  echo Export failed with exit code %errorlevel%.
  popd
  pause
  exit /b %errorlevel%
)

echo Done.
popd
pause
