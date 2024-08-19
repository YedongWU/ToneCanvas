import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('TkAgg')

def parse_praat_pitch_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.readlines()

    frames_data = []

    # Variables to hold current frame data
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

    # Append the last frame if it exists
    if current_frame is not None:
        frames_data.append(current_frame)
    
    return frames_data

def calculate_times(frames_data, x1, dx):
    return [x1 + (frame['frame'] - 1) * dx for frame in frames_data]

def plot_pitch_frequencies(file_path, x1, dx):
    frames_data = parse_praat_pitch_file(file_path)
    times = calculate_times(frames_data, x1, dx)
    primary_frequencies = [frame['candidates'][0]['frequency'] for frame in frames_data]

    plt.figure(figsize=(10, 6))
    plt.plot(times, primary_frequencies, marker='o', linestyle='-', color='b')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Pitch Frequency (Hz)')
    plt.title('Pitch Frequencies Over Time')
    plt.grid(True)
    plt.show()

# Example usage:
file_path = 'input_audio.Pitch'  # Replace with your file path
x1 = 0.030895833333333393
dx = 0.015
plot_pitch_frequencies(file_path, x1, dx)
