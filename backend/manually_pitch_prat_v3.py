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
    x1, dx = None, None

    for line in content:
        line = line.strip()
        if line.startswith('x1 ='):
            x1 = float(line.split('=')[1].strip())
        elif line.startswith('dx ='):
            dx = float(line.split('=')[1].strip())
        elif line.startswith('frames [') and 'frames []' not in line:
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
    
    return frames_data, x1, dx

def calculate_times(frames_data, x1, dx):
    return [x1 + (frame['frame'] - 1) * dx for frame in frames_data]

def segment_nonzero_times_and_frequencies(times, frequencies):
    segments = []
    current_segment = {'times': [], 'frequencies': []}
    
    for time, frequency in zip(times, frequencies):
        if frequency > 0:
            current_segment['times'].append(time)
            current_segment['frequencies'].append(frequency)
        else:
            if current_segment['times']:
                segments.append(current_segment)
                current_segment = {'times': [], 'frequencies': []}
    
    if current_segment['times']:
        segments.append(current_segment)
    
    return segments

def interpolate_pitch_segments(segments, target_sample_rate):
    all_new_times = []
    all_interpolated_frequencies = []
    
    for segment in segments:
        times = np.array(segment['times'])
        frequencies = np.array(segment['frequencies'])
        
        # Create an interpolation function
        interpolation_function = interp1d(times, frequencies, kind='cubic', fill_value="extrapolate")
        
        # Generate new time points at the target sample rate
        segment_new_times = np.arange(times[0], times[-1], 1/target_sample_rate)
        
        # Interpolate frequencies at the new time points
        segment_interpolated_frequencies = interpolation_function(segment_new_times)
        
        all_new_times.append(segment_new_times)
        all_interpolated_frequencies.append(segment_interpolated_frequencies)
    
    return all_new_times, all_interpolated_frequencies

def generate_sine_wave(frequencies, sample_rate):
    frequencies = np.array(frequencies)  # Ensure frequencies is a NumPy array
    t = np.arange(len(frequencies)) / sample_rate
    phase = np.cumsum(2 * np.pi * frequencies / sample_rate)
    wave = np.sin(phase)
    return wave

def plot_pitch_frequencies(file_path, target_sample_rate):
    frames_data, x1, dx = parse_praat_pitch_file(file_path)
    times = calculate_times(frames_data, x1, dx)
    primary_frequencies = [frame['candidates'][0]['frequency'] for frame in frames_data]

    plt.figure(figsize=(10, 6))
    plt.plot(times, primary_frequencies, 'o', label='Original Pitch Data', color='b')
    
    segments = segment_nonzero_times_and_frequencies(times, primary_frequencies)
    all_new_times, all_interpolated_frequencies = interpolate_pitch_segments(segments, target_sample_rate)
    
    combined_times = []
    combined_frequencies = []

    previous_end_time = None

    for new_times, interpolated_frequencies in zip(all_new_times, all_interpolated_frequencies):
        if previous_end_time is not None and new_times[0] > previous_end_time:
            zero_times = np.arange(previous_end_time, new_times[0], 1/target_sample_rate)
            combined_times.extend(zero_times)
            combined_frequencies.extend(np.zeros_like(zero_times))
        
        combined_times.extend(new_times)
        combined_frequencies.extend(interpolated_frequencies)
        previous_end_time = new_times[-1]

    plt.plot(combined_times, combined_frequencies, label='Interpolated Pitch Curve', color='r')

    plt.xlabel('Time (seconds)')
    plt.ylabel('Pitch Frequency (Hz)')
    plt.title('Pitch Frequencies Over Time')
    plt.legend()
    plt.grid(True)
    plt.show()
    
    return np.array(combined_times), np.array(combined_frequencies)

def save_interpolated_data_to_json(times, frequencies, file_path):
    # Special mark frequencies of 0 as NaN
    data = [{'time': t, 'frequency': float(f) if f != 0 else 'NaN'} for t, f in zip(times, frequencies)]
    
    # Calculate max and min of non-zero frequencies
    non_zero_frequencies = [f for f in frequencies if f > 0]
    max_frequency = max(non_zero_frequencies)
    min_frequency = min(non_zero_frequencies)
    
    json_data = {
        'data': data,
        'max_frequency': max_frequency,
        'min_frequency': min_frequency
    }
    
    with open(file_path, 'w') as json_file:
        json.dump(json_data, json_file, indent=4)

# Example usage:
file_path = 'input_audio.Pitch'  # Use the uploaded file path
target_sample_rate = 44100  # Desired sample rate for the output

new_times, interpolated_frequencies = plot_pitch_frequencies(file_path, target_sample_rate)

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
