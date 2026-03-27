import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, find_peaks
from scipy.ndimage import gaussian_filter1d
import os
import glob
from datetime import datetime
import json

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 导入原有的分析函数
from eda_analysis import (
    load_eda_data, 
    convert_time_to_minutes, 
    butter_lowpass_filter, 
    detect_scr_peaks, 
    calculate_scr_per_minute
)

def batch_analyze_eda_files(input_folder, output_folder="batch_results", file_pattern="*.csv"):
    """
    批量分析EDA文件
    
    参数:
    - input_folder: 输入文件夹路径
    - output_folder: 输出结果文件夹
    - file_pattern: 文件匹配模式 (如 "*.csv" 或 "data_*.csv")
    """
    
    # 创建输出文件夹
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"创建输出文件夹: {output_folder}")
    
    # 获取所有匹配的CSV文件
    search_pattern = os.path.join(input_folder, file_pattern)
    csv_files = glob.glob(search_pattern)
    
    if not csv_files:
        print(f"在 {input_folder} 中未找到匹配 {file_pattern} 的文件")
        return None
    
    print(f"找到 {len(csv_files)} 个CSV文件待处理")
    
    # 存储所有结果的汇总
    batch_summary = []
    all_results = []
    
    for i, csv_file in enumerate(csv_files, 1):
        print(f"\n{'='*60}")
        print(f"处理文件 {i}/{len(csv_files)}: {os.path.basename(csv_file)}")
        print(f"{'='*60}")
        
        try:
            # 分析单个文件
            file_results = analyze_single_eda_file(csv_file, output_folder)
            
            if file_results is not None:
                # 添加文件信息
                file_results['filename'] = os.path.basename(csv_file)
                all_results.append(file_results)
                
                # 添加到汇总统计
                summary_info = {
                    'filename': os.path.basename(csv_file),
                    'total_duration_min': file_results['total_duration'],
                    'total_scr_count': file_results['total_scr_count'],
                    'average_scr_per_min': file_results['average_scr_per_min'],
                    'average_scl': file_results['average_scl'],
                    'scl_std': file_results['scl_std'],
                    'processing_status': 'success'
                }
                batch_summary.append(summary_info)
                print(f"✓ 文件处理成功")
            else:
                batch_summary.append({
                    'filename': os.path.basename(csv_file),
                    'processing_status': 'failed',
                    'error': 'analysis_failed'
                })
                print(f"✗ 文件处理失败")
                
        except Exception as e:
            print(f"✗ 处理文件时出错: {str(e)}")
            batch_summary.append({
                'filename': os.path.basename(csv_file),
                'processing_status': 'failed',
                'error': str(e)
            })
    
    # 保存批量处理汇总结果
    save_batch_summary(batch_summary, all_results, output_folder)
    
    print(f"\n{'='*60}")
    print(f"批量处理完成！")
    print(f"成功处理: {sum(1 for s in batch_summary if s['processing_status'] == 'success')} 个文件")
    print(f"处理失败: {sum(1 for s in batch_summary if s['processing_status'] == 'failed')} 个文件")
    print(f"结果保存在: {output_folder}")
    print(f"{'='*60}")
    
    return batch_summary

