import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

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

def demo_neurokit_eda(filepath, sampling_rate=100):
    """
    使用NeuroKit2演示EDA数据分析
    
    参数:
    - filepath: EDA数据文件路径
    - sampling_rate: 采样率（Hz）
    """
    try:
        # 加载数据
        data = pd.read_csv(filepath)
        print(f"数据加载成功，共 {len(data)} 行数据")
        
        # 提取EDA信号
        eda_signal = data.iloc[:, 1].values
        
        # 创建NeuroKit数据框
        data = pd.DataFrame({"EDA_Raw": eda_signal})
        
        # 1. 清洗信号
        data["EDA_Clean"] = nk.eda_clean(data["EDA_Raw"], sampling_rate=sampling_rate)
        
        # 2. 处理EDA信号 - 分解为相位和强度成分，检测SCR
        eda_signals, info = nk.eda_process(data["EDA_Clean"], sampling_rate=sampling_rate)
        
        # 3. 绘制原始数据和处理结果
        print("绘制EDA信号...")
        
        # 绘制原始数据
        plt.figure(figsize=(10, 4))
        plt.plot(data["EDA_Raw"], label="原始EDA信号")
        plt.plot(data["EDA_Clean"], label="清洗后信号")
        plt.title("原始EDA信号与清洗后信号")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("nk_eda_raw.png", dpi=300)
        plt.close()
        
        # 使用NeuroKit的绘图功能
        print("绘制EDA处理结果...")
        nk.eda_plot(eda_signals, sampling_rate=sampling_rate)
        plt.savefig("nk_eda_processed.png", dpi=300)
        
        # 提取SCR特征 (使用可用的API)
        # 计算SCR幅度
        scr_amplitudes = []
        if len(info['SCR_Peaks']) > 0:
            for i, peak in enumerate(info['SCR_Peaks']):
                if i < len(info['SCR_Onsets']):
                    onset = info['SCR_Onsets'][i]
                    amplitude = eda_signals['EDA_Phasic'][peak] - eda_signals['EDA_Phasic'][onset]
                    scr_amplitudes.append(amplitude)
        
        print("\nSCR信息:")
        print(f"SCR峰值位置: {info['SCR_Peaks']}")
        print(f"SCR起始位置: {info['SCR_Onsets']}")
        
        # 输出SCR统计信息
        print(f"\n检测到SCR数量: {len(info['SCR_Peaks'])}")
        if scr_amplitudes:
            print(f"平均SCR幅度: {np.mean(scr_amplitudes):.3f}")
        else:
            print("未检测到SCR幅度")
        
        return eda_signals, info, scr_amplitudes
        
    except Exception as e:
        print(f"处理文件时出错: {str(e)}")
        return None, None, None

if __name__ == "__main__":
    # 查找数据文件
    data_folder = "eda_data"
    if not os.path.exists(data_folder):
        data_folder = "."
    
    csv_files = [f for f in os.listdir(data_folder) if f.endswith('.csv') and f.startswith('data_')]
    
    if not csv_files:
        print("错误: 未找到数据文件")
        exit(1)
    
    # 使用第一个找到的文件
    data_file = os.path.join(data_folder, csv_files[0])
    print(f"使用数据文件: {data_file}")
    
    # 运行演示
    signals, info, features = demo_neurokit_eda(data_file)
    
    print("\n演示完成！")
    print("生成的图表: nk_eda_raw.png, nk_eda_processed.png")
