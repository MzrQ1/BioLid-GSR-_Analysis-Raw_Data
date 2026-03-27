@echo off
echo 创建Python 3.13虚拟环境...

REM 删除旧的虚拟环境（如果存在）
if exist "py313_env" (
    echo 删除旧的虚拟环境...
    rmdir /s /q py313_env
)

REM 创建新的虚拟环境
echo 创建新的Python 3.13虚拟环境...
py -3.13 -m venv py313_env

REM 激活虚拟环境
call py313_env\Scripts\activate.bat

REM 升级pip
python -m pip install --upgrade pip

REM 安装依赖
pip install pandas numpy matplotlib scipy
pip install neurokit2

echo.
echo Python 3.13虚拟环境创建完成！
echo.
echo 使用方法：
echo 1. 激活环境：py313_env\Scripts\activate.bat
echo 2. 运行分析：python nk_eda_analysis.py
echo 3. 退出环境：deactivate
echo.
pause
