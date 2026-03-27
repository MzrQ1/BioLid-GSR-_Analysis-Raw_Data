# 皮电数据分析程序

## 功能描述
本程序用于分析皮电传感器数据，提取每分钟的皮肤电导水平(SCL)和皮肤电导反应(SCR)统计信息。

### 主要功能
- **SCL分析**: 计算每分钟的平均皮电导水平
- **SCR检测**: 自动检测SCR峰值并统计每分钟数量
- **信号处理**: 低通滤波去除噪声
- **可视化**: 生成综合分析图表

## 项目结构

```
皮电/
├── data/                          # 原始实验用户数据目录
│   ├── female/                    # 女性被试数据
│   │   ├── 被试8.17-13女阮湘婷23岁/
│   │   ├── 被试8.19-16女金可成26岁/
│   │   └── ...                    # 其他女性被试
│   └── male/                      # 男性被试数据
│       ├── 被试8.17-8男朱俊衡25岁/
│       ├── 被试8.19-15男张宇凡24岁/
│       └── ...                    # 其他男性被试
├── eda_analysis.py                # 单文件分析脚本
├── batch_eda_analysis.py          # 批量处理脚本
├── batch_config.json              # 批量处理配置文件
├── activate_env.bat               # 激活虚拟环境脚本
├── eda_analysis_env/              # Python虚拟环境目录
└── README.md                      # 项目说明文档
```

### 数据文件说明
- **CSV数据文件**: 包含两列数据
  - 第一列：时间戳(毫秒)
  - 第二列：GSR值(皮电响应值)
- **文件命名规则**:
  - `data_YYYYMMDD_HHMMSS.csv` - 常规实验数据
  - `眼罩data_YYYYMMDD_HHMMSS.csv` - 眼罩实验条件数据
- **音频文件**: `.m4a` 格式，记录实验过程中的音频信息

## 使用方法

### 方法一：单文件分析

#### 1. 激活虚拟环境
```bash
activate_env.bat
```

#### 2. 运行单文件分析
```bash
python eda_analysis.py
```
程序会自动查找当前目录下以 `data_` 开头的CSV文件进行分析。

### 方法二：批量处理（推荐）

#### 1. 配置批量处理参数
编辑 `batch_config.json` 文件：
```json
{
    "input_settings": {
        "input_folder": "data/female/被试8.17-13女阮湘婷23岁",  // 修改为实际数据路径
        "file_pattern": "data_*.csv"
    },
    "output_settings": {
        "output_folder": "batch_eda_results"
    }
}
```

#### 2. 运行批量分析
```bash
python batch_eda_analysis.py
```

## 输出结果

### 单文件分析输出
- **CSV结果**: `scl_analysis_per_minute.csv`
- **可视化图表**: `scl_scr_analysis_plot.png`

### 批量处理输出
批量处理会在 `batch_eda_results/` 文件夹中生成：

#### 1. 单个文件结果
- `[文件名]_analysis.csv` - 每个文件的详细分析结果
- `[文件名]_plot.png` - 每个文件的可视化图表

#### 2. 汇总结果
- `batch_summary.csv` - 所有文件的汇总统计
- `all_files_combined_results.csv` - 所有文件的合并详细结果
- `statistical_report.txt` - 统计分析报告

#### 3. CSV结果文件列说明
- `minute`: 分钟数(从0开始)
- `average_scl`: 该分钟内的平均SCL值
- `std_scl`: 该分钟内SCL的标准差
- `data_points`: 该分钟内的数据点数量
- `min_scl`: 该分钟内的最小SCL值
- `max_scl`: 该分钟内的最大SCL值
- `scr_count`: 该分钟内检测到的SCR数量
- `filename`: 原始文件名(仅在合并结果中)

#### 4. 可视化图表内容
三个子图：
- 上图：原始GSR信号、滤波后信号和SCR峰值标记
- 中图：每分钟平均SCL变化趋势(带标准差范围)
- 下图：每分钟SCR数量柱状图

