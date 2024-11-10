import os
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import math
import random
import colorsys
from pygame import Color
import numpy as np
from moviepy.video.io.ffmpeg_writer import FFMPEG_VideoWriter
from moviepy.editor import (
    AudioFileClip,
    VideoFileClip
)
import sys
import librosa

pygame.init()

# List of songs with their settings
videos_to_generate = [
    {
        'song_file': 'youtube_obWIUs6473M_audio.mp3',
        'video_duration': 60,  # Desired video duration in seconds
    },
    # Add more entries as needed
]

# Screen dimensions
width, height = 1080, 1920

# Video writer settings
fps = 60  # Frame rate

# Function to generate a random color
def random_color():
    return Color(
        random.randint(50, 255),
        random.randint(50, 255),
        random.randint(50, 255)
    )

# Function to linearly interpolate between two values
def lerp(start, end, t):
    return start + (end - start) * t

# Function to draw a radial gradient
def draw_radial_gradient(surface, center, radius, inner_color, outer_color):
    for i in range(int(radius), 0, -1):
        ratio = i / radius
        r = int(lerp(inner_color.r, outer_color.r, ratio))
        g = int(lerp(inner_color.g, outer_color.g, ratio))
        b = int(lerp(inner_color.b, outer_color.b, ratio))
        color = (r, g, b)
        pygame.draw.circle(surface, color, center, i)

# Function to update the progress bar
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

