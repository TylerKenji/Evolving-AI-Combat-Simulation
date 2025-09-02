@echo off
echo ======================================
echo Battle AI Development Environment Setup
echo ======================================

echo.
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo Python found!
python --version

echo.
echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo Failed to create virtual environment.
    pause
    exit /b 1
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Creating logs directory...
mkdir logs 2>nul

echo.
echo ======================================
echo Setup completed successfully!
echo ======================================
echo.
echo To activate the environment in the future, run:
echo   venv\Scripts\activate.bat
echo.
echo To run tests:
echo   pytest tests/
echo.
echo To start development, see TASK_BREAKDOWN.md
echo ======================================

pause
