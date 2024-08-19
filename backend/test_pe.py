import os
import parselmouth
import tgt
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import patches
import numpy as np
from scipy.interpolate import interp1d

def read_sound(file_path):
    """读取音频文件"""
    return parselmouth.Sound(file_path)

def read_textgrid(file_path):
    """使用 tgt 读取 TextGrid 文件"""
    return tgt.read_textgrid(file_path)

def frequency_to_semitones(frequencies, reference_frequency=85):
    """将频率转换为半音"""
    valid = frequencies > 0  # 过滤掉无效频率值
    semitones = np.zeros_like(frequencies)
    semitones[valid] = 12 * np.log2(frequencies[valid] / reference_frequency)
    semitones[~valid] = np.nan  # 将无效频率值设置为 NaN
    return semitones

def interpolate_to_uniform_length(times, data, num_points=100):
    """将数据插值到相同长度"""
    interpolated_data = []
    for time, datum in zip(times, data):
        # 处理 NaN 值，填充为最近的有效数据
        valid = ~np.isnan(datum)
        if not np.any(valid):
            continue
        time_valid = np.linspace(0, 100, num_points)
        interp_func = interp1d(np.linspace(0, 100, len(datum[valid])), datum[valid], kind='linear', fill_value="extrapolate")
        interpolated_data.append(interp_func(time_valid))
    return time_valid, interpolated_data

def plot_waveform(ax, sound, start_time, end_time):
    """绘制音频的波形"""
    ax.plot(np.linspace(start_time, end_time, len(sound.values.T)), sound.values.T, color='blue')
    ax.set_ylabel("Amplitude")
    ax.set_title("Waveform")

def plot_pitch(ax, times, pitches_semitones, labels, num_points=100, ylim=None):
    """绘制重叠音高（半音），使用单一 y 轴"""
    time_valid, interpolated_data = interpolate_to_uniform_length(times, pitches_semitones, num_points)
    for pitch_semitones_interp, label in zip(interpolated_data, labels):
        ax.plot(time_valid, pitch_semitones_interp, label=label, alpha=0.5)

    ax.set_ylabel("Semitones", fontsize=8)
    ax.set_title("Semitones", fontsize=10)
    ax.legend(loc='upper left', fontsize=8)
    if ylim:
        ax.set_ylim(ylim)
    
    # 设置比例横轴
    ax.set_xlim(0, 100)
    ax.set_xlabel("Proportion [%]", fontsize=8)

    return ax

def plot_textgrid(ax, textgrid, offset, color):
    """绘制 TextGrid 并用文本框表示音素"""
    for i, tier in enumerate(textgrid.tiers):
        for interval in tier.intervals:
            rect = patches.Rectangle((interval.start_time, i + offset - 0.4), 
                                     interval.end_time - interval.start_time, 0.8, 
                                     linewidth=1, edgecolor=color, facecolor='none')
            ax.add_patch(rect)
            ax.text((interval.start_time + interval.end_time) / 2, i + offset, interval.text, 
                    horizontalalignment='center', verticalalignment='center', color=color, fontsize=8)
    ax.set_ylim(0.5, len(textgrid.tiers) + 0.5 + offset)
    ax.set_yticks(range(1+offset, len(textgrid.tiers) + 1+offset))
    ax.set_yticklabels([tier.name for tier in textgrid.tiers], fontsize=8)
    ax.set_xlabel("Time [s]", fontsize=8)
    ax.set_title("TextGrid", fontsize=10)

def add_vertical_lines(ax, textgrid, color):
    """添加垂直线以分隔音素"""
    for tier in textgrid.tiers:
        for interval in tier.intervals:
            ax.axvline(x=interval.start_time, color=color, linestyle='--', alpha=0.5)
            ax.axvline(x=interval.end_time, color=color, linestyle='--', alpha=0.5)

def get_phonemes_from_textgrid(textgrid):
    """获取 TextGrid 中的音素序列"""
    phonemes = []
    for tier in textgrid.tiers:
        for interval in tier.intervals:
            phonemes.append(interval.text)
    return phonemes

