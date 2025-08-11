"""
Spartan - a retro-style top-down shooter in one file (Pygame).
Features:
 - Player with movement and shooting
 - Enemies spawning with increasing difficulty
 - Scoring and persistent high score (highscore.txt)
 - Lives and HUD
 - Pause, menus, and game over screen
 - Powerups, particle explosions
 - SECRET MODE (unlimited lives): type "spartan" during play/menu
"""

import pygame
import random
import math
import os
from collections import deque

# -------- CONFIG -----------
WIDTH, HEIGHT = 800, 600
FPS = 60
PLAYER_SPEED = 5
BULLET_SPEED = 10
ENEMY_SPEED_BASE = 1.0
SPAWN_BASE_INTERVAL = 120  # frames
HIGH_SCORE_FILE = "highscore.txt"
SECRET_CODE = "spartan"
# ---------------------------

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Spartan")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Consolas", 20)
bigfont = pygame.font.SysFont("Consolas", 48)

# Utility functions
def load_highscore():
    try:
        with open(HIGH_SCORE_FILE, "r") as f:
            return int(f.read().strip())
    except:
        return 0

def save_highscore(score):
    try:
        with open(HIGH_SCORE_FILE, "w") as f:
            f.write(str(score))
    except:
        pass

def draw_text(surf, text, x, y, size=20, color=(255,255,255)):
    f = pygame.font.SysFont("Consolas", size)
    surf.blit(f.render(text, True, color), (x,y))

# Simple particle system (small circles)
particles = []
def spawn_particles(x,y,amount=12,color=(255,200,50)):
    for _ in range(amount):
        vel = [random.uniform(-3,3), random.uniform(-3,3)]
        life = random.randint(20,50)
        particles.append({"pos":[x,y], "vel":vel, "life":life, "color":color})

def update_particles():
    for p in particles[:]:
        p["life"] -= 1
        if p["life"] <= 0:
            particles.remove(p)
            continue
        p["pos"][0] += p["vel"][0]
        p["pos"][1] += p["vel"][1]
        # fade
        alpha = max(0, int(255 * (p["life"]/50)))
        r,g,b = p["color"]
        surf = pygame.Surface((4,4), pygame.SRCALPHA)
        surf.fill((r,g,b,alpha))
        screen.blit(surf, (p["pos"][0], p["pos"][1]))

