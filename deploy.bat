@echo off
REM AI Script Studio - Windows Deployment Script
REM Automated deployment to Streamlit Cloud

echo ====================================
echo 🎬 AI Script Studio - Deploy Assistant
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if Git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git is not installed or not in PATH
    echo Please install Git and try again
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed
echo.

REM Run the Python deployment script
echo 🚀 Running deployment preparation...
python deploy.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Deployment preparation failed
    echo Check the error messages above
    pause
    exit /b 1
)

echo.
echo ✅ Deployment preparation completed successfully!
echo.
echo 📋 QUICK REFERENCE:
echo.
echo 1. Go to: https://share.streamlit.io
echo 2. Sign in with GitHub
echo 3. Click "New app" and select your repo
echo 4. Set main file: app.py
echo 5. Add secret: DEEPSEEK_API_KEY = "your_key"
echo 6. Click Deploy!
echo.
echo 📚 See STREAMLIT_DEPLOYMENT.md for detailed instructions
echo.
pause
