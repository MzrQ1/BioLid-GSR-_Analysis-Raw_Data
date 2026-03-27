@echo off
echo NeuroKit2 EDA分析程序
echo.

REM 检查虚拟环境是否存在
if not exist "eda_analysis_env\Scripts\activate.bat" (
    echo 虚拟环境不存在，正在创建...
    call setup_environment.bat
)

REM 检查NeuroKit2是否已安装
call eda_analysis_env\Scripts\activate.bat
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
