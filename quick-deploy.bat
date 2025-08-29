@echo off
echo ====================================
echo AI Script Studio - Quick Deploy
echo ====================================
echo.
echo Make sure you have:
echo 1. Created a GitHub repo named 'ai-script-studio'
echo 2. Have your GitHub username ready
echo.
set /p username="Enter your GitHub username: "
echo.
echo Running git commands...
echo.

git init
git add .
git commit -m "AI Script Studio - Initial deployment"
git branch -M main
git remote add origin https://github.com/%username%/ai-script-studio.git
git push -u origin main

echo.
echo ====================================
echo Files uploaded to GitHub!
echo Now go to: https://share.streamlit.io
echo And deploy your app!
echo ====================================
pause
