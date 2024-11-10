import pygame
import math
import random
import colorsys
import numpy as np
from pydub import AudioSegment
from pygame import Color

pygame.init()

width, height = 800, 600  # Increased width for better bar spacing
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Sound Visualization")

def lerp(start, end, t):
    return start + (end - start) * t

# Load and process audio
audio = AudioSegment.from_file('song.mp3')  # Replace with your song file
samples = np.array(audio.get_array_of_samples())

# Handle stereo audio
if audio.channels == 2:
    samples = samples.reshape((-1, 2))
    samples = samples.mean(axis=1)  # Convert to mono

samples = samples / np.max(np.abs(samples))  # Normalize samples
sample_rate = audio.frame_rate

# Prepare audio playback
pygame.mixer.init(frequency=sample_rate)
pygame.mixer.music.load('song.mp3')

# Audio processing parameters
frame_duration = 1 / 60  # 60 FPS
samples_per_frame = int(frame_duration * sample_rate)
audio_position = 0

# Visualization parameters
num_bars = 80
max_freq = sample_rate / 2
freqs = np.linspace(0, max_freq, num_bars + 1)

running = True
clock = pygame.time.Clock()

# Start playing the music
pygame.mixer.music.play()

while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Clear the screen
    screen.fill((0, 0, 0))

    # Calculate the current audio chunk
    chunk = samples[audio_position:audio_position + samples_per_frame]
    audio_position += samples_per_frame

    # If we've reached the end of the audio, loop back
    if audio_position >= len(samples):
        audio_position = 0
        pygame.mixer.music.play()

    # Perform FFT on the chunk
    fft_result = np.fft.fft(chunk)
    fft_freq = np.fft.fftfreq(len(chunk), d=1 / sample_rate)

    # Get the magnitude of the frequencies
    magnitudes = np.abs(fft_result)

    # Only consider the positive frequencies
    positive_freqs = fft_freq[:len(fft_freq) // 2]
    positive_magnitudes = magnitudes[:len(magnitudes) // 2]

    # Initialize an array to store magnitudes per band
    band_magnitudes = np.zeros(num_bars)

    for i in range(num_bars):
        # Find indices corresponding to the current band
        indices = np.where((positive_freqs >= freqs[i]) & (positive_freqs < freqs[i + 1]))[0]
        if len(indices) > 0:
            # Calculate the average magnitude for the band
            band_magnitudes[i] = np.mean(positive_magnitudes[indices])

    # Normalize magnitudes to the range [0, 1]
    if np.max(band_magnitudes) != 0:
        band_magnitudes /= np.max(band_magnitudes)
    else:
        band_magnitudes = np.zeros(num_bars)

    # Draw the bars
    bar_width = width / num_bars
    max_bar_height = height / 2  # Maximum height of the bars

    for i in range(num_bars):
        bar_x = i * bar_width
        bar_height = band_magnitudes[i] * max_bar_height
        bar_y = height - bar_height  # Draw from the bottom of the screen

        # Color mapping based on magnitude
        hue = i / num_bars
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, band_magnitudes[i])
        bar_color = (int(r * 255), int(g * 255), int(b * 255))

        pygame.draw.rect(screen, bar_color, (bar_x, bar_y, bar_width - 2, bar_height))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
