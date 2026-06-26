@echo off
REM ============================================================================
REM SUN-DIC 环境自动安装脚本 (Windows CMD)
REM
REM 用法:
REM   cmd:   setup_env.bat
REM
REM 可选环境变量:
REM   CONDA_PATH=C:\Users\xxx\anaconda3    (如果 conda 不在 PATH)
REM   ENV_NAME=sundic                       (环境名, 默认 sundic)
REM ============================================================================
setlocal enabledelayedexpansion

if not defined ENV_NAME set ENV_NAME=sundic
set PYTHON_VER=3.11

REM --- detect conda -----------------------------------------------------------
if not defined CONDA_PATH (
    REM try PATH
    where conda >nul 2>&1
    if !errorlevel! equ 0 (
        set CONDA_EXE=conda
    ) else (
        REM common install paths
        if exist "%USERPROFILE%\anaconda3\Scripts\conda.exe" (
            set CONDA_PATH=%USERPROFILE%\anaconda3
        ) else if exist "%USERPROFILE%\miniconda3\Scripts\conda.exe" (
            set CONDA_PATH=%USERPROFILE%\miniconda3
        ) else if exist "C:\ProgramData\anaconda3\Scripts\conda.exe" (
            set CONDA_PATH=C:\ProgramData\anaconda3
        )
    )
)
if defined CONDA_PATH set "CONDA_EXE=%CONDA_PATH%\Scripts\conda.exe"
if not defined CONDA_EXE (
    echo ERROR: conda not found. Set CONDA_PATH or install Anaconda/Miniconda.
    exit /b 1
)
echo Using conda: %CONDA_EXE%

REM --- create environment -----------------------------------------------------
echo.
echo === Step 1/4: Creating conda environment '%ENV_NAME%' (Python %PYTHON_VER%) ===
call "%CONDA_EXE%" create -n %ENV_NAME% python=%PYTHON_VER% -y

REM find python in new env
for /f "usebackq tokens=*" %%i in (`call "%CONDA_EXE%" run -n %ENV_NAME% python -c "import sys; print(sys.executable)"`) do set ENV_PYTHON=%%i
echo Python: %ENV_PYTHON%

REM --- install dependencies ---------------------------------------------------
echo.
echo === Step 2/4: Installing SUN-DIC dependencies ===
call "%ENV_PYTHON%" -m pip install numpy opencv-python-headless scikit-image scipy matplotlib pandas natsort numba msgpack-numpy ray

REM --- install PyQt6 6.5.3 ----------------------------------------------------
echo.
echo === Step 3/4: Installing PyQt6 6.5.3 ===
call "%ENV_PYTHON%" -m pip install PyQt6==6.5.3 PyQt6-Qt6==6.5.3
call "%ENV_PYTHON%" -c "from PyQt6.QtCore import Qt; print('PyQt6 OK')"

REM --- install SUN-DIC --------------------------------------------------------
echo.
echo === Step 4/4: Installing SUN-DIC ===
call "%ENV_PYTHON%" -m pip install -e "%~dp0."
call "%ENV_PYTHON%" -m pip install PyQt6-Qt6==6.5.3 --quiet

REM --- verify -----------------------------------------------------------------
echo.
echo === Verification ===
call "%ENV_PYTHON%" -c "from PyQt6.QtWidgets import QApplication; from sundic.gui.mainWindow import main; print('SUN-DIC OK!')"

echo.
echo ==============================================
echo   Environment '%ENV_NAME%' is ready.
echo   Activate:   conda activate %ENV_NAME%
echo   GUI:        sundic
echo ==============================================
endlocal
