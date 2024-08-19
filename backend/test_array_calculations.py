import numpy as np

def generate_sine_wave_v1(frequencies, sample_rate):
    t = np.arange(len(frequencies)) / sample_rate
    phase = 2 * np.pi * np.cumsum(frequencies / sample_rate)
    wave = np.sin(phase)
    return t, phase, wave

def generate_sine_wave_v2(frequencies, sample_rate):
    t = np.arange(len(frequencies)) / sample_rate
    phase = np.cumsum(2 * np.pi * frequencies / sample_rate)
    wave = np.sin(phase)
    return t, phase, wave

# 示例频率数组
sample_rate = 44100
frequencies = np.array([440, 440, 440, 440, 440, 440, 440, 440])

# 生成正弦波
t1, phase1, wave1 = generate_sine_wave_v1(frequencies, sample_rate)
t2, phase2, wave2 = generate_sine_wave_v2(frequencies, sample_rate)

# 打印结果进行对比
print("Phase1:", phase1)
print("Phase2:", phase2)
print("Waves equal:", np.allclose(wave1, wave2))
