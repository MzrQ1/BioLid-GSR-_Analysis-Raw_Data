import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import glob
from datetime import datetime
import json

# 尝试导入neurokit2，处理可能的导入错误
try:
    import neurokit2 as nk
except TypeError as e:
    if "unsupported operand type(s) for |" in str(e):
        print("错误: NeuroKit2需要Python 3.10+版本")
        print("请使用setup_py312_env.bat创建Python 3.13环境")
        exit(1)
    else:
        raise e

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def analyze_eda_with_neurokit(filepath, sampling_rate=100, output_folder="nk_results"):
    """
    使用NeuroKit2分析EDA数据
    
    参数:
    - filepath: EDA数据文件路径
    - sampling_rate: 采样率（Hz）
    - output_folder: 输出文件夹
    """
    # 创建输出文件夹
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    print(f"分析文件: {os.path.basename(filepath)}")
    
    try:
        # 加载数据
        data = pd.read_csv(filepath)
        print(f"数据加载成功，共 {len(data)} 行数据")
        
        # 提取时间和EDA信号
        time_ms = data.iloc[:, 0].values
        eda_signal = data.iloc[:, 1].values
        
        # 创建相对时间（分钟）
        relative_time_ms = time_ms - time_ms.min()
        time_min = relative_time_ms / (1000 * 60)
        
        # 使用NeuroKit2处理EDA信号
        # 1. 清洗信号
        eda_cleaned = nk.eda_clean(eda_signal, sampling_rate=sampling_rate)
        
        # 2. 处理EDA信号 - 分解为相位和强度成分，检测SCR
        eda_signals, info = nk.eda_process(eda_cleaned, sampling_rate=sampling_rate)
        
        # 3. 提取SCR特征 (使用可用的API)
        # NeuroKit2 0.2.12版本没有eda_scr_features函数，使用info中的峰值信息
        scr_features = pd.DataFrame({
            'SCR_Onset': info['SCR_Onsets'],
            'SCR_Peak': info['SCR_Peaks'],
            'SCR_Recovery': info['SCR_Recovery']
        })
        
        # 计算SCR幅度
        if len(info['SCR_Peaks']) > 0:
            scr_amplitudes = []
            for i, peak in enumerate(info['SCR_Peaks']):
                if i < len(info['SCR_Onsets']):
                    onset = info['SCR_Onsets'][i]
                    amplitude = eda_signals['EDA_Phasic'][peak] - eda_signals['EDA_Phasic'][onset]
                    scr_amplitudes.append(amplitude)
            
            if scr_amplitudes:
                scr_features['SCR_Amplitude'] = scr_amplitudes
        
        # 创建包含时间的数据框
        results_df = eda_signals.copy()
        results_df["Time_minutes"] = np.linspace(0, len(eda_signal)/sampling_rate/60, len(eda_signal))
        
        # 计算每分钟SCR数量
        scr_count_per_minute = []
        total_minutes = int(np.ceil(len(eda_signal) / sampling_rate / 60))
        
        for minute in range(total_minutes):
            start_idx = minute * 60 * sampling_rate
            end_idx = min((minute + 1) * 60 * sampling_rate, len(eda_signal))
            
            # 计算该分钟内的SCR数量
            minute_info = info.copy()
            minute_info["SCR_Onsets"] = [onset for onset in info["SCR_Onsets"] if start_idx <= onset < end_idx]
            minute_info["SCR_Peaks"] = [peak for peak in info["SCR_Peaks"] if start_idx <= peak < end_idx]
            minute_info["SCR_Recovery"] = [rec for rec in info["SCR_Recovery"] if start_idx <= rec < end_idx]
            
            scr_count = len(minute_info["SCR_Peaks"])
            
            scr_count_per_minute.append({
                "minute": minute,
                "scr_count": scr_count,
                "mean_scl": np.mean(eda_signals["EDA_Tonic"][start_idx:end_idx]),
                "std_scl": np.std(eda_signals["EDA_Tonic"][start_idx:end_idx]),
                "data_points": end_idx - start_idx
            })
        
        # 创建每分钟统计数据框
        minute_stats = pd.DataFrame(scr_count_per_minute)
        
        # 保存结果
        base_filename = os.path.splitext(os.path.basename(filepath))[0]
        
        # 保存详细信号数据
        signals_file = os.path.join(output_folder, f"{base_filename}_signals.csv")
        results_df.to_csv(signals_file, index=False)
        
        # 保存每分钟统计
        stats_file = os.path.join(output_folder, f"{base_filename}_minute_stats.csv")
        minute_stats.to_csv(stats_file, index=False)
        
        # 保存SCR特征
        features_file = os.path.join(output_folder, f"{base_filename}_scr_features.csv")
        scr_features.to_csv(features_file, index=False)
        
        # 创建可视化
        fig = plt.figure(figsize=(15, 12))
        
        # 子图1: 原始信号和处理后信号
        ax1 = plt.subplot(3, 1, 1)
        plt.plot(time_min, eda_signal, 'b-', alpha=0.5, label='原始EDA信号')
        plt.plot(time_min, eda_cleaned, 'r-', label='清洗后信号')
        plt.xlabel('时间 (分钟)')
        plt.ylabel('EDA值')
        plt.title('EDA信号时间序列')
        plt.legend()
        plt.grid(True)
        
        # 子图2: 分解后的相位和强度成分
        ax2 = plt.subplot(3, 1, 2)
        plt.plot(time_min, eda_signals["EDA_Tonic"], 'g-', label='SCL (强度成分)')
        plt.plot(time_min, eda_signals["EDA_Phasic"], 'm-', label='SCR (相位成分)')
        
        # 标记SCR峰值
        scr_peaks_time = [idx/sampling_rate/60 for idx in info["SCR_Peaks"]]
        scr_peaks_value = [eda_signals["EDA_Phasic"][idx] for idx in info["SCR_Peaks"]]
        plt.scatter(scr_peaks_time, scr_peaks_value, color='red', s=50, marker='v', 
                   label=f'SCR峰值 (n={len(info["SCR_Peaks"])})', zorder=5)
        
        plt.xlabel('时间 (分钟)')
        plt.ylabel('EDA分量')
        plt.title('EDA分解 - 强度成分(SCL)和相位成分(SCR)')
        plt.legend()
        plt.grid(True)
        
        # 子图3: 每分钟SCR数量
        ax3 = plt.subplot(3, 1, 3)
        plt.bar(minute_stats['minute'], minute_stats['scr_count'], 
                alpha=0.7, color='orange', label='SCR数量')
        plt.xlabel('时间 (分钟)')
        plt.ylabel('SCR数量')
        plt.title('每分钟皮电导反应(SCR)数量')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        plot_file = os.path.join(output_folder, f"{base_filename}_plot.png")
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        # 输出统计信息
        total_duration = len(eda_signal) / sampling_rate / 60
        total_scr = len(info["SCR_Peaks"])
        scr_per_min = total_scr / total_duration if total_duration > 0 else 0
        
        print(f"\n分析结果:")
        print(f"总时长: {total_duration:.2f} 分钟")
        print(f"检测到SCR数量: {total_scr}")
        print(f"平均每分钟SCR: {scr_per_min:.2f}")
        print(f"结果已保存到: {output_folder}")
        
        return {
            "filename": os.path.basename(filepath),
            "total_duration": total_duration,
            "total_scr": total_scr,
            "scr_per_min": scr_per_min,
            "signals": results_df,
            "minute_stats": minute_stats,
            "scr_features": scr_features
        }
        
    except Exception as e:
        print(f"处理文件时出错: {str(e)}")
        return None