def analyze_single_eda_file(filepath, output_folder):
    """分析单个EDA文件"""
    
    # 1. 加载数据
    data = load_eda_data(filepath)
    if data is None:
        return None
    
    time_ms = data.iloc[:, 0].values
    gsr_values = data.iloc[:, 1].values
    
    print(f"时间范围: {time_ms.min()} - {time_ms.max()} 毫秒")
    print(f"GSR值范围: {gsr_values.min()} - {gsr_values.max()}")
    
    # 2. 时间转换
    minutes = convert_time_to_minutes(time_ms)
    total_duration = minutes.max()
    print(f"总时长: {total_duration:.2f} 分钟")
    
    # 3. 信号滤波
    fs = 100
    cutoff = 0.1
    filtered_gsr = butter_lowpass_filter(gsr_values, cutoff, fs)
    print("信号滤波完成")
    
    # 4. SCR峰值检测
    print("开始SCR峰值检测...")
    signal_std = np.std(filtered_gsr)
    # 降低阈值系数，从0.3降低到0.15，以检测更多的SCR峰值
    adaptive_threshold = max(0.05, signal_std * 0.15)
    print(f"信号标准差: {signal_std:.3f}, 使用自适应阈值: {adaptive_threshold:.3f}")
    
    scr_peaks, scr_amplitudes, scr_onsets, scr_durations = detect_scr_peaks(
        filtered_gsr, fs=fs, min_amplitude=adaptive_threshold, min_duration=0.5, max_duration=10.0
    )
    print(f"检测到 {len(scr_peaks)} 个SCR峰值")
    
    # 5. 计算每分钟的SCR数量
    scr_per_minute = calculate_scr_per_minute(scr_peaks, minutes, total_duration)
    
    # 6. 按分钟分组计算SCL
    minute_bins = np.floor(minutes).astype(int)
    
    results = []
    for minute in range(int(minute_bins.max()) + 1):
        mask = minute_bins == minute
        if np.sum(mask) > 0:
            minute_data = filtered_gsr[mask]
            results.append({
                'minute': minute,
                'average_scl': np.mean(minute_data),
                'std_scl': np.std(minute_data),
                'data_points': np.sum(mask),
                'min_scl': np.min(minute_data),
                'max_scl': np.max(minute_data),
                'scr_count': scr_per_minute[minute] if minute < len(scr_per_minute) else 0
            })
    
    results_df = pd.DataFrame(results)
    
    # 7. 保存单个文件的结果
    base_filename = os.path.splitext(os.path.basename(filepath))[0]
    
    # 保存详细结果CSV
    output_csv = os.path.join(output_folder, f"{base_filename}_analysis.csv")
    results_df.to_csv(output_csv, index=False)
    
    # 生成可视化图表
    output_plot = os.path.join(output_folder, f"{base_filename}_plot.png")
    create_analysis_plot(minutes, gsr_values, filtered_gsr, scr_peaks, results_df, fs, output_plot)
    
    # 8. 返回汇总信息
    file_summary = {
        'total_duration': total_duration,
        'total_scr_count': len(scr_peaks),
        'average_scr_per_min': len(scr_peaks) / total_duration if total_duration > 0 else 0,
        'average_scl': np.mean(results_df['average_scl']),
        'scl_std': np.std(results_df['average_scl']),
        'scr_amplitudes': scr_amplitudes,
        'scr_durations': scr_durations,
        'detailed_results': results_df
    }
    
    return file_summary

def create_analysis_plot(minutes, gsr_values, filtered_gsr, scr_peaks, results_df, fs, output_path):
    """创建分析图表"""
    
    plt.figure(figsize=(15, 12))
    
    # 子图1: 原始信号和SCR检测
    plt.subplot(3, 1, 1)
    plt.plot(minutes, gsr_values, 'b-', alpha=0.5, label='原始GSR信号')
    plt.plot(minutes, filtered_gsr, 'r-', label='滤波后信号')
    
    if len(scr_peaks) > 0:
        scr_peak_times = scr_peaks / (fs * 60)
        plt.scatter(scr_peak_times, filtered_gsr[scr_peaks], 
                   color='red', s=50, marker='v', label=f'SCR峰值 (n={len(scr_peaks)})', zorder=5)
    
    plt.xlabel('时间 (分钟)')
    plt.ylabel('GSR值')
    plt.title('皮电信号时间序列与SCR检测')
    plt.legend()
    plt.grid(True)
    
    # 子图2: 每分钟SCL统计
    plt.subplot(3, 1, 2)
    plt.plot(results_df['minute'], results_df['average_scl'], 'go-', label='平均SCL')
    plt.fill_between(results_df['minute'], 
                     results_df['average_scl'] - results_df['std_scl'],
                     results_df['average_scl'] + results_df['std_scl'],
                     alpha=0.3, label='±1标准差')
    plt.xlabel('时间 (分钟)')
    plt.ylabel('平均SCL')
    plt.title('每分钟皮电导水平(SCL)变化')
    plt.legend()
    plt.grid(True)
    
    # 子图3: 每分钟SCR数量
    plt.subplot(3, 1, 3)
    plt.bar(results_df['minute'], results_df['scr_count'], 
            alpha=0.7, color='orange', label='SCR数量')
    plt.xlabel('时间 (分钟)')
    plt.ylabel('SCR数量')
    plt.title('每分钟皮电导反应(SCR)数量')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()  # 关闭图形以释放内存

