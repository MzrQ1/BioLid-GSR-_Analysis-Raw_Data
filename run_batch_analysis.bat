@echo off
echo 皮电数据批量分析程序
echo.

REM 检查虚拟环境是否存在
if not exist "eda_analysis_env\Scripts\activate.bat" (
    echo 虚拟环境不存在，正在创建...
    call setup_environment.bat
)

REM 激活虚拟环境
echo 激活虚拟环境...
call eda_analysis_env\Scripts\activate.bat

REM 运行批量分析
echo 开始批量分析...
python batch_eda_analysis.py

echo.
echo 批量分析完成！查看 batch_eda_results 文件夹中的结果。
pause