def get_phoneme_intervals(textgrid, phonemes):
    """根据音素序列获取对应的时间区间"""
    intervals = []
    for tier in textgrid.tiers:
        for interval in tier.intervals:
            if interval.text in phonemes:
                intervals.append((interval.start_time, interval.end_time, interval.text))
    return intervals

def crop_sound(sound, start_time, end_time):
    """裁剪音频文件"""
    if end_time > start_time:  # 确保区间有效
        print(f"裁剪音频：起始时间 {start_time}, 结束时间 {end_time}")
        return sound.extract_part(from_time=start_time, to_time=end_time)
    else:
        return None  # 如果区间无效，则返回 None

def scale_sound(sound, target_duration):
    """拉伸音频到目标长度"""
    original_duration = sound.get_total_duration()
    factor = target_duration / original_duration
    try:
        scaled_sound = sound.lengthen(factor=factor, minimum_pitch=100)
    except parselmouth.PraatError:
        scaled_sound = sound.lengthen(factor=factor, minimum_pitch=75)
    return scaled_sound

def plot_temporary_waveform_and_pitch(cropped_sound, start_time, end_time):
    """绘制临时音频的波形和音高图"""
    pitch_floors = [100, 75, 50, 25]
    pitch = None
    for pitch_floor in pitch_floors:
        try:
            pitch = cropped_sound.to_pitch(time_step=0.01, pitch_floor=pitch_floor)
            break
        except parselmouth.PraatError:
            continue
    if pitch is None:
        print("无法提取音高，跳过此文件。")
        return False
    
    pitch_semitones = frequency_to_semitones(pitch.selected_array['frequency'])

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    plot_waveform(axes[0], cropped_sound, start_time, end_time)
    axes[0].set_title(f"Temporary Cropped Waveform (from {start_time} to {end_time} s)")
    
    axes[1].plot(np.linspace(start_time, end_time, len(pitch_semitones)), pitch_semitones, color='blue')
    axes[1].set_ylabel("Semitones")
    axes[1].set_xlabel("Time [s]")
    axes[1].set_title("Temporary Cropped Pitch")
    
    plt.tight_layout()
    plt.show()
    
    return True

def print_colored_message(message, color_code):
    """打印带颜色的消息"""
    print(f"\033[{color_code}m{message}\033[0m")

