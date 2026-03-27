import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, find_peaks
from scipy.ndimage import gaussian_filter1d
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def load_eda_data(filepath):
    """加载皮电数据"""
    try:
        data = pd.read_csv(filepath)
        print(f"数据加载成功，共 {len(data)} 行数据")
        print(f"数据列名: {list(data.columns)}")
        return data
    except Exception as e:
        print(f"数据加载失败: {e}")
        return None

def convert_time_to_minutes(time_ms):
    """将毫秒时间戳转换为从开始的分钟数"""
    # 转换为相对时间(毫秒)
    relative_time_ms = time_ms - time_ms.min()
    # 转换为分钟
    minutes = relative_time_ms / (1000 * 60)
    return minutes

def butter_lowpass_filter(data, cutoff, fs, order=4):
    """低通滤波器"""
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = filtfilt(b, a, data)
    return y

def detect_scr_peaks(eda_signal, fs=100, min_amplitude=0.01, min_duration=0.5, max_duration=5.0):
    """
    检测SCR峰值 - 改进版本，更适合皮电数据
    
    参数:
    - eda_signal: 皮电信号
    - fs: 采样频率 (Hz)
    - min_amplitude: 最小SCR幅度 (相对于局部基线)
    - min_duration: 最小持续时间 (秒)
    - max_duration: 最大持续时间 (秒)
    
    返回:
    - scr_peaks: SCR峰值位置
    - scr_amplitudes: SCR幅度
    """
    
    # 1. 使用移动窗口计算局部基线
    window_size = int(fs * 30)  # 30秒窗口
    local_baseline = np.zeros_like(eda_signal)
    
    for i in range(len(eda_signal)):
        start_idx = max(0, i - window_size // 2)
        end_idx = min(len(eda_signal), i + window_size // 2)
        local_baseline[i] = np.percentile(eda_signal[start_idx:end_idx], 20)  # 使用20%分位数作为基线
    
    # 2. 计算相对于局部基线的信号
    relative_signal = eda_signal - local_baseline
    
    # 3. 计算信号的一阶导数（上升速率）
    gradient = np.gradient(relative_signal)
    
    # 4. 平滑梯度信号
    smooth_gradient = gaussian_filter1d(gradient, sigma=fs*0.2)
    
    # 5. 使用scipy的find_peaks寻找峰值
    # 设置峰值检测参数 - 降低阈值以检测更多峰值
    min_height = min_amplitude  # 最小高度
    min_distance = int(fs * 0.3)  # 最小间距降低到0.3秒
    width_range = (int(fs * min_duration), int(fs * max_duration))  # 宽度范围
    
    # 寻找峰值 - 降低突出度要求
    peaks, properties = find_peaks(
        relative_signal,
        height=min_height,
        distance=min_distance,
        width=width_range,
        prominence=min_amplitude * 0.3  # 突出度降低到0.3倍
    )
    
    # 6. 提取峰值信息
    scr_peaks = peaks
    scr_amplitudes = properties['peak_heights'] if 'peak_heights' in properties else relative_signal[peaks]
    scr_durations = properties['widths'] / fs if 'widths' in properties else np.ones(len(peaks))
    
    # 7. 寻找每个峰值的起始点
    scr_onsets = []
    for peak in peaks:
        # 向前搜索找到信号开始上升的点
        onset = peak
        for j in range(peak, max(0, peak - int(fs * 10)), -1):  # 最多向前搜索10秒
            if gradient[j] < 0:  # 找到开始上升前的点
                onset = j + 1
                break
        scr_onsets.append(onset)
    
    return np.array(scr_peaks), np.array(scr_amplitudes), np.array(scr_onsets), np.array(scr_durations)

def calculate_scr_per_minute(scr_peaks, minutes, total_minutes):
    """计算每分钟的SCR数量"""
    scr_per_minute = []
    
    for minute in range(int(total_minutes) + 1):
        # 获取该分钟内的SCR峰值
        minute_start = minute * 60  # 转换为秒
        minute_end = (minute + 1) * 60
        
        # 将峰值索引转换为时间（秒）
        scr_times = scr_peaks / 100.0  # 假设100Hz采样率
        
        # 计算该分钟内的SCR数量
        scr_in_minute = np.sum((scr_times >= minute_start) & (scr_times < minute_end))
        scr_per_minute.append(scr_in_minute)
    
    return scr_per_minute

def analyze_eda_per_minute(filepath):
    """分析皮电数据，提取每分钟SCL和SCR"""
    
    # 1. 加载数据
    data = load_eda_data(filepath)
    if data is None:
        return None
    
    time_ms = data.iloc[:, 0].values  # 时间戳(毫秒)
    gsr_values = data.iloc[:, 1].values  # GSR值
    
    print(f"时间范围: {time_ms.min()} - {time_ms.max()} 毫秒")
    print(f"GSR值范围: {gsr_values.min()} - {gsr_values.max()}")
    
    # 2. 时间转换
    minutes = convert_time_to_minutes(time_ms)
    total_duration = minutes.max()
    print(f"总时长: {total_duration:.2f} 分钟")
    
    # 3. 信号滤波
    fs = 100  # 采样频率100Hz
    cutoff = 0.1  # 截止频率0.1Hz，适合皮电信号
    filtered_gsr = butter_lowpass_filter(gsr_values, cutoff, fs)
    print("信号滤波完成")
    
    # 4. SCR峰值检测
    print("开始SCR峰值检测...")
    # 根据数据范围调整阈值 - 使用信号标准差的一定比例作为阈值
    signal_std = np.std(filtered_gsr)
    # 降低阈值系数，从0.3降低到0.15，以检测更多的SCR峰值
    adaptive_threshold = max(0.05, signal_std * 0.15)  # 最小阈值降低到0.05，系数降低到15%
    print(f"信号标准差: {signal_std:.3f}, 使用自适应阈值: {adaptive_threshold:.3f}")
    
    scr_peaks, scr_amplitudes, scr_onsets, scr_durations = detect_scr_peaks(
        filtered_gsr, fs=fs, min_amplitude=adaptive_threshold, min_duration=0.5, max_duration=10.0
    )
    print(f"检测到 {len(scr_peaks)} 个SCR峰值")
    
    # 5. 计算每分钟的SCR数量
    scr_per_minute = calculate_scr_per_minute(scr_peaks, minutes, total_duration)
    print("每分钟SCR计算完成")
    
    # 6. 按分钟分组计算SCL
    minute_bins = np.floor(minutes).astype(int)
    
    # 创建结果DataFrame
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
    print(f"分析完成，共 {len(results_df)} 分钟的数据")
    
    # 5. 保存结果
    output_file = "scl_analysis_per_minute.csv"
    results_df.to_csv(output_file, index=False)
    print(f"结果已保存到: {output_file}")
    
    # 7. 生成可视化图表
    plt.figure(figsize=(15, 12))
    
    # 子图1: 原始信号和SCR检测
    plt.subplot(3, 1, 1)
    plt.plot(minutes, gsr_values, 'b-', alpha=0.5, label='原始GSR信号')
    plt.plot(minutes, filtered_gsr, 'r-', label='滤波后信号')
    
    # 标记SCR峰值
    if len(scr_peaks) > 0:
        scr_peak_times = scr_peaks / (fs * 60)  # 转换为分钟
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
    plt.savefig('scl_scr_analysis_plot.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 8. 输出SCR统计信息
    if len(scr_peaks) > 0:
        print(f"\nSCR统计信息:")
        print(f"总SCR数量: {len(scr_peaks)}")
        print(f"平均SCR幅度: {np.mean(scr_amplitudes):.3f}")
        print(f"SCR平均持续时间: {np.mean(scr_durations):.2f}秒")
        print(f"每分钟平均SCR数量: {len(scr_peaks) / total_duration:.2f}")
    else:
        print("\n未检测到明显的SCR峰值，可能需要调整检测参数")
    
    return results_df

if __name__ == "__main__":
    # 检查是否有CSV文件可用于分析
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv') and f.startswith('data_')]
    
    if not csv_files:
        print("错误: 当前目录中没有找到以 'data_' 开头的CSV文件")
        print("请确保数据文件在当前目录中，或使用批量处理程序分析 eda_data 文件夹中的文件")
        print("使用批量处理: python batch_eda_analysis.py")
    else:
        # 使用第一个找到的文件
        data_file = csv_files[0]
        print(f"找到数据文件: {data_file}")
        
        result = analyze_eda_per_minute(data_file)
        if result is not None and not result.empty:
            print("皮电数据分析完成!")
            print(f"生成了 {len(result)} 分钟的SCL和SCR统计数据")
            print("结果文件: scl_analysis_per_minute.csv")
            print("可视化图表: scl_scr_analysis_plot.png")
        else:
            print("分析过程中出现错误")
