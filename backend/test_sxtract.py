import parselmouth
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import soundfile as sf
import textgrid
from scipy.interpolate import interp1d

# def interpolate_to_uniform_length(times, data, num_points=100):
#     """将数据插值到相同长度"""
#     interpolated_data = []
#     for time, datum in zip(times, data):
#         # 处理 NaN 值，填充为最近的有效数据
#         valid = ~np.isnan(datum)
#         if not np.any(valid):
#             continue
#         time_valid = np.linspace(0, 100, num_points)
#         interp_func = interp1d(np.linspace(0, 100, len(datum[valid])), datum[valid], kind='linear', fill_value="extrapolate")
#         interpolated_data.append(interp_func(time_valid))
#     return time_valid, interpolated_data

# def plot_pitch(ax, times, pitches_semitones, labels, num_points=100, ylim=None):
#     """绘制重叠音高（半音），使用单一 y 轴"""
#     time_valid, interpolated_data = interpolate_to_uniform_length(times, pitches_semitones, num_points)
#     for pitch_semitones_interp, label in zip(interpolated_data, labels):
#         ax.plot(time_valid, pitch_semitones_interp, label=label, alpha=0.5)

#     ax.set_ylabel("Semitones", fontsize=8)
#     ax.set_title("Semitones", fontsize=10)
#     ax.legend(loc='upper left', fontsize=8)
#     if ylim:
#         ax.set_ylim(ylim)
    
#     # 设置比例横轴
#     ax.set_xlim(0, 100)
#     ax.set_xlabel("Proportion [%]", fontsize=8)

#     return ax

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
    # pitch_floors = [25, 50, 75, 100]
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
    
    return pitch.xs(), pitch_semitones

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
    print(interval)
    input()
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

# 绘图
# if times and pitches_semitones:
#     fig, ax = plt.subplots(figsize=(12, 8))  # 调整绘图区域高度

#     # 绘制裁剪后的重叠音高（半音）
#     ax_pitch = plot_pitch(ax, times, pitches_semitones, ['Segment'] * len(times),
#                           ylim=(np.nanmin([np.nanmin(p) for p in pitches_semitones]), 
#                                 np.nanmax([np.nanmax(p) for p in pitches_semitones])))

#     # 调整绘图区的位置，以确保曲线紧贴绘图区域的边界
#     plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

#     # 调整布局并显示图像
#     plt.tight_layout()
#     plt.savefig("cropped_comparison_output_image.png")
#     print("生成完成")
#     plt.show()
# else:
#     print("没有有效的数据进行绘图。")
