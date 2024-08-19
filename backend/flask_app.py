from flask import Flask, send_from_directory, jsonify, request, send_file
from flask_cors import CORS
import os
import numpy as np
import matplotlib.pyplot as plt
import soundfile as sf
from scipy.interpolate import interp1d
import json

app = Flask(__name__)
CORS(app)  # 启用CORS

corpus_dir = os.path.join(os.path.dirname(__file__), 'corpus')
icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
temp_dir = os.path.join(os.path.dirname(__file__), 'temp')

if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

files = [f for f in os.listdir(corpus_dir) if f.endswith('.wav')]
current_index = 0

@app.route('/api/get-wav-file', methods=['GET'])
def get_wav_file():
    global current_index
    if not files:
        return "No wav files found", 404

    file_to_play = files[current_index]
    return send_from_directory(corpus_dir, file_to_play)

@app.route('/api/switch-wav-file', methods=['POST'])
def switch_wav_file():
    global current_index
    current_index = (current_index + 1) % len(files)
    return jsonify(currentIndex=current_index)

@app.route('/api/get-icon/<filename>', methods=['GET'])
def get_icon(filename):
    return send_from_directory(icons_dir, filename)

@app.route('/api/get-pitch-json', methods=['GET'])
def get_pitch_json():
    global current_index
    if not files:
        return "No wav files found", 404

    pitch_file = os.path.join(corpus_dir, files[current_index].replace('.wav', '.Pitch'))
    if not os.path.exists(pitch_file):
        return "No pitch file found for the current wav file", 404

    target_sample_rate = 100  # Desired sample rate for the output
    new_times, interpolated_frequencies = process_pitch_file(pitch_file, target_sample_rate)

    json_output_path = os.path.join(temp_dir, 'interpolated_pitch_data.json')
    save_interpolated_data_to_json(new_times, interpolated_frequencies, json_output_path)
    
    return send_file(json_output_path, as_attachment=True)

@app.route('/api/get-pitch-audio', methods=['GET'])
def get_pitch_audio():
    global current_index
    if not files:
        return "No wav files found", 404

    pitch_file = os.path.join(corpus_dir, files[current_index].replace('.wav', '.Pitch'))
    if not os.path.exists(pitch_file):
        return "No pitch file found for the current wav file", 404

    target_sample_rate = 44100  # Desired sample rate for the output
    new_times, interpolated_frequencies = process_pitch_file(pitch_file, target_sample_rate)

    sine_wave = generate_sine_wave(interpolated_frequencies, target_sample_rate)
    audio_output_path = os.path.join(temp_dir, 'pitch_only_audio_manually.wav')
    sf.write(audio_output_path, sine_wave, target_sample_rate)
    
    return send_file(audio_output_path, as_attachment=True)

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

def process_pitch_file(file_path, target_sample_rate):
    frames_data, x1, dx = parse_praat_pitch_file(file_path)
    times = calculate_times(frames_data, x1, dx)
    primary_frequencies = [frame['candidates'][0]['frequency'] for frame in frames_data]

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
    
    return np.array(combined_times), np.array(combined_frequencies)

def save_interpolated_data_to_json(times, frequencies, file_path):
    # Special mark frequencies of 0 as NaN
    data = [{'time': t, 'frequency': float(f) if f != 0 else 'NaN'} for t, f in zip(times, frequencies)]
    
    # Calculate max and min of non-zero frequencies
    non_zero_frequencies = [f for f in frequencies if f > 0]
    max_frequency = max(non_zero_frequencies)
    min_frequency = min(non_zero_frequencies)
    
    json_data = {
        'max_frequency': max_frequency,
        'min_frequency': min_frequency,
        'data': data
    }
    
    with open(file_path, 'w') as json_file:
        json.dump(json_data, json_file, indent=4)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