# Entities
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.surf = pygame.Surface((36, 24), pygame.SRCALPHA)
        pygame.draw.polygon(self.surf, (80,160,255), [(0,24),(18,0),(36,24)])
        self.rect = self.surf.get_rect(center=(WIDTH//2, HEIGHT-60))
        self.speed = PLAYER_SPEED
        self.cooldown = 0
        self.lives = 3
        self.score = 0
        self.invuln = 0
        self.power = 1  # bullet power
    def update(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.rect.y += self.speed
        self.rect.clamp_ip(pygame.Rect(0,0,WIDTH,HEIGHT))
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.invuln > 0:
            self.invuln -= 1
    def shoot(self):
        if self.cooldown == 0:
            self.cooldown = max(10, 20 - 2*self.power)
            bullets.add(Bullet(self.rect.centerx, self.rect.top, -BULLET_SPEED, owner="player", power=self.power))
            if self.power >= 2:
                bullets.add(Bullet(self.rect.centerx-12, self.rect.top, -BULLET_SPEED, owner="player", power=1))
                bullets.add(Bullet(self.rect.centerx+12, self.rect.top, -BULLET_SPEED, owner="player", power=1))

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, vy, owner="player", power=1):
        super().__init__()
        self.owner = owner
        self.power = power
        self.vy = vy
        self.image = pygame.Surface((4 + power*2, 8 + power*2), pygame.SRCALPHA)
        color = (255,255,100) if owner=="player" else (255,100,100)
        pygame.draw.rect(self.image, color, self.image.get_rect())
        self.rect = self.image.get_rect(center=(x,y))
    def update(self):
        self.rect.y += self.vy
        if self.rect.bottom < 0 or self.rect.top > HEIGHT:
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, vx, vy, hp=1, score_value=10, color=(255,80,80), size=28):
        super().__init__()
        self.hp = hp
        self.vx = vx
        self.vy = vy
        self.score_value = score_value
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (size//2, size//2), size//2)
        self.rect = self.image.get_rect(center=(x,y))
    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if self.rect.top > HEIGHT + 50 or self.rect.left < -100 or self.rect.right > WIDTH + 100:
            self.kill()

class Powerup(pygame.sprite.Sprite):
    def __init__(self, x, y, kind="life"):
        super().__init__()
        self.kind = kind
        self.image = pygame.Surface((18,18), pygame.SRCALPHA)
        color = (100,255,100) if kind=="life" else (255,255,100)
        pygame.draw.rect(self.image, color, self.image.get_rect())
        self.rect = self.image.get_rect(center=(x,y))
        self.vy = 2
    def update(self):
        self.rect.y += self.vy
        if self.rect.top > HEIGHT:
            self.kill()

# Sprites groups
player = Player()
bullets = pygame.sprite.Group()
enemies = pygame.sprite.Group()
powerups = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()
all_sprites.add(player)

# Game state
running = True
paused = False
state = "menu"  # menu, playing, gameover
frame = 0
spawn_timer = SPAWN_BASE_INTERVAL
level = 1
highscore = load_highscore()
secret_buffer = deque(maxlen=len(SECRET_CODE))
god_mode = False

# Enemy spawning logic
def spawn_enemy_wave(level):
    # spawn mixture: normal, fast, tank
    for _ in range(max(1, level//2)):
        x = random.randint(20, WIDTH-20)
        y = -20
        vx = random.uniform(-0.6,0.6) * (1 + level*0.02)
        vy = ENEMY_SPEED_BASE + random.random()*0.5 + level*0.1
        e = Enemy(x,y,vx,vy,hp=1,score_value=10, color=(255,120,120), size=22)
        enemies.add(e)
    # occasional tank
    if random.random() < min(0.35, level*0.03):
        x = random.randint(40, WIDTH-40)
        y = -40
        vx = random.uniform(-0.3,0.3)
        vy = ENEMY_SPEED_BASE*0.6 + level*0.05
        tank = Enemy(x,y,vx,vy,hp=3,score_value=40, color=(200,80,200), size=40)
        enemies.add(tank)

def spawn_powerup(x,y):
    kind = random.choice(["life","power"])
    pu = Powerup(x,y,kind=kind)
    powerups.add(pu)

# Collision handling
def handle_collisions():
    global god_mode
    # player bullets hit enemies
    hits = pygame.sprite.groupcollide(enemies, bullets, False, True, collided=pygame.sprite.collide_mask if False else None)
    for e, blist in hits.items():
        for b in blist:
            if b.owner == "player":
                e.hp -= b.power
                spawn_particles(b.rect.centerx, b.rect.centery, amount=6, color=(255,220,80))
                if e.hp <= 0:
                    player.score += e.score_value
                    spawn_particles(e.rect.centerx, e.rect.centery, amount=18, color=(255,80,80))
                    # chance to drop powerup
                    if random.random() < 0.12:
                        spawn_powerup(e.rect.centerx, e.rect.centery)
                    e.kill()
    # enemy bullets (if any) hit player - (we don't have enemy bullets now)
    # enemies touch player
    if player.invuln <= 0 and not god_mode:
        collided = pygame.sprite.spritecollide(player, enemies, True, pygame.sprite.collide_rect)
        if collided:
            player.lives -= 1
            player.invuln = 90
            spawn_particles(player.rect.centerx, player.rect.centery, amount=24, color=(255,255,255))
            if player.lives <= 0:
                return "dead"
    # player picks powerup
    pu_hits = pygame.sprite.spritecollide(player, powerups, True)
    for pu in pu_hits:
        if pu.kind == "life":
            player.lives += 1
        else:
            player.power = min(3, player.power + 1)
    return "alive"

# Menu draw helpers
def draw_hud():
    draw_text(screen, f"Score: {player.score}", 8, 8, 18)
    draw_text(screen, f"Lives: {'∞' if god_mode else player.lives}", WIDTH-140, 8, 18)
    draw_text(screen, f"Level: {level}", WIDTH//2-40, 8, 18)
    draw_text(screen, f"High: {highscore}", WIDTH-240, 8, 18)

def reset_game():
    global level, spawn_timer, frame, player, enemies, bullets, powerups, highscore
    enemies.empty(); bullets.empty(); powerups.empty()
    player.rect.center = (WIDTH//2, HEIGHT-80)
    player.lives = 3
    player.score = 0
    player.power = 1
    player.invuln = 0
    level = 1
    spawn_timer = SPAWN_BASE_INTERVAL
    frame = 0

# Main loop
while running:
    dt = clock.tick(FPS)
    frame += 1

    # Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            # global keys
            if event.key == pygame.K_ESCAPE:
                if state == "playing":
                    paused = not paused
                else:
                    running = False
            # secret code handling (letters only)
            if event.unicode and event.unicode.isalpha():
                secret_buffer.append(event.unicode.lower())
                if "".join(secret_buffer).endswith(SECRET_CODE):
                    god_mode = not god_mode
                    # brief on-screen message via simple print and HUD change
                    # reward: if god_mode turned on, set lives to very large
                    if god_mode:
                        player.lives = 9999
                    else:
                        if player.lives > 5:
                            player.lives = 3
            # menu/start controls
            if state == "menu":
                if event.key == pygame.K_RETURN:
                    reset_game()
                    state = "playing"
            elif state == "playing":
                if event.key == pygame.K_SPACE:
                    player.shoot()
            elif state == "gameover":
                if event.key == pygame.K_RETURN:
                    state = "menu"

    keys = pygame.key.get_pressed()

    # State handling
    if state == "menu":
        screen.fill((12,12,30))
        draw_text(screen, "SPARTAN", WIDTH//2-120, HEIGHT//2 - 120, size=64)
        draw_text(screen, "Press ENTER to Start", WIDTH//2-140, HEIGHT//2 - 10, size=28)
        draw_text(screen, f"High Score: {highscore}", WIDTH//2-90, HEIGHT//2 + 40)
        draw_text(screen, "Secret: type 'spartan' to toggle unlimited lives", WIDTH//2-230, HEIGHT//2 + 90, size=16)
        pygame.display.flip()
        continue

    if state == "gameover":
        screen.fill((0,0,0))
        draw_text(screen, "GAME OVER", WIDTH//2-130, HEIGHT//2-80, size=64)
        draw_text(screen, f"Score: {player.score}", WIDTH//2-80, HEIGHT//2-10, size=28)
        draw_text(screen, f"High Score: {highscore}", WIDTH//2-110, HEIGHT//2+30, size=22)
        draw_text(screen, "Press ENTER to return to Menu", WIDTH//2-170, HEIGHT//2+90)
        pygame.display.flip()
        continue

    if paused:
        draw_text(screen, "PAUSED - ESC to resume", WIDTH//2-140, HEIGHT//2-20, size=28)
        pygame.display.flip()
        continue

    # Update game objects
    player.update(keys)
    bullets.update()
    enemies.update()
    powerups.update()
    update_particles()

    # Enemy spawning and difficulty scaling
    if frame % max(30, SPAWN_BASE_INTERVAL - level*2) == 0:
        spawn_enemy_wave(level)
    # occasional single fast enemy
    if random.random() < 0.01 + level*0.0006:
        x = random.choice([random.randint(0, 80), random.randint(WIDTH-80, WIDTH)])
        e = Enemy(x, -10, random.uniform(-1.5,1.5), 2.5 + level*0.05, hp=1, score_value=20, color=(80,200,255), size=20)
        enemies.add(e)

    # simple enemy shooting could be added here

    # collisions
    status = handle_collisions()
    if status == "dead":
        # game over handling
        if player.score > highscore:
            highscore = player.score
            save_highscore(highscore)
        state = "gameover"

    # level up logic
    if frame % (FPS * 20) == 0:
        level += 1

    # draw
    screen.fill((8,8,24))
    # background grid
    for i in range(0, WIDTH, 40):
        pygame.draw.line(screen, (10,10,40), (i,0), (i, HEIGHT), 1)
    for j in range(0, HEIGHT, 40):
        pygame.draw.line(screen, (10,10,40), (0,j), (WIDTH, j), 1)

    # draw sprites
    screen.blit(player.surf, player.rect)
    for b in bullets:
        screen.blit(b.image, b.rect)
    for e in enemies:
        screen.blit(e.image, e.rect)
    for p in powerups:
        screen.blit(p.image, p.rect)
    update_particles()
    draw_hud()

    # Secret mode banner
    if god_mode:
        s = bigfont.render("GOD MODE", True, (255,215,0))
        screen.blit(s, (WIDTH//2 - s.get_width()//2, 40))

    pygame.display.flip()

pygame.quit()
