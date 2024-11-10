import os
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import math
import random
import colorsys
from pygame import Color
import numpy as np
from moviepy.video.io.ffmpeg_writer import FFMPEG_VideoWriter
from moviepy.editor import AudioFileClip, VideoFileClip
import sys

pygame.init()

# Screen dimensions
width, height = 1080, 1920
screen = pygame.Surface((width, height))

# Audio setup
audio_filename = 'song.ogg'  # Ensure this is in the same directory

# Video writer setup
fps = 60  # Frame rate
video_filename = "animation_no_audio.mp4"  # Intermediate video without audio
final_video_filename = "animation_with_audio.mp4"  # Final video with synchronized audio

# Colors
background_top_color = (15, 15, 60)
background_bottom_color = (30, 30, 30)

margin = 50  # Margin to prevent touching edges
boundary_radius = min(width, height) // 2 - margin
boundary_center = (width // 2, height // 2)

circle_radius = 20
initial_circle_radius = circle_radius  # Store the initial value
circle_x, circle_y = width // 2, height // 3
speed_x, speed_y = 10, 11
expansion_rate = 1.10
max_radius = boundary_radius

# Trail effect variables
trail = []
trail_length = 15

# Particle effect variables
particles = []

# Pulsating circles (pulses) list
pulses = []

# Color variables
current_color = Color(70, 130, 180)
target_color = current_color
color_transition_progress = 1.0
color_transition_speed = 0.02

# Hue for hue rotation
hue = 0.0

running = True
clock = pygame.time.Clock()

# Frame counter for progress bar update
frame_count = 0

def lerp(start, end, t):
    return start + (end - start) * t

def draw_radial_gradient(surface, center, radius, inner_color, outer_color):
    for i in range(int(radius), 0, -1):
        ratio = i / radius
        r = int(lerp(inner_color.r, outer_color.r, ratio))
        g = int(lerp(inner_color.g, outer_color.g, ratio))
        b = int(lerp(inner_color.b, outer_color.b, ratio))
        color = (r, g, b)
        pygame.draw.circle(surface, color, center, i)

def draw_gradient_background(surface, color_top, color_bottom):
    gradient_surface = pygame.Surface((1, height))  # Create a 1-pixel wide surface
    for y in range(height):
        ratio = y / height
        r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
        g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
        b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
        gradient_surface.set_at((0, y), (r, g, b))
    # Scale the 1-pixel wide gradient to the full width
    scaled_surface = pygame.transform.scale(gradient_surface, (width, height))
    surface.blit(scaled_surface, (0, 0))

def update_progress_bar(progress):
    bar_length = 50  # Length of the progress bar in characters
    status = ""

    if progress >= 1:
        progress = 1
        status = "Complete\r\n"
    elif progress < 0:
        progress = 0
        status = ""

    block = int(round(bar_length * progress))
    text = "\rRendering Video: [{0}] {1:.2%} {2}".format(
        "#" * block + "-" * (bar_length - block), progress, status)
    sys.stdout.write(text)
    sys.stdout.flush()

# Initialize the video writer (without audio)
video_writer = FFMPEG_VideoWriter(
    video_filename, (width, height), fps=fps, codec="libx264", preset='medium',
    threads=None, ffmpeg_params=['-pix_fmt', 'yuv420p']
)

while running:
    # Limit frame rate
    clock.tick(fps)
    t = pygame.time.get_ticks() / 1000  # Current time in seconds

    # Draw gradient background
    draw_gradient_background(screen, background_top_color, background_bottom_color)

    # Calculate hue for pulsing boundary color
    hue_speed = 0.1  # Adjust this value for faster or slower color changes
    hue = (t * hue_speed) % 1.0

    # Convert hue to RGB color
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    boundary_color = (int(r * 255), int(g * 255), int(b * 255))

    # Draw the boundary with pulsing colors
    pygame.draw.circle(screen, boundary_color, boundary_center, boundary_radius, 2)

    # Update the circle's position
    circle_x += speed_x
    circle_y += speed_y

    # Calculate the distance from the circle's center to the boundary center
    dx = circle_x - boundary_center[0]
    dy = circle_y - boundary_center[1]
    distance_from_center = math.hypot(dx, dy)

    # Collision detection based on circle edges
    if distance_from_center + circle_radius >= boundary_radius:
        # Calculate the normal vector at the point of collision
        normal_x = dx / distance_from_center
        normal_y = dy / distance_from_center

        # Reflect the velocity vector over the normal vector
        dot_product = speed_x * normal_x + speed_y * normal_y
        speed_x -= 2 * dot_product * normal_x
        speed_y -= 2 * dot_product * normal_y

        # Increase the radius without shrinking
        circle_radius = min(circle_radius * expansion_rate, max_radius)

        # Adjust position to prevent overlap
        overlap = distance_from_center + circle_radius - boundary_radius
        if overlap > 0:
            circle_x -= normal_x * overlap
            circle_y -= normal_y * overlap

        # Set a new random target color
        target_color = Color(
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        )
        color_transition_progress = 0.0

        # Generate particles with random colors
        for _ in range(20):
            particles.append({
                'x': circle_x,
                'y': circle_y,
                'vx': random.uniform(-5, 5),
                'vy': random.uniform(-5, 5),
                'life': random.randint(20, 40),
                'color': Color(
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255)
                )
            })

        # Add a new pulse at the collision point
        pulses.append({
            'x': circle_x,
            'y': circle_y,
            'radius': circle_radius,
            'max_radius': boundary_radius * 1.2,  # The pulse can grow slightly beyond the boundary
            'alpha': 255,
            'color': current_color
        })

    # Update color transition
    if color_transition_progress < 1.0:
        color_transition_progress += color_transition_speed
        if color_transition_progress > 1.0:
            color_transition_progress = 1.0

        # Interpolate colors
        r = lerp(current_color.r, target_color.r, color_transition_progress)
        g = lerp(current_color.g, target_color.g, color_transition_progress)
        b = lerp(current_color.b, target_color.b, color_transition_progress)
        current_color = Color(int(r), int(g), int(b))
    else:
        current_color = target_color

    # Update and draw pulses
    for pulse in pulses[:]:
        pulse['radius'] += 5  # Adjust for faster or slower expansion
        pulse['alpha'] -= 5   # Adjust for faster or slower fading
        if pulse['alpha'] <= 0 or pulse['radius'] >= pulse['max_radius']:
            pulses.remove(pulse)
            continue
        # Draw the pulse
        pulse_surface = pygame.Surface((pulse['radius'] * 2, pulse['radius'] * 2), pygame.SRCALPHA)
        pulse_alpha = int(pulse['alpha'])
        pulse_color = (pulse['color'].r, pulse['color'].g, pulse['color'].b, pulse_alpha)
        pygame.draw.circle(pulse_surface, pulse_color, (int(pulse['radius']), int(pulse['radius'])), int(pulse['radius']))
        screen.blit(pulse_surface, (pulse['x'] - pulse['radius'], pulse['y'] - pulse['radius']))

    # Update and draw particles
    for particle in particles[:]:
        particle['x'] += particle['vx']
        particle['y'] += particle['vy']
        particle['life'] -= 1
        if particle['life'] <= 0:
            particles.remove(particle)
            continue
        alpha = int(255 * (particle['life'] / 40))
        particle_color = (particle['color'].r, particle['color'].g, particle['color'].b, alpha)
        particle_surface = pygame.Surface((4, 4), pygame.SRCALPHA)
        pygame.draw.circle(particle_surface, particle_color, (2, 2), 2)
        screen.blit(particle_surface, (particle['x'], particle['y']))

    # Draw the trail
    trail.append((circle_x, circle_y, current_color))
    if len(trail) > trail_length:
        trail.pop(0)
    for i, (pos_x, pos_y, color) in enumerate(trail):
        trail_alpha = int(255 * (i + 1) / trail_length)
        trail_surface = pygame.Surface((circle_radius * 2, circle_radius * 2), pygame.SRCALPHA)
        trail_color = (color.r, color.g, color.b, trail_alpha)
        pygame.draw.circle(trail_surface, trail_color, (int(circle_radius), int(circle_radius)), int(circle_radius))
        screen.blit(trail_surface, (pos_x - circle_radius, pos_y - circle_radius))

    # Draw the moving circle with radial gradient
    circle_surface = pygame.Surface((circle_radius * 2, circle_radius * 2), pygame.SRCALPHA)
    draw_radial_gradient(
        circle_surface,
        (int(circle_radius), int(circle_radius)),
        int(circle_radius),
        Color(255, 255, 255),  # Inner color
        current_color          # Outer color
    )
    screen.blit(circle_surface, (circle_x - circle_radius, circle_y - circle_radius))

    # Convert Pygame surface to RGB array
    frame = pygame.surfarray.array3d(screen)
    frame = frame.swapaxes(0, 1)  # Convert from (width, height, channels) to (height, width, channels)

    # Write frame to video
    video_writer.write_frame(frame)

    # Update frame count
    frame_count += 1

    # Calculate progress based on the circle's radius
    progress = (circle_radius - initial_circle_radius) / (boundary_radius - initial_circle_radius)
    progress = max(0.0, min(progress, 1.0))  # Ensure progress stays within [0, 1]

    # Update the progress bar every 10 frames to reduce terminal output
    if frame_count % 10 == 0:
        update_progress_bar(progress)

    # Check if the circle's radius has reached the boundary's radius
    if circle_radius >= boundary_radius:
        running = False  # Exit the main loop

# Finalize the video
video_writer.close()
pygame.quit()

# Ensure the progress bar is complete
update_progress_bar(1.0)
print()  # Move to a new line

# Load the video without audio
video_clip = VideoFileClip(video_filename)

# Get the duration of the video
video_duration = video_clip.duration

# Load and trim the audio to match the video's duration
audio_clip = AudioFileClip(audio_filename).subclip(0, video_duration)

# Set the audio of the video clip
video_with_audio = video_clip.set_audio(audio_clip)

# Write the final video with audio (MoviePy shows its own progress bar)
video_with_audio.write_videofile(
    final_video_filename,
    codec="libx264",
    audio_codec='aac',
    preset='medium',
    threads=None,
    ffmpeg_params=['-pix_fmt', 'yuv420p']
)

# Optionally, delete the intermediate video file without audio
os.remove(video_filename)