def save_batch_summary(batch_summary, all_results, output_folder):
    """保存批量处理汇总结果"""
    
    # 保存汇总统计CSV
    summary_df = pd.DataFrame(batch_summary)
    summary_csv = os.path.join(output_folder, "batch_summary.csv")
    summary_df.to_csv(summary_csv, index=False)
    
    # 创建详细的汇总报告
    if all_results:
        # 合并所有结果
        combined_results = []
        for result in all_results:
            df = result['detailed_results'].copy()
            df['filename'] = result['filename']
            combined_results.append(df)
        
        combined_df = pd.concat(combined_results, ignore_index=True)
        combined_csv = os.path.join(output_folder, "all_files_combined_results.csv")
        combined_df.to_csv(combined_csv, index=False)
        
        # 创建统计报告
        create_statistical_report(all_results, output_folder)
    
    print(f"汇总结果已保存到: {summary_csv}")

def create_statistical_report(all_results, output_folder):
    """创建统计报告"""
    
    report_path = os.path.join(output_folder, "statistical_report.txt")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("皮电数据批量分析统计报告\n")
        f.write("=" * 50 + "\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"总文件数: {len(all_results)}\n")
        
        # 汇总统计
        total_durations = [r['total_duration'] for r in all_results]
        total_scr_counts = [r['total_scr_count'] for r in all_results]
        average_scr_rates = [r['average_scr_per_min'] for r in all_results]
        average_scls = [r['average_scl'] for r in all_results]
        
        f.write(f"\n记录时长统计:\n")
        f.write(f"  平均时长: {np.mean(total_durations):.2f} 分钟\n")
        f.write(f"  时长范围: {np.min(total_durations):.2f} - {np.max(total_durations):.2f} 分钟\n")
        
        f.write(f"\nSCR统计:\n")
        f.write(f"  平均总SCR数: {np.mean(total_scr_counts):.1f}\n")
        f.write(f"  平均SCR/分钟: {np.mean(average_scr_rates):.2f}\n")
        f.write(f"  SCR/分钟范围: {np.min(average_scr_rates):.2f} - {np.max(average_scr_rates):.2f}\n")
        
        f.write(f"\nSCL统计:\n")
        f.write(f"  平均SCL: {np.mean(average_scls):.2f}\n")
        f.write(f"  SCL范围: {np.min(average_scls):.2f} - {np.max(average_scls):.2f}\n")
        
        f.write(f"\n各文件详细信息:\n")
        f.write("-" * 50 + "\n")
        for result in all_results:
            f.write(f"文件: {result['filename']}\n")
            f.write(f"  时长: {result['total_duration']:.2f}分钟\n")
            f.write(f"  SCR总数: {result['total_scr_count']}\n")
            f.write(f"  SCR/分钟: {result['average_scr_per_min']:.2f}\n")
            f.write(f"  平均SCL: {result['average_scl']:.2f}\n")
            f.write("\n")

def load_config(config_file="batch_config.json"):
    """加载配置文件"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"配置文件 {config_file} 未找到，使用默认配置")
        return {
            "input_settings": {
                "input_folder": ".",
                "file_pattern": "*.csv"
            },
            "output_settings": {
                "output_folder": "batch_eda_results"
            }
        }
    except Exception as e:
        print(f"加载配置文件时出错: {e}")
        return None

if __name__ == "__main__":
    print("皮电数据批量分析程序")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    if config is None:
        print("配置加载失败，程序退出")
        exit(1)
    
    # 从配置文件获取参数
    input_folder = config["input_settings"]["input_folder"]
    file_pattern = config["input_settings"]["file_pattern"]
    output_folder = config["output_settings"]["output_folder"]
    
    print(f"输入目录: {input_folder}")
    print(f"输出目录: {output_folder}")
    print(f"文件模式: {file_pattern}")
    
    # 检查输入文件夹是否存在
    if not os.path.exists(input_folder):
        print(f"错误: 输入文件夹 '{input_folder}' 不存在！")
        print("请检查配置文件中的 input_folder 设置")
        exit(1)
    
    print("=" * 60)
    
    # 执行批量分析
    results = batch_analyze_eda_files(input_folder, output_folder, file_pattern)
