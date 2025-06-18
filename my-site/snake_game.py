import pygame
import random
import sys

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 600, 400
TILE_SIZE = 20

# Colors
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)

# Fonts
title_font = pygame.font.SysFont('Arial', 40, bold=True)
score_font = pygame.font.SysFont('Arial', 20)
level_font = pygame.font.SysFont('Arial', 18)

# Set up display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Snake Game')

# Clock
clock = pygame.time.Clock()

def draw_text(text, font, color, surface, x, y, center=False):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    if center:
        textrect.midtop = (x, y)
    else:
        textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

def random_position():
    return (random.randrange(0, WIDTH, TILE_SIZE), random.randrange(0, HEIGHT, TILE_SIZE))

def main():
    snake = [(WIDTH // 2, HEIGHT // 2)]
    direction = (0, -TILE_SIZE)
    meal = random_position()
    score = 0
    level = 1
    speed = 10

    running = True
    while running:
        clock.tick(speed + (level - 1) * 2)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and direction != (0, TILE_SIZE):
                    direction = (0, -TILE_SIZE)
                elif event.key == pygame.K_DOWN and direction != (0, -TILE_SIZE):
                    direction = (0, TILE_SIZE)
                elif event.key == pygame.K_LEFT and direction != (TILE_SIZE, 0):
                    direction = (-TILE_SIZE, 0)
                elif event.key == pygame.K_RIGHT and direction != (-TILE_SIZE, 0):
                    direction = (TILE_SIZE, 0)

        # Move snake
        new_head = ((snake[0][0] + direction[0]) % WIDTH, (snake[0][1] + direction[1]) % HEIGHT)
        if new_head in snake:
            running = False  # End game on self-collision
            continue
        snake.insert(0, new_head)

        # Check for meal
        if new_head == meal:
            score += 1
            if score % 10 == 0:
                level += 1
            meal = random_position()
            while meal in snake:
                meal = random_position()
        else:
            snake.pop()

        # Draw everything
        screen.fill(BLACK)
        # Draw title
        draw_text('Snake Game', title_font, WHITE, screen, WIDTH // 2, 10, center=True)
        # Draw score and level
        draw_text(f'Score: {score}', score_font, WHITE, screen, WIDTH - 120, 10)
        draw_text(f'Level: {level}', level_font, WHITE, screen, WIDTH - 120, 35)
        # Draw meal
        pygame.draw.rect(screen, RED, (*meal, TILE_SIZE, TILE_SIZE))
        # Draw snake
        for segment in snake:
            pygame.draw.rect(screen, GREEN, (*segment, TILE_SIZE, TILE_SIZE))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()