## 算法说明
1. **数据加载**: 读取CSV格式的皮电数据
2. **时间转换**: 将毫秒时间戳转换为相对分钟数
3. **信号滤波**: 使用0.1Hz低通滤波器去除高频噪声
4. **SCR检测**: 
   - 计算信号梯度检测上升趋势
   - 使用高斯滤波平滑梯度信号
   - 识别持续时间0.5-5秒的有效SCR
   - 设置最小幅度阈值过滤噪声
5. **SCL计算**: 按分钟分组计算平均皮电导水平和统计指标
6. **结果输出**: 生成CSV文件和综合可视化图表

## 参数说明
- 采样频率: 100Hz
- 滤波器截止频率: 0.1Hz
- SCR检测参数:
  - 最小幅度: 0.5 (可调节)
  - 最小持续时间: 0.5秒
  - 最大持续时间: 5.0秒
- 输出图像分辨率: 300 DPI

## SCR检测说明
SCR（皮肤电导反应）是皮电信号中的"峰值"特征，表现为信号的快速增加。程序自动检测：
- **事件相关SCR**: 在刺激后1-5秒内出现的反应
- **非特异性SCR**: 无明显外部刺激的自发性反应

检测结果包括每个SCR的位置、幅度和持续时间，并统计每分钟的SCR数量。

## 批量处理使用指南

### 1. 文件组织
```
项目目录/
├── data_file1.csv
├── data_file2.csv
├── data_file3.csv
├── batch_eda_analysis.py
├── batch_config.json
└── run_batch_analysis.bat
```

### 2. 配置文件说明 (batch_config.json)
```json
{
    "input_settings": {
        "input_folder": ".",           # 输入文件夹路径
        "file_pattern": "data_*.csv",  # 文件匹配模式
        "recursive_search": false      # 是否递归搜索子文件夹
    },
    "analysis_parameters": {
        "sampling_frequency": 100,     # 采样频率
        "lowpass_cutoff": 0.1,        # 低通滤波截止频率
        "scr_detection": {
            "min_duration": 1.0,       # SCR最小持续时间
            "max_duration": 10.0,      # SCR最大持续时间
            "adaptive_threshold_factor": 0.3  # 自适应阈值因子
        }
    }
}
```

### 3. 批量处理流程
1. **准备**: 将所有CSV文件放在指定文件夹
2. **配置**: 根据需要修改 `batch_config.json`
3. **运行**: 双击 `run_batch_analysis.bat` 或运行Python脚本
4. **查看结果**: 在 `batch_eda_results/` 文件夹中查看输出

### 4. 常见文件命名模式
- `data_*.csv` - 匹配所有以"data_"开头的CSV文件
- `*.csv` - 匹配所有CSV文件

## 依赖环境
- Python 3.9+
- pandas
- numpy
- matplotlib
- scipy

## 更新日志

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2025-03-27 | v1.1 | 添加英文版README文档 |
| 2025-03-27 | v1.0 | 初始版本，包含单文件分析和批量处理功能；添加data目录存放原始实验用户数据 |

---

# EDA Data Analysis Program (English Version)

## Overview
This program analyzes electrodermal activity (EDA) sensor data, extracting per-minute Skin Conductance Level (SCL) and Skin Conductance Response (SCR) statistics.

### Key Features
- **SCL Analysis**: Calculate average skin conductance level per minute
- **SCR Detection**: Automatically detect SCR peaks and count per minute
- **Signal Processing**: Low-pass filtering to remove noise
- **Visualization**: Generate comprehensive analysis charts

## Project Structure

```
EDA_Analysis/
├── data/                          # Raw experimental user data directory
│   ├── female/                    # Female subject data
│   │   ├── Subject_8.17-13_F_RuanXiangting_23y/
│   │   ├── Subject_8.19-16_F_JinKecheng_26y/
│   │   └── ...                    # Other female subjects
│   └── male/                      # Male subject data
│       ├── Subject_8.17-8_M_ZhuJunheng_25y/
│       ├── Subject_8.19-15_M_ZhangYufan_24y/
│       └── ...                    # Other male subjects
├── eda_analysis.py                # Single file analysis script
├── batch_eda_analysis.py          # Batch processing script
├── batch_config.json              # Batch processing configuration
├── activate_env.bat               # Virtual environment activation script
├── eda_analysis_env/              # Python virtual environment
└── README.md                      # Documentation
```

