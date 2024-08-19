import parselmouth
import numpy as np
import matplotlib.pyplot as plt
import soundfile as sf
import textgrid

def frequency_to_semitones(frequencies, reference_frequency=85):
    """将频率转换为半音"""
    valid = frequencies > 0  # 过滤掉无效频率值
    semitones = np.zeros_like(frequencies)
    semitones[valid] = 12 * np.log2(frequencies[valid] / reference_frequency)
    semitones[~valid] = np.nan  # 将无效频率值设置为 NaN
    return semitones

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
        return None, None
    
    pitch_semitones = frequency_to_semitones(pitch.selected_array['frequency'])
    
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    # 绘制波形图
    axes[0].plot(np.linspace(start_time, end_time, len(cropped_sound.values.T)), cropped_sound.values.T, color='blue')
    axes[0].set_ylabel("Amplitude")
    axes[0].set_title(f"Temporary Cropped Waveform (from {start_time} to {end_time} s)")
    
    # 绘制音高图
    axes[1].plot(np.linspace(start_time, end_time, len(pitch_semitones)), pitch_semitones, color='blue')
    axes[1].set_ylabel("Semitones")
    axes[1].set_xlabel("Time [s]")
    axes[1].set_title("Temporary Cropped Pitch")
    
    plt.tight_layout()
    plt.show()
    
    return np.linspace(start_time, end_time, len(pitch_semitones)), pitch_semitones

# 读取音频文件
audio_file = 'input_audio.wav'
signal, sample_rate = sf.read(audio_file)

# 创建 parselmouth 的 Sound 对象
sound = parselmouth.Sound(audio_file)

# 读取 TextGrid 文件
tg = textgrid.TextGrid.fromFile('input_audio.TextGrid')
phones_tier = tg.getFirst('phones')

# 获取波形数据
x = np.arange(len(signal)) / sample_rate

# 初始化音高数据
pitch_values = np.full_like(x, np.nan)

# 遍历每个音素的时间间隔并提取音高
times = []
pitches_semitones = []

for interval in phones_tier.intervals:
    if interval.mark.strip() == "":
        continue
    start_time = interval.minTime
    end_time = interval.maxTime
    cropped_sound = sound.extract_part(from_time=start_time, to_time=end_time, preserve_times=True)
    
    # 绘制临时波形和音高图
    segment_times, segment_pitch_semitones = plot_temporary_waveform_and_pitch(cropped_sound, start_time, end_time)
    if segment_times is None or segment_pitch_semitones is None:
        continue
    
    # 保存时间和半音数据
    times.append(segment_times)
    pitches_semitones.append(segment_pitch_semitones)

# 合并所有时间轴和音高数据
all_times = np.concatenate(times)
all_pitches_semitones = np.concatenate(pitches_semitones)

# 绘图
if all_times.size > 0 and all_pitches_semitones.size > 0:
    fig, ax = plt.subplots(figsize=(12, 8))  # 调整绘图区域高度

    # 绘制按比例显示的音高图
    ax.plot(all_times, all_pitches_semitones, label='Pitch', alpha=0.7)

    ax.set_ylabel("Semitones", fontsize=8)
    ax.set_title("Pitch over Time", fontsize=10)
    ax.legend(loc='upper left', fontsize=8)
    
    ax.set_xlabel("Time [s]", fontsize=8)

    # 调整布局并显示图像
    plt.tight_layout()
    plt.savefig("pitch_over_time_output_image.png")
    print("生成完成")
    plt.show()
else:
    print("没有有效的数据进行绘图。")
