import pygame
import math

pygame.init()

width, height = 600, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Bouncing Circle Animation")

background_color = (30, 30, 30)
circle_color = (70, 130, 180)
boundary_color = (255, 255, 255)

boundary_radius = 250
boundary_center = (width // 2, height // 2)

circle_radius = 20
circle_x, circle_y = width // 2, height // 3
speed_x, speed_y = 10, 11
expansion_rate = 1.10
max_radius = boundary_radius

pygame.mixer.init()
sound = pygame.mixer.Sound('bounce.wav')

running = True
clock = pygame.time.Clock()

while running:
    screen.fill(background_color)

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

        sound.play()

    # Draw the moving circle
    pygame.draw.circle(screen, circle_color, (int(circle_x), int(circle_y)), int(circle_radius))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
