# NeuroKit2 皮电数据分析

## 简介

这是使用NeuroKit2库分析皮电(EDA)数据的工具集。NeuroKit2是一个强大的Python库，专门用于生理信号处理，包括皮电、心电图、呼吸等。

## 功能特点

- **专业算法**: 使用NeuroKit2提供的专业生理信号处理算法
- **自动化处理**: 自动清洗信号、分解成分、检测SCR
- **详细指标**: 提供丰富的SCR特征指标
- **可视化**: 生成专业的EDA分析图表
- **批量处理**: 支持批量处理多个数据文件

## 安装

```bash
# 运行安装脚本
install_neurokit2.bat

# 或手动安装
pip install neurokit2
```

## 使用方法

### 方法一: 快速演示

运行演示脚本，查看NeuroKit2的基本功能:

```bash
python nk_demo.py
```

演示脚本会加载一个EDA数据文件，并使用NeuroKit2进行处理，生成两个图表:
- `nk_eda_raw.png`: 原始信号和清洗后信号
- `nk_eda_processed.png`: 完整的EDA分析图表

### 方法二: 批量处理

使用批量处理脚本分析多个数据文件:

```bash
# 运行批量处理脚本
run_neurokit_analysis.bat

# 或直接运行Python脚本
python nk_eda_analysis.py
```

## 输出结果

批量处理会在 `nk_results/` 文件夹中生成以下文件:

### 每个数据文件的结果
- `[文件名]_signals.csv`: 包含原始信号、清洗后信号、相位成分、强度成分等
- `[文件名]_minute_stats.csv`: 每分钟的SCL和SCR统计
- `[文件名]_scr_features.csv`: SCR特征参数(幅度、上升时间、半恢复时间等)
- `[文件名]_plot.png`: 可视化图表

### 汇总结果
- `nk_batch_summary.csv`: 所有文件的汇总统计
- `nk_statistical_report.txt`: 详细的统计分析报告

## NeuroKit2 vs 自定义实现

相比之前的自定义实现，使用NeuroKit2的优势:

1. **专业算法**: 使用经过同行评审的专业算法
2. **全面分析**: 提供更多生理指标和特征参数
3. **标准化**: 结果符合生理学研究标准
4. **可靠性**: 由专业社区维护和更新

## 参考资料

- [NeuroKit2 官方文档](https://neuropsychology.github.io/NeuroKit/)
- [EDA 分析指南](https://neuropsychology.github.io/NeuroKit/examples/eda_analysis.html)
- [SCR 特征提取](https://neuropsychology.github.io/NeuroKit/functions/eda.html#neurokit2.eda.eda_scr_features)
