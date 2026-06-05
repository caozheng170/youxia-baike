@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "GIT=C:\Program Files\Git\cmd\git.exe"
set "GH=C:\Users\pgrad\AppData\Local\Microsoft\WinGet\Packages\GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\gh.exe"

echo.
echo ========================================
echo   推送项目到 GitHub
echo ========================================
echo.

"%GH%" auth status >nul 2>&1
if errorlevel 1 (
  echo [1/2] 尚未登录 GitHub，即将打开登录流程...
  echo       按提示选择: GitHub.com - HTTPS - Login with browser
  echo.
  "%GH%" auth login
  if errorlevel 1 (
    echo 登录失败，请重试。
    pause
    exit /b 1
  )
)

echo.
echo [2/2] 创建 GitHub 仓库并推送...
echo       仓库名默认: youxia-baike （可在下面改成你想要的）
echo.

set /p REPO_NAME=输入仓库名 [默认 youxia-baike]: 
if "%REPO_NAME%"=="" set REPO_NAME=youxia-baike

"%GH%" repo create %REPO_NAME% --public --source=. --remote=origin --push
if errorlevel 1 (
  echo.
  echo 如果提示仓库已存在，可改个名字，或手动添加 remote 后 push:
  echo   "%GIT%" remote add origin https://github.com/你的用户名/%REPO_NAME%.git
  echo   "%GIT%" push -u origin main
  pause
  exit /b 1
)

echo.
echo 完成！在浏览器打开仓库:
"%GH%" repo view %REPO_NAME% --json url -q .url
echo.
pause