# Main loop to generate videos
for idx, video_settings in enumerate(videos_to_generate):
    # Extract settings
    song_filename = video_settings['song_file']
    video_duration = video_settings['video_duration']

    # Generate unique filenames
    base_name = os.path.splitext(os.path.basename(song_filename))[0]
    video_filename = f"{base_name}_no_audiob.mp4"  # Intermediate video without audio
    final_video_filename = f"{base_name}_with_audiob.mp4"  # Final video with synchronized audio

    # Load the song using librosa
    y, sr = librosa.load(song_filename)

    # Get the duration of the song
    song_duration = librosa.get_duration(y=y, sr=sr)

    # If the song duration is shorter than the video duration, use the song duration
    if song_duration < video_duration:
        video_duration = song_duration

    # Analyze the song to extract beats
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    # Extract scalar value from tempo
    tempo = float(tempo)

    # Filter beat_times to only include times within the video duration
    beat_times = beat_times[beat_times <= video_duration]

    # Print some info
    print(f"Song Tempo: {tempo:.2f} BPM")
    print(f"Number of Beats: {len(beat_times)}")

    # Determine the number of balls based on the tempo
    if tempo < 60:
        num_balls = 1
    elif tempo < 90:
        num_balls = 2
    elif tempo < 120:
        num_balls = 3
    elif tempo < 150:
        num_balls = 4
    else:
        num_balls = 5

    print(f"Number of Balls: {num_balls}")

    # Adjust ball speed based on tempo
    # We'll set a base speed and scale it with tempo
    base_speed = tempo / 60  # Normalize tempo to a factor

    # Create a new off-screen surface for each video
    screen = pygame.Surface((width, height))

    # Background gradient colors (black to marine blue)
    background_top_color = (0, 0, 0)       # Black
    background_bottom_color = (0, 0, 128)  # Marine Blue

    # Function to draw gradient background
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

    # Initialize boundary circle variables
    margin = 50  # Margin to prevent touching edges
    boundary_radius = min(width, height) // 2 - margin
    boundary_center = (width // 2, height // 2)
    max_radius = boundary_radius

    # Initialize balls
    balls = []
    for i in range(num_balls):
        speed_multiplier = base_speed  # Adjust speed based on tempo
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(5, 10) * speed_multiplier
        speed_x = math.cos(angle) * speed
        speed_y = math.sin(angle) * speed

        # Place balls randomly inside the boundary circle
        r = random.uniform(0, boundary_radius - 100)
        theta = random.uniform(0, 2 * math.pi)
        x = boundary_center[0] + r * math.cos(theta)
        y = boundary_center[1] + r * math.sin(theta)

        ball = {
            'radius': 20,
            'x': x,
            'y': y,
            'speed_x': speed_x,
            'speed_y': speed_y,
            'color': random_color(),
            'bounce_times': [],  # To be filled later
            'particles': [],     # Particle effects
            'initial_radius': 20,
            'expansion_rate': 1.10,
        }
        balls.append(ball)

    # Assign bounce times to balls
    for idx, time in enumerate(beat_times):
        ball_index = idx % num_balls
        balls[ball_index]['bounce_times'].append(time)

    # Initialize the video writer (without audio)
    video_writer = FFMPEG_VideoWriter(
        video_filename, (width, height), fps=fps, codec="libx264", preset='medium',
        threads=None, ffmpeg_params=['-pix_fmt', 'yuv420p']
    )

    # Initialize clock and frame count
    clock = pygame.time.Clock()
    frame_count = 0

    # Main rendering loop
    running = True
    while running:
        # Limit frame rate
        clock.tick(fps)
        # Corrected time calculation based on frame count
        t = frame_count / fps  # Current time in seconds

        # Draw gradient background
        draw_gradient_background(screen, background_top_color, background_bottom_color)

        # Draw the boundary with pulsing colors
        hue_speed = 0.1  # Adjust this value for faster or slower color changes
        hue = (t * hue_speed) % 1.0
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        boundary_color = (int(r * 255), int(g * 255), int(b * 255))
        pygame.draw.circle(screen, boundary_color, boundary_center, boundary_radius, 2)

        # Update and draw each ball
        for ball in balls[:]:  # Use a copy of the list in case we need to modify it
            # Check if it's time for the ball to bounce
            if ball['bounce_times'] and t >= ball['bounce_times'][0]:
                # Remove the bounce time from the list
                ball['bounce_times'].pop(0)
                # Reverse the speed to simulate bounce
                # Calculate the normal vector at the point of collision
                dx = ball['x'] - boundary_center[0]
                dy = ball['y'] - boundary_center[1]
                distance_from_center = math.hypot(dx, dy)

                normal_x = dx / distance_from_center
                normal_y = dy / distance_from_center

                # Reflect the velocity vector over the normal vector
                dot_product = ball['speed_x'] * normal_x + ball['speed_y'] * normal_y
                ball['speed_x'] -= 2 * dot_product * normal_x
                ball['speed_y'] -= 2 * dot_product * normal_y

                # Increase the radius without shrinking
                ball['radius'] = min(ball['radius'] * ball['expansion_rate'], max_radius)

                # Adjust position to prevent overlap
                overlap = distance_from_center + ball['radius'] - boundary_radius
                if overlap > 0:
                    ball['x'] -= normal_x * overlap
                    ball['y'] -= normal_y * overlap

                # Add visual effects here (e.g., change color, particles)
                ball['color'] = random_color()
                # Create particles
                for _ in range(20):
                    particle = {
                        'x': ball['x'],
                        'y': ball['y'],
                        'vx': random.uniform(-5, 5),
                        'vy': random.uniform(-5, 5),
                        'life': random.randint(20, 40),
                        'color': ball['color'],
                    }
                    ball['particles'].append(particle)

                # Check if the ball's radius has reached the maximum radius
                if ball['radius'] >= max_radius:
                    running = False  # Exit the main loop

            # Update ball position
            ball['x'] += ball['speed_x']
            ball['y'] += ball['speed_y']

            # Calculate the distance from the ball's center to the boundary center
            dx = ball['x'] - boundary_center[0]
            dy = ball['y'] - boundary_center[1]
            distance_from_center = math.hypot(dx, dy)

            # Collision detection with boundary circle
            if distance_from_center + ball['radius'] >= boundary_radius:
                # Calculate the normal vector at the point of collision
                normal_x = dx / distance_from_center
                normal_y = dy / distance_from_center

                # Reflect the velocity vector over the normal vector
                dot_product = ball['speed_x'] * normal_x + ball['speed_y'] * normal_y
                ball['speed_x'] -= 2 * dot_product * normal_x
                ball['speed_y'] -= 2 * dot_product * normal_y

                # Adjust position to prevent overlap
                overlap = distance_from_center + ball['radius'] - boundary_radius
                if overlap > 0:
                    ball['x'] -= normal_x * overlap
                    ball['y'] -= normal_y * overlap

            # Update and draw particles
            for particle in ball['particles'][:]:
                particle['x'] += particle['vx']
                particle['y'] += particle['vy']
                particle['life'] -= 1
                if particle['life'] <= 0:
                    ball['particles'].remove(particle)
                    continue
                alpha = int(255 * (particle['life'] / 40))
                particle_color = (particle['color'].r, particle['color'].g, particle['color'].b, alpha)
                particle_surface = pygame.Surface((4, 4), pygame.SRCALPHA)
                pygame.draw.circle(particle_surface, particle_color, (2, 2), 2)
                screen.blit(particle_surface, (particle['x'], particle['y']))

            # Draw the ball with radial gradient
            circle_surface = pygame.Surface((ball['radius'] * 2, ball['radius'] * 2), pygame.SRCALPHA)
            draw_radial_gradient(
                circle_surface,
                (int(ball['radius']), int(ball['radius'])),
                int(ball['radius']),
                Color(255, 255, 255),  # Inner color
                ball['color']          # Outer color
            )
            screen.blit(circle_surface, (ball['x'] - ball['radius'], ball['y'] - ball['radius']))

        # Convert Pygame surface to RGB array
        frame = pygame.surfarray.array3d(screen)
        frame = frame.swapaxes(0, 1)  # Convert from (width, height, channels) to (height, width, channels)

        # Write frame to video
        video_writer.write_frame(frame)

        # Update frame count
        frame_count += 1

        # Update the progress bar every 10 frames to reduce terminal output
        if frame_count % 10 == 0:
            # Calculate progress based on the largest ball's radius
            max_ball_radius = max(ball['radius'] for ball in balls)
            progress = (max_ball_radius - balls[0]['initial_radius']) / (max_radius - balls[0]['initial_radius'])
            progress = max(0.0, min(progress, 1.0))  # Ensure progress stays within [0, 1]
            update_progress_bar(progress)

    # Finalize the video
    video_writer.close()
    pygame.quit()

    # Ensure the progress bar is complete
    update_progress_bar(1.0)
    print()  # Move to a new line

    # Load the video without audio
    video_clip = VideoFileClip(video_filename)

    # Load and trim the song to match the video's duration
    audio_clip = AudioFileClip(song_filename).subclip(0, video_clip.duration)

    # Set the audio of the video clip
    video_with_audio = video_clip.set_audio(audio_clip)

    # Write the final video with audio
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

    print(f"Video '{final_video_filename}' has been generated.\n")

print("All videos have been generated.")
