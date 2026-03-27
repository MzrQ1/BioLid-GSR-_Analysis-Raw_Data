@echo off
echo 创建皮电数据分析虚拟环境...

REM 创建虚拟环境
python -m venv eda_analysis_env

REM 激活虚拟环境
call eda_analysis_env\Scripts\activate.bat

REM 升级pip
python -m pip install --upgrade pip

REM 安装依赖
pip install pandas numpy matplotlib scipy

echo.
echo 虚拟环境创建完成！
echo.
echo 使用方法：
echo 1. 激活环境：eda_analysis_env\Scripts\activate.bat
echo 2. 运行分析：python eda_analysis.py
echo 3. 退出环境：deactivate
echo.
pause
