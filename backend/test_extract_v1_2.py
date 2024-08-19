import parselmouth
import numpy as np
import matplotlib.pyplot as plt
import soundfile as sf
import textgrid
from scipy.interpolate import interp1d
import csv

def frequency_to_semitones(frequencies, reference_frequency=85):
    """Convert frequency to semitones"""
    valid = frequencies > 0  # Filter out invalid frequency values
    semitones = np.zeros_like(frequencies)
    semitones[valid] = 12 * np.log2(frequencies[valid] / reference_frequency)
    semitones[~valid] = np.nan  # Set invalid frequency values to NaN
    return semitones

def semitones_to_frequency(semitones, reference_frequency=85):
    """Convert semitones to frequency"""
    frequencies = reference_frequency * 2**(semitones / 12)
    frequencies[np.isnan(semitones)] = 0  # Set NaN values to 0 Hz
    return frequencies

def extract_pitch(cropped_sound, start_time, end_time):
    """Extract pitch and convert to semitones"""
    pitch_floors = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    # pitch_floors = [100]
    pitch = None
    for pitch_floor in pitch_floors:
        print(pitch_floor)
        try:
            pitch = cropped_sound.to_pitch(time_step=0.001, pitch_floor=pitch_floor)
            break
        except parselmouth.PraatError:
            continue
    if pitch is None:
        print("Unable to extract pitch, skipping this file.")
        return None, None
    
    pitch_semitones = frequency_to_semitones(pitch.selected_array['frequency'])
    return pitch.xs(), pitch_semitones

def generate_sine_wave(frequencies, sample_rate):
    """Generate a sine wave for the given frequencies"""
    t = np.arange(len(frequencies)) / sample_rate
    phase = 2 * np.pi * np.cumsum(frequencies / sample_rate)
    wave = np.sin(phase)
    return wave

# Read audio file
audio_file = 'input_audio.wav'
signal, sample_rate = sf.read(audio_file)

# Create a Sound object for parselmouth
sound = parselmouth.Sound(audio_file)

# Read TextGrid file
tg = textgrid.TextGrid.fromFile('input_audio.TextGrid')
phones_tier = tg.getFirst('phones')

# Initialize pitch data
overall_times = np.arange(len(signal)) / sample_rate
overall_pitch_values = np.full_like(overall_times, np.nan)

# Iterate over each phoneme interval and extract pitch
for interval in phones_tier.intervals:
    print(interval)
    if interval.mark.strip() == "":
        continue
    start_time = interval.minTime
    end_time = interval.maxTime
    cropped_sound = sound.extract_part(from_time=start_time, to_time=end_time, preserve_times=True)
    
    # Extract pitch
    segment_times, segment_pitch_semitones = extract_pitch(cropped_sound, start_time, end_time)
    if segment_times is None or segment_pitch_semitones is None:
        continue
    
    # Interpolate segment pitch data to match the length of the overall timeline section
    start_index = int(start_time * sample_rate)
    end_index = int(end_time * sample_rate)
    if end_index > start_index:
        interpolated_pitch = np.interp(
            np.arange(start_index, end_index),
            np.linspace(start_index, end_index, len(segment_pitch_semitones)),
            segment_pitch_semitones
        )
        overall_pitch_values[start_index:end_index] = interpolated_pitch
        
        # Plot each phoneme's pitch data
        plt.figure(figsize=(12, 6))
        plt.plot(np.linspace(start_time, end_time, len(interpolated_pitch)), interpolated_pitch, label=f'Pitch (Semitones) for phoneme {interval.mark}', color='blue')
        plt.xlabel('Time (s)')
        plt.ylabel('Pitch (Semitones)')
        plt.title(f'Pitch Contour for phoneme {interval.mark}')
        plt.legend()
        plt.show()

# Convert semitones to frequency for overall pitch values
overall_frequencies = semitones_to_frequency(overall_pitch_values)

# Ensure frequencies reset to 0 after the last meaningful data point
last_valid_index = np.max(np.where(overall_frequencies > 0))
overall_frequencies[last_valid_index + 1:] = 0

# Plot overall pitch data
fig, ax = plt.subplots(figsize=(12, 8))

ax.plot(overall_times, overall_frequencies, label="Pitch (Frequency)", color='blue')
ax.set_ylabel("Frequency (Hz)")
ax.set_xlabel("Time [s]")
ax.set_title("Overall Pitch Contour")
ax.legend(loc='upper right')
plt.tight_layout()
plt.savefig("overall_pitch_contour.png")
plt.show()

print("Generation completed")

# Save the time and pitch data to a CSV file
with open("pitch_data.csv", mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Time (s)", "Pitch (Semitones)"])
    for time, pitch in zip(overall_times, overall_pitch_values):
        writer.writerow([time, pitch])

print("Pitch data saved to pitch_data.csv")

# Directly plot the data from the variables without reading the CSV file
plt.figure(figsize=(12, 6))
plt.plot(overall_times, overall_frequencies, label='Pitch (Frequency)', color='blue')
plt.xlabel('Time (s)')
plt.ylabel('Frequency (Hz)')
plt.title('Pitch Contour Directly from Variables')
plt.legend()
plt.show()
print(overall_frequencies.shape)
print(overall_frequencies.size)
# Generate sine wave based on the interpolated frequencies
sine_wave = generate_sine_wave(overall_frequencies, sample_rate)

# Save the sine wave as an audio file
sf.write('pitch_only_audio.wav', sine_wave, sample_rate)

# Plot the generated sine wave
plt.figure(figsize=(12, 6))
plt.plot(np.arange(len(sine_wave)) / sample_rate, sine_wave, label='Generated Sine Wave')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')
plt.title('Generated Sine Waveform')
plt.legend()
plt.show()

print("Pitch-only audio saved as pitch_only_audio.wav")