if __name__ == "__main__":
    sns.set()
    
    phonemes_list = []
    sound_files = []
    textgrid_files = []
    labels = []
    times = []  # 初始化times列表
    pitches_semitones = []  # 初始化pitches_semitones列表

    # 获取corpus目录下的所有.wav文件
    corpus_dir = "corpus"
    wav_files = [f for f in os.listdir(corpus_dir) if f.endswith('.wav')]
    
    print(f"当前{corpus_dir}目录下有如下文件:")
    for file in wav_files:
        print(file)

    # 从终端获取要对比的文件名，直到输入关键词END
    while True:
        file = input("请输入要对比的文件（输入END结束）: ")
        if file == "END":
            break
        if not os.path.exists(os.path.join(corpus_dir, file)):
            print(f"文件 {file} 不存在，请重新输入。")
            continue
        sound_files.append(os.path.join(corpus_dir, file))
        textgrid_files.append(os.path.join("result", file.replace(".wav", ".TextGrid")))
        
        if not os.path.exists(textgrid_files[-1]):
            print(f"TextGrid 文件 {textgrid_files[-1]} 不存在，请重新输入。")
            sound_files.pop()
            textgrid_files.pop()
            continue
        
        textgrid = read_textgrid(textgrid_files[-1])
        phonemes = get_phonemes_from_textgrid(textgrid)
        
        print(f"根据textgrid, 文件{file}包含以下音素序列:")
        print(phonemes)
        phonemes_input = input("请输入要参与对比的音素序列,默认全选: ")
        if phonemes_input:
            phonemes = [p.strip().strip("'").strip('"') for p in phonemes_input.split(',')]
        print(f"处理后的音素序列: {phonemes}")

        # 获取音素区间
        intervals = get_phoneme_intervals(textgrid, phonemes)
        if not intervals:
            print(f"输入的音素序列无效，请检查音素是否在文本网格中: {file}")
            continue
        
        start_time = intervals[0][0]
        end_time = intervals[-1][1]
        
        print(f"裁剪时间: 起始时间 {start_time}, 结束时间 {end_time}")

        # 裁剪音频文件并绘制临时波形和音高图
        sound = read_sound(sound_files[-1])
        cropped_sound = crop_sound(sound, start_time, end_time)
        
        if cropped_sound is None:
            print(f"裁剪后的音频无效，请检查输入的音素序列: {file}")
            sound_files.pop()
            textgrid_files.pop()
            continue
        
        # 绘制临时波形和音高图
        if not plot_temporary_waveform_and_pitch(cropped_sound, start_time, end_time):
            sound_files.pop()
            textgrid_files.pop()
            continue
        
        modify_times = input(f"是否需要修改切片的起止时间点? 如果需要,请输入两个浮点值（起点,终点）以逗号分割,否则直接回车: ")
        if modify_times:
            try:
                new_times = [float(x) for x in modify_times.split(',')]
                if len(new_times) == 2:
                    start_time, end_time = new_times
                    print(f"新的裁剪时间: 起始时间 {start_time}, 结束时间 {end_time}")
                else:
                    print_colored_message("输入的时间点数目不正确，使用默认时间点。", '31')  # 红色输出
            except ValueError:
                print_colored_message("输入的时间点格式不正确，使用默认时间点。", '31')  # 红色输出

        # 再次裁剪音频文件
        cropped_sound = crop_sound(sound, start_time, end_time)
        
        # 确保裁剪结果有效
        if cropped_sound is None:
            print(f"裁剪后的音频无效，请检查输入的音素序列: {file}")
            sound_files.pop()
            textgrid_files.pop()
            continue

        label_input = input("请输入这个音素序列代表的意思（直接回车使用音素序列作为标签）: ")
        if not label_input:
            label_input = ' + '.join(phonemes)
        
        phonemes_list.append(phonemes)
        labels.append(label_input)

        # 提取音高并转换为半音
        try:
            # 拉伸音频到相同长度
            max_duration = cropped_sound.get_total_duration()
            cropped_sound = scale_sound(cropped_sound, max_duration)
            
            # 提取音高
            pitch_floors = [100, 75, 50, 25]
            pitch = None
            for pitch_floor in pitch_floors:
                try:
                    pitch = cropped_sound.to_pitch(time_step=0.01, pitch_floor=pitch_floor)
                    break
                except parselmouth.PraatError:
                    continue
            if pitch is None:
                print(f"处理音素 {label_input} 时出错，跳过。无法提取音高。")
                continue
            
            # 将音高转换为半音
            pitch_semitones = frequency_to_semitones(pitch.selected_array['frequency'])
        except parselmouth.PraatError as e:
            print(f"处理音素 {label_input} 时出错，跳过。错误信息: {e}")
            continue
        
        # 保存时间和半音数据
        times.append(pitch.xs())
        pitches_semitones.append(pitch_semitones)

    # 绘图
    if times and pitches_semitones:
        fig, ax = plt.subplots(figsize=(12, 8))  # 调整绘图区域高度

        # 绘制裁剪后的重叠音高（半音）
        ax_pitch = plot_pitch(ax, times, pitches_semitones, labels,
                              ylim=(np.nanmin([np.nanmin(p) for p in pitches_semitones]), 
                                    np.nanmax([np.nanmax(p) for p in pitches_semitones])))
        
        # 调整绘图区的位置，以确保曲线紧贴绘图区域的边界
        plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
        
        # 调整布局并显示图像
        plt.tight_layout()
        plt.savefig("cropped_comparison_output_image.png")
        print("生成完成")
        plt.show()
    else:
        print("没有有效的数据进行绘图。")
