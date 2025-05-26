#!/bin/bash

echo "Initializing Git repository..."

# 初始化Git仓库
git init
git add .
git commit -m "Initial commit: User Behavior Monitor"

# 提示用户输入GitHub仓库URL
echo ""
echo "Please enter your GitHub repository URL (e.g., https://github.com/username/user-behavior-monitor.git):"
read repo_url

# 添加远程仓库并推送
git remote add origin "$repo_url"
git branch -M main
git push -u origin main

echo ""
echo "Repository has been initialized and pushed to GitHub." 