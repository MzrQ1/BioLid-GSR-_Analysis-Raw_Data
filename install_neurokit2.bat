@echo off
echo 安装NeuroKit2库...

REM 激活虚拟环境
call eda_analysis_env\Scripts\activate.bat

REM 安装NeuroKit2
pip install neurokit2

echo.
echo NeuroKit2安装完成！
pause
