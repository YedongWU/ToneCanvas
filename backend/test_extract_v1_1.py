import parselmouth
import numpy as np
import matplotlib.pyplot as plt
import soundfile as sf
import textgrid

def frequency_to_semitones(frequencies, reference_frequency=85):
    """Convert frequency to semitones"""
    valid = frequencies > 0  # Filter out invalid frequency values
    semitones = np.zeros_like(frequencies)
    semitones[valid] = 12 * np.log2(frequencies[valid] / reference_frequency)
    semitones[~valid] = np.nan  # Set invalid frequency values to NaN
    return semitones

def extract_pitch(cropped_sound, start_time, end_time):
    """Extract pitch and convert to semitones"""
    pitch_floors = [100, 75, 50, 25]
    pitch = None
    for pitch_floor in pitch_floors:
        try:
            pitch = cropped_sound.to_pitch(time_step=0.01, pitch_floor=pitch_floor)
            break
        except parselmouth.PraatError:
            continue
    if pitch is None:
        print("Unable to extract pitch, skipping this file.")
        return None, None
    
    pitch_semitones = frequency_to_semitones(pitch.selected_array['frequency'])
    return pitch.xs(), pitch_semitones

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
    
    # Align pitch data with overall timeline
    start_index = int(start_time * sample_rate / 100)  # Correct the calculation of start_index
    end_index = start_index + len(segment_pitch_semitones)
    overall_pitch_values[start_index:end_index] = segment_pitch_semitones

# Plot overall pitch data
fig, ax = plt.subplots(figsize=(12, 8))

ax.plot(overall_times, overall_pitch_values, label="Pitch (Semitones)", color='blue')
ax.set_ylabel("Semitones")
ax.set_xlabel("Time [s]")
ax.set_title("Overall Pitch Contour")
ax.legend(loc='upper right')
plt.tight_layout()
plt.savefig("overall_pitch_contour.png")
plt.show()

print("Generation completed")

import csv

# Print the time and pitch arrays
print("Times:", overall_times)
print("Pitch Values:", overall_pitch_values)

# Save the time and pitch data to a CSV file
with open("pitch_data.csv", mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Time (s)", "Pitch (Semitones)"])
    for time, pitch in zip(overall_times, overall_pitch_values):
        writer.writerow([time, pitch])

print("Pitch data saved to pitch_data.csv")