### Data File Description
- **CSV Data Files**: Contains two columns
  - Column 1: Timestamp (milliseconds)
  - Column 2: GSR value (galvanic skin response)
- **File Naming Convention**:
  - `data_YYYYMMDD_HHMMSS.csv` - Regular experimental data
  - `眼罩data_YYYYMMDD_HHMMSS.csv` - Eye mask experimental condition data
- **Audio Files**: `.m4a` format, recording audio during experiments

## Usage

### Method 1: Single File Analysis

#### 1. Activate Virtual Environment
```bash
activate_env.bat
```

#### 2. Run Single File Analysis
```bash
python eda_analysis.py
```
The program automatically searches for CSV files starting with `data_` in the current directory.

### Method 2: Batch Processing (Recommended)

#### 1. Configure Batch Processing
Edit `batch_config.json`:
```json
{
    "input_settings": {
        "input_folder": "data/female/Subject_8.17-13_F_RuanXiangting_23y",
        "file_pattern": "data_*.csv"
    },
    "output_settings": {
        "output_folder": "batch_eda_results"
    }
}
```

#### 2. Run Batch Analysis
```bash
python batch_eda_analysis.py
```

## Output Results

### Single File Analysis Output
- **CSV Results**: `scl_analysis_per_minute.csv`
- **Visualization**: `scl_scr_analysis_plot.png`

### Batch Processing Output
Generated in `batch_eda_results/` folder:

#### 1. Individual File Results
- `[filename]_analysis.csv` - Detailed analysis results per file
- `[filename]_plot.png` - Visualization chart per file

#### 2. Summary Results
- `batch_summary.csv` - Summary statistics for all files
- `all_files_combined_results.csv` - Combined detailed results
- `statistical_report.txt` - Statistical analysis report

#### 3. CSV Result Columns
- `minute`: Minute number (starting from 0)
- `average_scl`: Average SCL value within the minute
- `std_scl`: Standard deviation of SCL within the minute
- `data_points`: Number of data points within the minute
- `min_scl`: Minimum SCL value within the minute
- `max_scl`: Maximum SCL value within the minute
- `scr_count`: Number of SCR detected within the minute
- `filename`: Original filename (only in combined results)

#### 4. Visualization Content
Three subplots:
- Top: Raw GSR signal, filtered signal, and SCR peak markers
- Middle: Per-minute average SCL trend (with standard deviation range)
- Bottom: Per-minute SCR count bar chart

## Algorithm Description
1. **Data Loading**: Read CSV format EDA data
2. **Time Conversion**: Convert millisecond timestamps to relative minutes
3. **Signal Filtering**: Use 0.1Hz low-pass filter to remove high-frequency noise
4. **SCR Detection**:
   - Calculate signal gradient to detect rising trends
   - Apply Gaussian filter to smooth gradient signal
   - Identify valid SCRs with duration 0.5-5 seconds
   - Set minimum amplitude threshold to filter noise
5. **SCL Calculation**: Calculate average skin conductance level and statistics per minute
6. **Output**: Generate CSV files and comprehensive visualization

## Parameters
- Sampling frequency: 100Hz
- Filter cutoff frequency: 0.1Hz
- SCR detection parameters:
  - Minimum amplitude: 0.5 (adjustable)
  - Minimum duration: 0.5 seconds
  - Maximum duration: 5.0 seconds
- Output image resolution: 300 DPI

## SCR Detection Notes
SCR (Skin Conductance Response) is a "peak" feature in EDA signals, characterized by rapid signal increase. The program automatically detects:
- **Event-related SCR**: Responses appearing 1-5 seconds after stimulus
- **Non-specific SCR**: Spontaneous responses without obvious external stimulus

Detection results include position, amplitude, and duration of each SCR, with per-minute SCR counts.

## Dependencies
- Python 3.9+
- pandas
- numpy
- matplotlib
- scipy

## Changelog

| Date | Version | Updates |
|------|---------|---------|
| 2025-03-27 | v1.0 | Initial release with single file analysis and batch processing; added data directory for raw experimental user data |
