import parselmouth
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import soundfile as sf
import textgrid
from scipy.interpolate import interp1d

def interpolate_to_uniform_length(times, data, num_points=100):
    """Interpolate data to a uniform length"""
    interpolated_data = []
    for time, datum in zip(times, data):
        # Handle NaN values by filling with the nearest valid data
        valid = ~np.isnan(datum)
        if not np.any(valid):
            continue
        time_valid = np.linspace(0, 100, num_points)
        interp_func = interp1d(np.linspace(0, 100, len(datum[valid])), datum[valid], kind='linear', fill_value="extrapolate")
        interpolated_data.append(interp_func(time_valid))
    return time_valid, interpolated_data

def plot_pitch(ax, times, pitches_semitones, labels, num_points=100, ylim=None):
    """Plot overlapping pitch (semitones) using a single y-axis"""
    time_valid, interpolated_data = interpolate_to_uniform_length(times, pitches_semitones, num_points)
    for pitch_semitones_interp, label in zip(interpolated_data, labels):
        ax.plot(time_valid, pitch_semitones_interp, label=label, alpha=0.5)

    ax.set_ylabel("Semitones", fontsize=8)
    ax.set_title("Semitones", fontsize=10)
    ax.legend(loc='upper left', fontsize=8)
    if ylim:
        ax.set_ylim(ylim)
    
    # Set proportionate x-axis
    ax.set_xlim(0, 100)
    ax.set_xlabel("Proportion [%]", fontsize=8)

    return ax

def frequency_to_semitones(frequencies, reference_frequency=85):
    """Convert frequency to semitones"""
    valid = frequencies > 0  # Filter out invalid frequency values
    semitones = np.zeros_like(frequencies)
    semitones[valid] = 12 * np.log2(frequencies[valid] / reference_frequency)
    semitones[~valid] = np.nan  # Set invalid frequency values to NaN
    return semitones

def plot_temporary_waveform_and_pitch(cropped_sound, start_time, end_time):
    """Plot the waveform and pitch of a temporary audio segment"""
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
    
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    # Plot waveform
    axes[0].plot(np.linspace(start_time, end_time, len(cropped_sound.values.T)), cropped_sound.values.T, color='blue')
    axes[0].set_ylabel("Amplitude")
    axes[0].set_title(f"Temporary Cropped Waveform (from {start_time} to {end_time} s)")
    
    # Plot pitch
    axes[1].plot(np.linspace(start_time, end_time, len(pitch_semitones)), pitch_semitones, color='blue')
    axes[1].set_ylabel("Semitones")
    axes[1].set_xlabel("Time [s]")
    axes[1].set_title("Temporary Cropped Pitch")
    
    plt.tight_layout()
    plt.show()
    
    return pitch.xs(), pitch_semitones

# Read audio file
audio_file = 'input_audio.wav'
signal, sample_rate = sf.read(audio_file)

# Create a Sound object for parselmouth
sound = parselmouth.Sound(audio_file)

# Read TextGrid file
tg = textgrid.TextGrid.fromFile('input_audio.TextGrid')
phones_tier = tg.getFirst('phones')

# Get waveform data
x = np.arange(len(signal)) / sample_rate

# Initialize pitch data
pitch_values = np.full_like(x, np.nan)

# Iterate over each phoneme interval and extract pitch
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
    
    # Plot temporary waveform and pitch
    segment_times, segment_pitch_semitones = plot_temporary_waveform_and_pitch(cropped_sound, start_time, end_time)
    if segment_times is None or segment_pitch_semitones is None:
        continue
    
    # Save time and semitone data
    times.append(segment_times)
    pitches_semitones.append(segment_pitch_semitones)

# Plot all data
if times and pitches_semitones:
    fig, ax = plt.subplots(figsize=(12, 8))  # Adjust plot area height

    # Plot overlapping pitches (semitones)
    ax_pitch = plot_pitch(ax, times, pitches_semitones, ['Segment'] * len(times),
                          ylim=(np.nanmin([np.nanmin(p) for p in pitches_semitones]), 
                                np.nanmax([np.nanmax(p) for p in pitches_semitones])))

    # Adjust plot area position to ensure curves are close to the plot area boundary
    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

    # Adjust layout and show image
    plt.tight_layout()
    plt.savefig("cropped_comparison_output_image.png")
    print("Generation completed")
    plt.show()
else:
    print("No valid data for plotting.")
