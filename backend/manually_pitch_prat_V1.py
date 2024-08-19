import numpy as np
import matplotlib.pyplot as plt
import soundfile as sf
from scipy.interpolate import interp1d
import json

def parse_praat_pitch_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.readlines()

    frames_data = []
    current_frame = None
    intensity = None

    for line in content:
        line = line.strip()
        if line.startswith('frames [') and 'frames []' not in line:
            if current_frame is not None:
                frames_data.append(current_frame)
            current_frame = {'frame': int(line.split('[')[1].split(']')[0]), 'candidates': []}
        elif line.startswith('intensity ='):
            intensity = float(line.split('=')[1].strip())
            current_frame['intensity'] = intensity
        elif line.startswith('candidates ['):
            candidate = {}
        elif line.startswith('frequency ='):
            candidate['frequency'] = float(line.split('=')[1].strip())
        elif line.startswith('strength ='):
            candidate['strength'] = float(line.split('=')[1].strip())
            current_frame['candidates'].append(candidate)

    if current_frame is not None:
        frames_data.append(current_frame)
    
    return frames_data

def calculate_times(frames_data, x1, dx):
    return [x1 + (frame['frame'] - 1) * dx for frame in frames_data]

def interpolate_pitch(times, frequencies, target_sample_rate):
    frequencies = np.array(frequencies)
    times = np.array(times)
    
    # Create an interpolation function
    interpolation_function = interp1d(times, frequencies, kind='cubic', fill_value="extrapolate")
    
    # Generate new time points at the target sample rate
    new_times = np.arange(times[0], times[-1], 1/target_sample_rate)
    
    # Interpolate frequencies at the new time points
    interpolated_frequencies = interpolation_function(new_times)
    
    return new_times, interpolated_frequencies

def generate_sine_wave(frequencies, sample_rate):
    t = np.arange(len(frequencies)) / sample_rate
    phase = np.cumsum(2 * np.pi * frequencies / sample_rate)
    wave = np.sin(phase)
    return wave

def plot_pitch_frequencies(file_path, x1, dx, target_sample_rate):
    frames_data = parse_praat_pitch_file(file_path)
    times = calculate_times(frames_data, x1, dx)
    primary_frequencies = [frame['candidates'][0]['frequency'] for frame in frames_data]

    plt.figure(figsize=(10, 6))
    plt.plot(times, primary_frequencies, 'o', label='Original Pitch Data', color='b')
    
    new_times, interpolated_frequencies = interpolate_pitch(times, primary_frequencies, target_sample_rate)
    plt.plot(new_times, interpolated_frequencies, label='Interpolated Pitch Curve', color='r')
    
    plt.xlabel('Time (seconds)')
    plt.ylabel('Pitch Frequency (Hz)')
    plt.title('Pitch Frequencies Over Time')
    plt.legend()
    plt.grid(True)
    plt.show()
    
    return new_times, interpolated_frequencies

def save_interpolated_data_to_json(times, frequencies, file_path):
    data = list(zip(times.tolist(), frequencies.tolist()))
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    
# Example usage:
file_path = 'input_audio.Pitch'  # Replace with your file path
x1 = 0.030895833333333393
dx = 0.015
target_sample_rate = 44100  # Desired sample rate for the output

new_times, interpolated_frequencies = plot_pitch_frequencies(file_path, x1, dx, target_sample_rate)

# Save interpolated data to a JSON file
json_output_path = 'interpolated_pitch_data.json'
save_interpolated_data_to_json(new_times, interpolated_frequencies, json_output_path)

# Generate sine wave based on the interpolated frequencies
sine_wave = generate_sine_wave(interpolated_frequencies, target_sample_rate)

# Save the sine wave as an audio file
sf.write('pitch_only_audio_manually.wav', sine_wave, target_sample_rate)

# Plot the generated sine wave
plt.figure(figsize=(12, 6))
plt.plot(np.arange(len(sine_wave)) / target_sample_rate, sine_wave, label='Generated Sine Wave')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')
plt.title('Generated Sine Waveform')
plt.legend()
plt.show()

print(f"Pitch-only audio saved as pitch_only_audio_manually.wav")
print(f"Interpolated pitch data saved as {json_output_path}")
