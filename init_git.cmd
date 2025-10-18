@echo off
echo Initializing Git repository...
git init
echo Adding files...
git add .
echo Creating commit...
git commit -m "feat: initial release v0.1.0"
echo.
echo Git repository initialized!
echo.
echo Next steps:
echo 1. Create repository on GitHub: https://github.com/new
echo 2. Name: universal-parser
echo 3. Don't add README, .gitignore, license
echo 4. Run these commands:
echo    git remote add origin https://github.com/YOUR_USERNAME/universal-parser.git
echo    git branch -M main
echo    git push -u origin main
echo.
pause
