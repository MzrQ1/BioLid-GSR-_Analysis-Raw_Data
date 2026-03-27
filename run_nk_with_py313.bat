@echo off
echo NeuroKit2 EDA分析程序 (Python 3.13版本)
echo.

REM 检查Python 3.13虚拟环境是否存在
if not exist "py313_env\Scripts\activate.bat" (
    echo Python 3.13虚拟环境不存在，正在创建...
    call setup_py312_env.bat
)

REM 激活Python 3.13虚拟环境
echo 激活Python 3.13虚拟环境...
call py313_env\Scripts\activate.bat

REM 检查Python版本
python --version

REM 检查NeuroKit2是否已安装
python -c "import sys; sys.exit(0 if 'neurokit2' in sys.modules or any('neurokit2' in m for m in sys.modules) else 1)" 2>nul
if errorlevel 1 (
    echo NeuroKit2未安装，正在安装...
    pip install neurokit2
)

REM 运行分析
echo 开始使用NeuroKit2分析EDA数据...
python nk_eda_analysis.py

echo.
echo 分析完成！查看 nk_results 文件夹中的结果。
pause
