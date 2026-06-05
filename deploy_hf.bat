@echo off
cd /d "%~dp0"
echo.
echo ========================================
echo   上传后端到 Hugging Face Space
echo   caozheng/youxia
echo ========================================
echo.
echo 接下来会提示粘贴 HF 令牌 (hf_...)
echo 粘贴时屏幕不显示字符，这是正常的，贴完按回车即可。
echo.
.\.venv\Scripts\python.exe deploy_hf.py
echo.
pause
