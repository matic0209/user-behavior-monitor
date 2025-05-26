@echo off
echo Initializing Git repository...

git init
git add .
git commit -m "Initial commit: User Behavior Monitor"

echo.
echo Please enter your GitHub repository URL (e.g., https://github.com/username/user-behavior-monitor.git):
set /p repo_url=

git remote add origin %repo_url%
git branch -M main
git push -u origin main

echo.
echo Repository has been initialized and pushed to GitHub.
pause 