def batch_process_with_neurokit(input_folder="eda_data", output_folder="nk_results", file_pattern="data_*.csv"):
    """批量处理EDA数据文件"""
    # 创建输出文件夹
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # 获取所有匹配的CSV文件
    search_pattern = os.path.join(input_folder, file_pattern)
    csv_files = glob.glob(search_pattern)
    
    if not csv_files:
        print(f"在 {input_folder} 中未找到匹配 {file_pattern} 的文件")
        return None
    
    print(f"找到 {len(csv_files)} 个CSV文件待处理")
    
    # 存储所有结果
    all_results = []
    summary_data = []
    
    for i, csv_file in enumerate(csv_files, 1):
        print(f"\n{'='*60}")
        print(f"处理文件 {i}/{len(csv_files)}: {os.path.basename(csv_file)}")
        print(f"{'='*60}")
        
        result = analyze_eda_with_neurokit(csv_file, output_folder=output_folder)
        
        if result:
            all_results.append(result)
            
            # 添加到汇总
            summary_data.append({
                "filename": result["filename"],
                "total_duration_min": result["total_duration"],
                "total_scr": result["total_scr"],
                "scr_per_min": result["scr_per_min"]
            })
    
    # 创建汇总报告
    if all_results:
        # 保存汇总CSV
        summary_df = pd.DataFrame(summary_data)
        summary_file = os.path.join(output_folder, "nk_batch_summary.csv")
        summary_df.to_csv(summary_file, index=False)
        
        # 创建统计报告
        report_file = os.path.join(output_folder, "nk_statistical_report.txt")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("NeuroKit2 EDA分析统计报告\n")
            f.write("=" * 50 + "\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"总文件数: {len(all_results)}\n")
            
            # 汇总统计
            total_durations = [r["total_duration"] for r in all_results]
            total_scr_counts = [r["total_scr"] for r in all_results]
            scr_rates = [r["scr_per_min"] for r in all_results]
            
            f.write(f"\n记录时长统计:\n")
            f.write(f"  平均时长: {np.mean(total_durations):.2f} 分钟\n")
            f.write(f"  时长范围: {np.min(total_durations):.2f} - {np.max(total_durations):.2f} 分钟\n")
            
            f.write(f"\nSCR统计:\n")
            f.write(f"  平均SCR数: {np.mean(total_scr_counts):.1f}\n")
            f.write(f"  平均SCR/分钟: {np.mean(scr_rates):.2f}\n")
            f.write(f"  SCR/分钟范围: {np.min(scr_rates):.2f} - {np.max(scr_rates):.2f}\n")
            
            f.write(f"\n各文件详细信息:\n")
            f.write("-" * 50 + "\n")
            for result in all_results:
                f.write(f"文件: {result['filename']}\n")
                f.write(f"  时长: {result['total_duration']:.2f}分钟\n")
                f.write(f"  SCR总数: {result['total_scr']}\n")
                f.write(f"  SCR/分钟: {result['scr_per_min']:.2f}\n")
                f.write("\n")
        
        print(f"\n批量处理完成！")
        print(f"处理了 {len(all_results)} 个文件")
        print(f"结果保存在: {output_folder}")
        print(f"汇总报告: {report_file}")
    
    return all_results

def load_config(config_file="batch_config.json"):
    """加载配置文件"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"加载配置文件时出错: {e}")
        return {
            "input_settings": {
                "input_folder": "eda_data",
                "file_pattern": "data_*.csv"
            },
            "output_settings": {
                "output_folder": "nk_results"
            }
        }

if __name__ == "__main__":
    print("NeuroKit2 EDA分析程序")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    
    # 从配置文件获取参数
    input_folder = config["input_settings"]["input_folder"]
    file_pattern = config["input_settings"]["file_pattern"]
    output_folder = "nk_results"  # 使用专门的输出文件夹
    
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
    results = batch_process_with_neurokit(input_folder, output_folder, file_pattern)
