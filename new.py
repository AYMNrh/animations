import pygame
import math
import random
import colorsys
from pygame import Color

pygame.init()

width, height = 600, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Bouncing Circle Animation")

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

# Colors
background_top_color = (15, 15, 60)
background_bottom_color = (30, 30, 30)

boundary_radius = 250
boundary_center = (width // 2, height // 2)

circle_radius = 20
circle_x, circle_y = width // 2, height // 3
speed_x, speed_y = 10, 11
expansion_rate = 1.10
max_radius = boundary_radius

pygame.mixer.init()
pygame.mixer.music.load('song.mp3')  # Replace with your song file

current_pos = 0.0
segment_duration = 0.5
MUSIC_PAUSE_EVENT = pygame.USEREVENT + 1

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

def draw_gradient_background(screen, color_top, color_bottom):
    rect = pygame.Rect(0, 0, width, height)
    gradient_surface = pygame.Surface((2, height))
    for y in range(height):
        ratio = y / height
        r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
        g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
        b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
        gradient_surface.set_at((0, y), (r, g, b))
        gradient_surface.set_at((1, y), (r, g, b))
    scaled_surface = pygame.transform.smoothscale(gradient_surface, (width, height))
    screen.blit(scaled_surface, (0, 0))

while running:
    # Draw gradient background
    draw_gradient_background(screen, background_top_color, background_bottom_color)

    # Get the current time in seconds
    current_time = pygame.time.get_ticks() / 1000

    # Calculate hue for pulsing boundary color
    hue_speed = 0.1  # Adjust this value for faster or slower color changes
    hue = (current_time * hue_speed) % 1.0

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

        # Play the next segment of the song
        pygame.time.set_timer(MUSIC_PAUSE_EVENT, 0)
        pygame.mixer.music.stop()
        pygame.mixer.music.play(loops=0, start=current_pos)
        pygame.time.set_timer(MUSIC_PAUSE_EVENT, int(segment_duration * 1000), loops=1)
        current_pos += segment_duration

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

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == MUSIC_PAUSE_EVENT:
            pygame.mixer.music.pause()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
