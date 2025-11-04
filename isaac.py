import pygame
import random
import math
import json
import os

# === Initialisation ===
pygame.init()
screen = pygame.display.set_mode((1366, 769))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 48)
small_font = pygame.font.SysFont(None, 32)
title_font = pygame.font.SysFont(None, 96)
fword_font = pygame.font.SysFont(None, 180)

# === Constantes ===
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
GROUND_Y = 680
GROUND_START_X = 0
GROUND_END_X = 3000

GRAVITY = 800
JUMP_FORCE = -600
MOVE_SPEED = 300
PROJECTILE_SPEED = 800
STAMINA_MAX = 100
STAMINA_JUMP_COST = 10
STAMINA_REGEN_DELAY = 4.0
STAMINA_REGEN_INTERVAL = 0.5
STAMINA_REGEN_AMOUNT = 5
DOUBLE_JUMP_COST = 15
DASH_COST = 10
DASH_SPEED = 900
DASH_DURATION = 0.2
FPS = 60
MAX_MONSTERS = 3
MONSTER_SPAWN_COOLDOWN = 2.0  # Secondes entre chaque spawn
DEATH_BELOW_Y = GROUND_Y + 1500

# === Caméra ===
camera_offset = pygame.Vector2(0, 0)
CAMERA_LAG = 0.05

# === Couleurs améliorées ===
SKY_COLOR = (70, 130, 180)
GROUND_COLOR = (34, 139, 34)
PLATFORM_COLOR = (101, 67, 33)
PLATFORM_HIGHLIGHT = (139, 90, 43)
DOOR_COLOR = (184, 134, 11)
DOOR_FRAME = (139, 69, 19)
SHIRT_COLOR = (50, 120, 220)
PANTS_COLOR = (30, 50, 90)
SHOE_COLOR = (40, 40, 40)
HAND_COLOR = (255, 220, 177)
HAIR_COLOR = (60, 40, 20)

# === Particules ===
particles = []

def create_particles(pos, color, count=8):
    """Crée des particules d'explosion"""
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(50, 150)
        particles.append({
            "pos": pygame.Vector2(pos),
            "vel": pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed),
            "color": color,
            "life": 1.0
        })

def circle_rect_collision(center, radius, rect):
    cx, cy = center
    closest_x = max(rect.left, min(cx, rect.right))
    closest_y = max(rect.top, min(cy, rect.bottom))
    dx = cx - closest_x
    dy = cy - closest_y
    return dx * dx + dy * dy <= radius * radius

# === Nuages et Parallax ===
clouds = []

def init_clouds():
    global clouds
    clouds = []
    for i in range(12):
        x = random.randint(-200, 3000)
        y = random.randint(50, 300)
        speed = random.uniform(10, 30)
        scale = random.uniform(0.6, 1.4)
        clouds.append({"x": x, "y": y, "speed": speed, "scale": scale})

def update_clouds(dt):
    for c in clouds:
        c["x"] += c["speed"] * dt
        if c["x"] - camera_offset.x > 3200:
            c["x"] = camera_offset.x - random.randint(200, 600)
            c["y"] = random.randint(50, 300)
            c["speed"] = random.uniform(10, 30)

def draw_cloud(screen, x, y, scale):
    # Nuage composé de plusieurs ellipses
    color = (255, 255, 255)
    offsets = [(-40, 10, 90, 50), (0, 0, 120, 60), (60, 15, 80, 45)]
    for ox, oy, w, h in offsets:
        rect = pygame.Rect(int(x + ox*scale), int(y + oy*scale), int(w*scale), int(h*scale))
        pygame.draw.ellipse(screen, color, rect)

def draw_parallax_background():
    # Ciel dégradé
    for i in range(SCREEN_HEIGHT):
        color = (
            int(70 + (130 - 70) * i / SCREEN_HEIGHT),
            int(130 + (180 - 130) * i / SCREEN_HEIGHT),
            int(180 + (230 - 180) * i / SCREEN_HEIGHT)
        )
        pygame.draw.line(screen, color, (0, i), (SCREEN_WIDTH, i))

    # Montagnes (3 couches)
    layers = [((90, 110, 140), 0.2, 180), ((80, 100, 130), 0.35, 260), ((70, 90, 120), 0.5, 340)]
    for col, factor, base_y in layers:
        points = []
        start_x = -int(camera_offset.x * factor) - 300
        for x in range(start_x, start_x + SCREEN_WIDTH + 600, 120):
            y = base_y + int(40 * math.sin(x * 0.01))
            points.append((x, y))
        points = [(-1000, SCREEN_HEIGHT), *points, (SCREEN_WIDTH + 1000, SCREEN_HEIGHT)]
        pygame.draw.polygon(screen, col, points)

    # Nuages (parallax léger)
    for c in clouds:
        cx = c["x"] - camera_offset.x * 0.2
        cy = c["y"] - camera_offset.y * 0.2
        draw_cloud(screen, cx, cy, c["scale"])

def draw_shadow(center_x, feet_y_world, max_radius):
    # Ombre douce au sol
    shadow_y = int(feet_y_world - camera_offset.y)
    shadow_x = int(center_x - camera_offset.x)
    width = int(max_radius * 2.4)
    height = max(6, int(max_radius * 0.5))
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (0, 0, 0, 90), surf.get_rect())
    screen.blit(surf, (shadow_x - width//2, shadow_y - height//2))

# === Joueur ===
player_pos = pygame.Vector2(SCREEN_WIDTH / 2, GROUND_Y)
head_radius = 20
body_height = 40
leg_height = 30
arm_length = 25
skin_color = (255, 220, 177)
player_vel_y = 0
direction = 1
walk_cycle = 0
blink_timer = 0.0
blink_close = 0.0
prev_on_ground = True
shoot_recoil = 0.0
stamina = STAMINA_MAX
stamina_idle_timer = 0.0
stamina_regen_timer = 0.0
air_jumps_left = 1
jump_was_pressed = False
dash_was_pressed = False
dash_timer = 0.0
dash_direction = 1

player_pos.y = GROUND_Y - (head_radius + body_height + leg_height)
spawn_point = player_pos.copy()

# === Projectiles ===
projectiles = []
projectile_radius = 6

# === Ennemis ===
monster_radius = 25
monster_spawn_timer = 0.0

def spawn_monster():
    x = random.randint(100, 2500)
    # Types: tank (gros/lent), fast (petit/rapide), flyer (vole)
    r = random.random()
    if r < 0.3:
        m_type = "tank"
        radius = 32
        speed = 60
        hp = 3
        y = GROUND_Y - radius
        extra = {"vel_y": 0.0}
    elif r < 0.7:
        m_type = "fast"
        radius = 18
        speed = 140
        hp = 1
        y = GROUND_Y - radius
        extra = {"vel_y": 0.0}
    else:
        m_type = "flyer"
        radius = 22
        speed = 110
        hp = 1
        base_y = random.randint(GROUND_Y - 280, GROUND_Y - 140)
        y = base_y
        extra = {"fly_phase": random.uniform(0, 6.28), "base_y": base_y}

    data = {
        "pos": pygame.Vector2(x, y),
        "dir": random.choice([-1, 1]),
        "type": m_type,
        "radius": radius,
        "speed": speed,
        "hp": hp,
        "hit_flash": 0.0,
    }
    data.update(extra)
    return data

monsters = [spawn_monster() for _ in range(MAX_MONSTERS)]

# === Multi-niveaux: chargement levels.json et application d'un niveau ===
def _default_level():
    return {
        "name": "Niveau 1",
        "ground": {"y": 680, "start_x": 0, "end_x": 3000},
        "spawn": {"x": SCREEN_WIDTH / 2, "y": 680 - (head_radius + body_height + leg_height)},
        "goal": {"x": 2300, "y": -30, "w": 70, "h": 110},
        "platforms": [
            {"x": 100, "y": 560, "w": 200, "h": 20},
            {"x": 380, "y": 480, "w": 180, "h": 20},
            {"x": 620, "y": 420, "w": 160, "h": 20},
            {"x": 860, "y": 360, "w": 140, "h": 20},
            {"x": 1060, "y": 300, "w": 180, "h": 20},
            {"x": 1300, "y": 200, "w": 250, "h": 20},
            {"x": 1600, "y": 600, "w": 100, "h": 20},
            {"x": 1750, "y": 500, "w": 100, "h": 20},
            {"x": 1600, "y": 400, "w": 100, "h": 20},
            {"x": 1750, "y": 300, "w": 100, "h": 20},
            {"x": 1600, "y": 200, "w": 100, "h": 20},
            {"x": 1750, "y": 100, "w": 100, "h": 20},
            {"x": 1900, "y": 60, "w": 500, "h": 20},
        ],
    }

levels = []
levels_path = os.path.join(os.path.dirname(__file__), "levels.json")
try:
    if os.path.isfile(levels_path):
        with open(levels_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and isinstance(data.get("levels"), list) and data["levels"]:
                levels = data["levels"]
except Exception:
    levels = []

if not levels:
    levels = [_default_level()]

selected_level_idx = 0

platforms = []
goal_rect = pygame.Rect(0, 0, 0, 0)
spawn_point = pygame.Vector2(0, 0)

def apply_level(level):
    global GROUND_Y, GROUND_START_X, GROUND_END_X, platforms, goal_rect, spawn_point
    # Sol
    GROUND_Y = int(level.get("ground", {}).get("y", GROUND_Y))
    GROUND_START_X = int(level.get("ground", {}).get("start_x", GROUND_START_X))
    GROUND_END_X = int(level.get("ground", {}).get("end_x", GROUND_END_X))
    # Plateformes
    platforms = [
        pygame.Rect(int(p.get("x", 0)), int(p.get("y", 0)), int(p.get("w", 0)), int(p.get("h", 0)))
        for p in level.get("platforms", [])
    ]
    # Porte/objectif
    g = level.get("goal", {})
    goal_rect.x = int(g.get("x", 2300))
    goal_rect.y = int(g.get("y", -30))
    goal_rect.w = int(g.get("w", 70))
    goal_rect.h = int(g.get("h", 110))
    # Spawn
    s = level.get("spawn", {})
    spawn_point.update(float(s.get("x", SCREEN_WIDTH / 2)), float(s.get("y", GROUND_Y - (head_radius + body_height + leg_height))))

# Appliquer le niveau initial
apply_level(levels[selected_level_idx])
init_clouds()

# === Score, Vies, Victoire ===
score = 0
lives = 3
invuln_time = 1.5
invuln_timer = 0.0
is_invulnerable = False
victory = False

# === Etat du jeu ===
game_state = "MENU"  # MENU, PLAYING, PAUSED
fword_timer = 0.0

# === Boucle principale ===
running = True
dt = 0

while running:
    # Boutons du menu (recalculés à chaque frame pour simplicité)
    play_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 + 40, 300, 70)
    quit_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 + 130, 300, 70)
    # Boutons de pause
    pause_resume_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 - 20, 300, 70)
    pause_menu_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 + 70, 300, 70)
    pause_quit_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 + 160, 300, 70)
    # Événements
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if game_state == "MENU":
                running = False
            elif game_state == "PLAYING":
                # Ouvrir le menu pause
                game_state = "PAUSED"
            elif game_state == "PAUSED":
                # Reprendre
                game_state = "PLAYING"
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_o:
            # Easter egg: gros texte à l'écran
            fword_timer = 1.5
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game_state == "MENU":
                if play_rect.collidepoint(event.pos):
                    # Reset et démarrage du jeu
                    score = 0
                    lives = 3
                    invuln_timer = 0.0
                    is_invulnerable = False
                    victory = False
                    # Appliquer le niveau sélectionné au démarrage
                    apply_level(levels[selected_level_idx])
                    player_pos = spawn_point.copy()
                    player_vel_y = 0
                    camera_offset = pygame.Vector2(0, 0)
                    monsters = [spawn_monster() for _ in range(MAX_MONSTERS)]
                    projectiles = []
                    particles = []
                    monster_spawn_timer = 0.0
                    stamina = STAMINA_MAX
                    stamina_idle_timer = 0.0
                    stamina_regen_timer = 0.0
                    air_jumps_left = 1
                    jump_was_pressed = False
                    dash_was_pressed = False
                    dash_timer = 0.0
                    dash_direction = 1
                    game_state = "PLAYING"
                elif quit_rect.collidepoint(event.pos):
                    running = False
            elif game_state == "PAUSED":
                if pause_resume_rect.collidepoint(event.pos):
                    game_state = "PLAYING"
                elif pause_menu_rect.collidepoint(event.pos):
                    game_state = "MENU"
                elif pause_quit_rect.collidepoint(event.pos):
                    running = False
            elif game_state == "PLAYING":
                # Tir vers la souris
                mouse_world_x = event.pos[0] + camera_offset.x
                mouse_world_y = event.pos[1] + camera_offset.y
                
                dx = mouse_world_x - player_pos.x
                dy = mouse_world_y - player_pos.y
                distance = math.sqrt(dx**2 + dy**2)
                
                if distance > 0:
                    dir_x = dx / distance
                    dir_y = dy / distance
                    
                    proj_x = player_pos.x + dir_x * (head_radius + 10)
                    proj_y = player_pos.y + dir_y * (head_radius + 10)
                    
                    projectiles.append({
                        "pos": pygame.Vector2(proj_x, proj_y),
                        "vel": pygame.Vector2(dir_x * PROJECTILE_SPEED, dir_y * PROJECTILE_SPEED)
                    })
                    # Animation de recul et effet visuel
                    shoot_recoil = 0.12
                    create_particles((proj_x, proj_y), (255, 230, 100), 6)
        elif event.type == pygame.KEYDOWN and game_state == "PAUSED":
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                game_state = "PLAYING"
            elif event.key == pygame.K_m:
                game_state = "MENU"
        elif event.type == pygame.KEYDOWN:
            if game_state == "MENU" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                # Lancer le jeu via clavier
                score = 0
                lives = 3
                invuln_timer = 0.0
                is_invulnerable = False
                victory = False
                # Appliquer le niveau sélectionné au démarrage
                apply_level(levels[selected_level_idx])
                player_pos = spawn_point.copy()
                player_vel_y = 0
                camera_offset = pygame.Vector2(0, 0)
                monsters = [spawn_monster() for _ in range(MAX_MONSTERS)]
                projectiles = []
                particles = []
                monster_spawn_timer = 0.0
                stamina = STAMINA_MAX
                stamina_idle_timer = 0.0
                stamina_regen_timer = 0.0
                air_jumps_left = 1
                jump_was_pressed = False
                dash_was_pressed = False
                dash_timer = 0.0
                dash_direction = 1
                game_state = "PLAYING"
            elif game_state == "MENU" and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                # Changer de niveau sélectionné dans le menu
                if event.key == pygame.K_LEFT:
                    selected_level_idx = (selected_level_idx - 1) % len(levels)
                else:
                    selected_level_idx = (selected_level_idx + 1) % len(levels)
                # Pré-appliquer pour que spawn/sol soient prêts au lancement
                apply_level(levels[selected_level_idx])

    # --- MENU PRINCIPAL ---
    if game_state == "MENU":
        # Fond avec parallax + nuages
        update_clouds(dt)
        draw_parallax_background()

        # Titre
        title_surf = title_font.render("Mon Jeu", True, (255, 255, 255))
        screen.blit(title_surf, (SCREEN_WIDTH//2 - title_surf.get_width()//2, SCREEN_HEIGHT//2 - 120))

        # Boutons
        mouse_pos = pygame.mouse.get_pos()
        def draw_button(rect, text):
            hovered = rect.collidepoint(mouse_pos)
            base = (50, 50, 50)
            hover = (80, 80, 80)
            pygame.draw.rect(screen, hover if hovered else base, rect, border_radius=10)
            pygame.draw.rect(screen, (200, 200, 200), rect, 3, border_radius=10)
            txt = font.render(text, True, (255, 255, 255))
            screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

        # Afficher le niveau sélectionné
        level_name = levels[selected_level_idx].get("name", f"Niveau {selected_level_idx+1}")
        level_txt = small_font.render(f"Niveau: {level_name}", True, (255, 255, 255))
        screen.blit(level_txt, (SCREEN_WIDTH//2 - level_txt.get_width()//2, SCREEN_HEIGHT//2 - 60))

        draw_button(play_rect, "Jouer")
        draw_button(quit_rect, "Quitter")

        hint = small_font.render("Entrée/Espace pour jouer", True, (230, 230, 230))
        screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT//2 + 220))

        pygame.display.flip()
        dt = clock.tick(FPS) / 1000
        continue

    # --- MENU PAUSE ---
    if game_state == "PAUSED":
        # Fond atténué
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Titre
        pause_title = title_font.render("Pause", True, (255, 255, 255))
        screen.blit(pause_title, (SCREEN_WIDTH//2 - pause_title.get_width()//2, SCREEN_HEIGHT//2 - 120))

        mouse_pos = pygame.mouse.get_pos()
        def draw_button(rect, text):
            hovered = rect.collidepoint(mouse_pos)
            base = (50, 50, 50)
            hover = (80, 80, 80)
            pygame.draw.rect(screen, hover if hovered else base, rect, border_radius=10)
            pygame.draw.rect(screen, (200, 200, 200), rect, 3, border_radius=10)
            txt = font.render(text, True, (255, 255, 255))
            screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

        draw_button(pause_resume_rect, "Reprendre")
        draw_button(pause_menu_rect, "Menu")
        draw_button(pause_quit_rect, "Quitter")

        hint = small_font.render("Echap/Entrée/Espace: Reprendre | M: Menu", True, (230, 230, 230))
        screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT//2 + 250))

        pygame.display.flip()
        dt = clock.tick(FPS) / 1000
        continue

    # --- LOGIQUE DU JEU ---

    # Mouvements
    stamina_idle_timer += dt
    keys = pygame.key.get_pressed()
    moving = False
    if keys[pygame.K_q] or keys[pygame.K_LEFT]:
        player_pos.x -= MOVE_SPEED * dt
        direction = -1
        moving = True
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        player_pos.x += MOVE_SPEED * dt
        direction = 1
        moving = True
    if moving:
        walk_cycle += 10 * dt
    else:
        walk_cycle = 0

    # Détection sol/plateforme
    feet_y = player_pos.y + head_radius + body_height + leg_height
    on_ground = False
    # Sol infini limité en X
    if feet_y >= GROUND_Y - 0.1 and GROUND_START_X <= player_pos.x <= GROUND_END_X:
        on_ground = True
    else:
        for plat in platforms:
            if plat.left - 5 < player_pos.x < plat.right + 5 and abs(feet_y - plat.top) <= 6:
                on_ground = True
                player_pos.y = plat.top - (head_radius + body_height + leg_height)
                player_vel_y = 0
                break

    if on_ground:
        air_jumps_left = 1

    space_pressed = keys[pygame.K_SPACE]
    if space_pressed and not jump_was_pressed:
        if on_ground and stamina >= STAMINA_JUMP_COST:
            player_vel_y = JUMP_FORCE
            stamina = max(0, stamina - STAMINA_JUMP_COST)
            stamina_idle_timer = 0.0
            stamina_regen_timer = 0.0
            air_jumps_left = 1
        elif not on_ground and air_jumps_left > 0 and stamina >= DOUBLE_JUMP_COST:
            player_vel_y = JUMP_FORCE
            stamina = max(0, stamina - DOUBLE_JUMP_COST)
            stamina_idle_timer = 0.0
            stamina_regen_timer = 0.0
            air_jumps_left -= 1

    dash_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
    if dash_pressed and not dash_was_pressed and dash_timer <= 0 and stamina >= DASH_COST:
        desired_dir = 0
        if keys[pygame.K_q] or keys[pygame.K_LEFT]:
            desired_dir = -1
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            desired_dir = 1
        else:
            desired_dir = direction
        if desired_dir != 0:
            dash_direction = desired_dir
            dash_timer = DASH_DURATION
            stamina = max(0, stamina - DASH_COST)
            stamina_idle_timer = 0.0
            stamina_regen_timer = 0.0

    jump_was_pressed = space_pressed
    dash_was_pressed = dash_pressed

    player_vel_y += GRAVITY * dt
    player_pos.y += player_vel_y * dt

    feet_y = player_pos.y + head_radius + body_height + leg_height
    if feet_y > GROUND_Y and GROUND_START_X <= player_pos.x <= GROUND_END_X:
        player_pos.y = GROUND_Y - (head_radius + body_height + leg_height)
        player_vel_y = 0

    player_rect = pygame.Rect(int(player_pos.x - head_radius), int(player_pos.y - head_radius), 
                              head_radius*2, head_radius*2 + body_height + leg_height)
    if player_vel_y >= 0:
        for plat in platforms:
            if player_rect.colliderect(plat):
                plat_top = plat.top
                if feet_y - player_vel_y * dt <= plat_top:
                    player_pos.y = plat_top - (head_radius + body_height + leg_height)
                    player_vel_y = 0
                    break

    if dash_timer > 0:
        player_pos.x += dash_direction * DASH_SPEED * dt
        dash_timer = max(0.0, dash_timer - dt)

    player_pos.x = max(head_radius, player_pos.x)

    if stamina_idle_timer >= STAMINA_REGEN_DELAY and stamina < STAMINA_MAX:
        stamina_regen_timer += dt
        while stamina_regen_timer >= STAMINA_REGEN_INTERVAL and stamina < STAMINA_MAX:
            stamina = min(STAMINA_MAX, stamina + STAMINA_REGEN_AMOUNT)
            stamina_regen_timer -= STAMINA_REGEN_INTERVAL
        if stamina >= STAMINA_MAX:
            stamina_regen_timer = 0.0
    else:
        stamina_regen_timer = 0.0

    if not prev_on_ground and on_ground and player_vel_y == 0:
        feet_x = player_pos.x
        feet_y = GROUND_Y if feet_y >= GROUND_Y else player_pos.y + head_radius + body_height + leg_height
        create_particles((feet_x, feet_y), (180, 180, 180), 10)
    prev_on_ground = on_ground

    blink_timer -= dt
    if blink_timer <= 0 and blink_close <= 0:
        blink_close = 0.12
        blink_timer = random.uniform(2.0, 5.0)
    if blink_close > 0:
        blink_close -= dt
    if shoot_recoil > 0:
        shoot_recoil -= dt

    if player_pos.y > DEATH_BELOW_Y:
        lives -= 1
        is_invulnerable = True
        invuln_timer = invuln_time
        player_pos = spawn_point.copy()
        player_vel_y = 0
        create_particles(player_pos, (255, 100, 100), 15)

    # Caméra
    target_x = player_pos.x - SCREEN_WIDTH // 2
    target_y = player_pos.y - SCREEN_HEIGHT // 2
    camera_offset.x += (target_x - camera_offset.x) * CAMERA_LAG
    camera_offset.y += (target_y - camera_offset.y) * CAMERA_LAG

    # Projectiles avec direction
    for proj in projectiles[:]:
        proj["pos"] += proj["vel"] * dt
        if (proj["pos"].x < camera_offset.x - 200 or proj["pos"].x > camera_offset.x + SCREEN_WIDTH + 200 or
            proj["pos"].y < camera_offset.y - 200 or proj["pos"].y > camera_offset.y + SCREEN_HEIGHT + 200):
            projectiles.remove(proj)

    # Collision projectile-monstre
    for proj in projectiles[:]:
        for monster in monsters[:]:
            if proj["pos"].distance_to(monster["pos"]) < projectile_radius + monster["radius"]:
                monster["hp"] -= 1
                monster["hit_flash"] = 0.2
                
                if monster["hp"] <= 0:
                    create_particles(monster["pos"], (255, 50, 50), 12)
                    monsters.remove(monster)
                    score += 2 if monster["type"] == "tank" else 1
                
                if proj in projectiles:
                    projectiles.remove(proj)
                break

    # Spawn avec cooldown
    monster_spawn_timer -= dt
    if monster_spawn_timer <= 0 and len(monsters) < MAX_MONSTERS:
        monsters.append(spawn_monster())
        monster_spawn_timer = MONSTER_SPAWN_COOLDOWN

    # Monstres (mouvement, gravité/vol et flash)
    for monster in monsters:
        # Horizontal
        monster["pos"].x += monster["dir"] * monster["speed"] * dt
        if monster["pos"].x < 50:
            monster["dir"] = 1
        if monster["pos"].x > 2500:
            monster["dir"] = -1

        if monster.get("type") == "flyer":
            # Vol stationnaire/ondulant
            monster["fly_phase"] += dt * 2.0
            monster["pos"].y = monster["base_y"] + math.sin(monster["fly_phase"]) * 25
        else:
            # Gravité (marcheurs)
            monster["vel_y"] += GRAVITY * dt
            monster["pos"].y += monster["vel_y"] * dt

            # Collision sol
            feet_y = monster["pos"].y + monster["radius"]
            if feet_y > GROUND_Y:
                monster["pos"].y = GROUND_Y - monster["radius"]
                monster["vel_y"] = 0

            # Collision plateformes (atterrir par dessus)
            if monster["vel_y"] >= 0:
                monster_rect = pygame.Rect(int(monster["pos"].x - monster["radius"]),
                                           int(monster["pos"].y - monster["radius"]),
                                           monster["radius"]*2, monster["radius"]*2)
                for plat in platforms:
                    if monster_rect.colliderect(plat):
                        plat_top = plat.top
                        if feet_y - monster["vel_y"] * dt <= plat_top + 2:
                            monster["pos"].y = plat_top - monster["radius"]
                            monster["vel_y"] = 0
                            break

        # Flash dégâts
        if monster["hit_flash"] > 0:
            monster["hit_flash"] -= dt

    # Collision joueur-ennemi
    p_center = (int(player_pos.x), int(player_pos.y))
    if not is_invulnerable:
        for monster in monsters[:]:
            if circle_rect_collision((monster["pos"].x, monster["pos"].y), monster["radius"], player_rect):
                lives -= 1
                is_invulnerable = True
                invuln_timer = invuln_time
                player_pos = spawn_point.copy()
                player_vel_y = 0
                create_particles(player_pos, (255, 255, 100), 15)
                break

    if is_invulnerable:
        invuln_timer -= dt
        if invuln_timer <= 0:
            is_invulnerable = False

    # Particules
    for part in particles[:]:
        part["pos"] += part["vel"] * dt
        part["vel"].y += GRAVITY * 0.5 * dt
        part["life"] -= dt * 2
        if part["life"] <= 0:
            particles.remove(part)

    # Victoire
    if not victory and pygame.Rect(int(player_pos.x - head_radius), int(player_pos.y - head_radius), 
                                   head_radius*2, head_radius*2).colliderect(goal_rect):
        victory = True

    # --- DESSIN ---

    # Ciel dégradé
    for i in range(SCREEN_HEIGHT):
        color = (
            int(70 + (130 - 70) * i / SCREEN_HEIGHT),
            int(130 + (180 - 130) * i / SCREEN_HEIGHT),
            int(180 + (230 - 180) * i / SCREEN_HEIGHT)
        )
        pygame.draw.line(screen, color, (0, i), (SCREEN_WIDTH, i))

    # Sol avec texture
    ground_rect = pygame.Rect(GROUND_START_X - camera_offset.x, GROUND_Y - camera_offset.y, GROUND_END_X - GROUND_START_X, 100)
    pygame.draw.rect(screen, GROUND_COLOR, ground_rect)
    pygame.draw.rect(screen, (25, 100, 25), ground_rect, 3)
    for i in range(0, 3000, 50):
        pygame.draw.line(screen, (44, 160, 44), 
                        (i - camera_offset.x, GROUND_Y - camera_offset.y),
                        (i - camera_offset.x, GROUND_Y - camera_offset.y + 100), 2)

    # Plateformes avec relief
    for plat in platforms:
        plat_rect_screen = plat.move(-camera_offset.x, -camera_offset.y)
        pygame.draw.rect(screen, PLATFORM_COLOR, plat_rect_screen)
        pygame.draw.rect(screen, PLATFORM_HIGHLIGHT, plat_rect_screen, 3)
        pygame.draw.line(screen, (80, 50, 20), 
                        (plat_rect_screen.left, plat_rect_screen.top + 5),
                        (plat_rect_screen.right, plat_rect_screen.top + 5), 2)

    # Porte avec détails
    goal_rect_screen = goal_rect.move(-camera_offset.x, -camera_offset.y)
    pygame.draw.rect(screen, DOOR_COLOR, goal_rect_screen)
    pygame.draw.rect(screen, DOOR_FRAME, goal_rect_screen, 5)
    pygame.draw.line(screen, (100, 70, 20), 
                    (goal_rect_screen.centerx, goal_rect_screen.top),
                    (goal_rect_screen.centerx, goal_rect_screen.bottom), 3)
    knob_pos = (goal_rect_screen.right - 12, goal_rect_screen.centery)
    pygame.draw.circle(screen, (30, 30, 30), knob_pos, 6)
    pygame.draw.circle(screen, (80, 80, 80), knob_pos, 3)

    # Ombres
    player_feet = player_pos.y + head_radius + body_height + leg_height
    draw_shadow(player_pos.x, player_feet, head_radius + 12)
    for monster in monsters:
        draw_shadow(monster["pos"].x, monster["pos"].y + monster["radius"], monster["radius"])

    # Joueur
    p_center_screen = (int(player_pos.x - camera_offset.x), int(player_pos.y - camera_offset.y))
    moving_now = keys[pygame.K_q] or keys[pygame.K_LEFT] or keys[pygame.K_d] or keys[pygame.K_RIGHT]
    bob = math.sin(walk_cycle * 12) * 2 if moving_now else 0
    render_center = (p_center_screen[0], p_center_screen[1] + int(bob))

    if not is_invulnerable or int(invuln_timer * 10) % 2 == 0:
        # Tête avec contour
        pygame.draw.circle(screen, skin_color, render_center, head_radius)
        pygame.draw.circle(screen, (0, 0, 0), render_center, head_radius, 3)
        
        # Visage
        eye_offset = 7
        eye_pos = (render_center[0] - eye_offset * direction, render_center[1] - 5)
        if blink_close > 0:
            pygame.draw.line(screen, (0, 0, 0), (int(eye_pos[0]-3), int(eye_pos[1])), (int(eye_pos[0]+3), int(eye_pos[1])), 2)
        else:
            pygame.draw.circle(screen, (0, 0, 0), (int(eye_pos[0]), int(eye_pos[1])), 3)
        pygame.draw.arc(screen, (0, 0, 0), 
                       (render_center[0] - head_radius, render_center[1] - head_radius, 
                        head_radius*2, head_radius*2), 3.8, 5.0, 3)

        # Cou + Torse (rectangle arrondi comme un t-shirt)
        neck_width = 10
        neck_height = 6
        neck_rect = pygame.Rect(render_center[0] - neck_width//2, render_center[1] + head_radius - 2, neck_width, neck_height)
        pygame.draw.rect(screen, HAND_COLOR, neck_rect, border_radius=3)

        torso_width = 26
        tilt = direction * (2 if moving_now else 0)
        torso_rect = pygame.Rect(0, 0, torso_width, body_height)
        torso_rect.centerx = render_center[0] + int(tilt)
        torso_rect.top = render_center[1] + head_radius
        pygame.draw.rect(screen, SHIRT_COLOR, torso_rect, border_radius=6)
        pygame.draw.rect(screen, (0, 0, 0), torso_rect, 2, border_radius=6)
        body_start = (torso_rect.centerx, torso_rect.top)
        body_end = (torso_rect.centerx, torso_rect.bottom)

        # Bras (recul au tir et pose en l'air) plus épais avec mains
        base_arm_y = render_center[1] + head_radius + 16
        arm_y = base_arm_y - (6 if not on_ground else 0)
        arm_angle = math.sin(walk_cycle * 10) * 15
        arm_offset = arm_length * math.cos(math.radians(arm_angle))
        if shoot_recoil > 0:
            recoil_factor = 1.0 - min(1.0, shoot_recoil / 0.12) * 0.6
            arm_offset *= recoil_factor
            arm_y -= 2
        if not on_ground:
            arm_offset *= 0.6
        left_hand = (int(render_center[0] - arm_offset), int(arm_y))
        right_hand = (int(render_center[0] + arm_offset), int(arm_y))
        pygame.draw.line(screen, (0, 0, 0), (left_hand[0], arm_y), (right_hand[0], arm_y), 6)
        pygame.draw.circle(screen, HAND_COLOR, left_hand, 4)
        pygame.draw.circle(screen, HAND_COLOR, right_hand, 4)

        # Pistolet dans la main avant, orienté vers la souris
        mouse_x, mouse_y = pygame.mouse.get_pos()
        mouse_world = pygame.Vector2(mouse_x + camera_offset.x, mouse_y + camera_offset.y)
        aim_vec = (mouse_world - pygame.Vector2(player_pos.x, player_pos.y))
        if aim_vec.length_squared() == 0:
            aim_dir = pygame.Vector2(direction, 0)
        else:
            aim_dir = aim_vec.normalize()
        # Choisir la main avant selon l'orientation de visée
        front_hand = right_hand if aim_dir.x >= 0 else left_hand
        # Paramètres visuels du pistolet
        grip_len, body_len, barrel_len = 8, 12, 10
        thickness = 5
        # Points du pistolet
        base = pygame.Vector2(front_hand)
        perp = pygame.Vector2(-aim_dir.y, aim_dir.x)
        grip_end = base - perp * 4 + aim_dir * 2
        body_end = base + aim_dir * body_len
        barrel_end = body_end + aim_dir * barrel_len
        # Dessin
        pygame.draw.line(screen, (20, 20, 20), base, grip_end, thickness)  # poignée
        pygame.draw.line(screen, (30, 30, 30), base, body_end, thickness)  # corps
        pygame.draw.line(screen, (80, 80, 80), body_end, barrel_end, 3)    # canon

        # (Jambes retirées)

        # Cheveux simples
        hair_rect = pygame.Rect(render_center[0] - head_radius + 4, render_center[1] - head_radius + 2, head_radius*2 - 8, head_radius)
        pygame.draw.arc(screen, HAIR_COLOR, hair_rect, math.radians(200), math.radians(340), 4)

    # Projectiles avec traînée
    for proj in projectiles:
        proj_screen = (int(proj["pos"].x - camera_offset.x), int(proj["pos"].y - camera_offset.y))
        pygame.draw.circle(screen, (150, 255, 150), proj_screen, projectile_radius + 2)
        pygame.draw.circle(screen, (0, 255, 0), proj_screen, projectile_radius)
        pygame.draw.circle(screen, (255, 255, 255), proj_screen, projectile_radius - 3)

    # Monstres (types: tank, fast, flyer)
    for monster in monsters:
        monster_screen = (int(monster["pos"].x - camera_offset.x), 
                         int(monster["pos"].y - camera_offset.y))
        r = monster["radius"]
        
        # Couleur selon flash
        base_colors = {
            "tank": (200, 40, 40),
            "fast": (255, 140, 0),
            "flyer": (100, 160, 255),
        }
        monster_color = (255, 220, 220) if monster["hit_flash"] > 0 else base_colors.get(monster["type"], (220, 20, 20))

        if monster["type"] == "tank":
            # Corps plus gros + contour
            pygame.draw.circle(screen, monster_color, monster_screen, r)
            pygame.draw.circle(screen, (0, 0, 0), monster_screen, r, 3)
            # Sac à dos / blindage
            backpack_x = monster_screen[0] - 18
            backpack_y = monster_screen[1]
            backpack_rect = pygame.Rect(backpack_x - 12, backpack_y - 18, 24, 36)
            pygame.draw.rect(screen, (60, 40, 20), backpack_rect)
            pygame.draw.rect(screen, (0, 0, 0), backpack_rect, 2)
            pygame.draw.circle(screen, (100, 80, 50), (backpack_x, backpack_y - 6), 5)
            # Yeux
            pygame.draw.circle(screen, (255, 255, 0), (monster_screen[0] - 9, monster_screen[1] - 6), 4)
            pygame.draw.circle(screen, (255, 255, 0), (monster_screen[0] + 9, monster_screen[1] - 6), 4)
            pygame.draw.circle(screen, (0, 0, 0), (monster_screen[0] - 9, monster_screen[1] - 6), 2)
            pygame.draw.circle(screen, (0, 0, 0), (monster_screen[0] + 9, monster_screen[1] - 6), 2)
        elif monster["type"] == "fast":
            # Petit rapide
            pygame.draw.circle(screen, monster_color, monster_screen, r)
            pygame.draw.circle(screen, (0, 0, 0), monster_screen, r, 3)
            # Yeux plus rapprochés
            pygame.draw.circle(screen, (0, 0, 0), (monster_screen[0] - 6, monster_screen[1] - 4), 3)
            pygame.draw.circle(screen, (0, 0, 0), (monster_screen[0] + 6, monster_screen[1] - 4), 3)
            # Traînée légère
            pygame.draw.circle(screen, (255, 200, 120), (monster_screen[0] - monster["dir"]*r, monster_screen[1]), max(1, r//4))
        else:  # flyer
            # Corps volant avec ailes
            pygame.draw.circle(screen, monster_color, monster_screen, r)
            pygame.draw.circle(screen, (0, 0, 0), monster_screen, r, 3)
            wing_span = r + 10
            left_wing = [(monster_screen[0] - 2, monster_screen[1]),
                         (monster_screen[0] - wing_span, monster_screen[1] - 6),
                         (monster_screen[0] - wing_span + 6, monster_screen[1] + 6)]
            right_wing = [(monster_screen[0] + 2, monster_screen[1]),
                          (monster_screen[0] + wing_span, monster_screen[1] - 6),
                          (monster_screen[0] + wing_span - 6, monster_screen[1] + 6)]
            pygame.draw.polygon(screen, (180, 210, 255), left_wing)
            pygame.draw.polygon(screen, (180, 210, 255), right_wing)
            pygame.draw.polygon(screen, (0, 0, 0), left_wing, 2)
            pygame.draw.polygon(screen, (0, 0, 0), right_wing, 2)

    # Particules
    for part in particles:
        if part["life"] > 0:
            part_screen = (int(part["pos"].x - camera_offset.x), int(part["pos"].y - camera_offset.y))
            alpha = int(255 * part["life"])
            color = tuple(min(255, max(0, int(c * part["life"]))) for c in part["color"])
            pygame.draw.circle(screen, color, part_screen, 3)

    # --- HUD ---
    # Panneau semi-transparent
    hud_panel = pygame.Surface((300, 210), pygame.SRCALPHA)
    hud_panel.fill((0, 0, 0, 120))
    screen.blit(hud_panel, (10, 10))

    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(score_text, (30, 25))
    
    # Vies avec cœurs
    lives_text = font.render("Vies:", True, (255, 255, 255))
    screen.blit(lives_text, (30, 70))
    for i in range(lives):
        heart_x = 130 + i * 35
        pygame.draw.circle(screen, (255, 50, 50), (heart_x - 5, 85), 10)
        pygame.draw.circle(screen, (255, 50, 50), (heart_x + 5, 85), 10)
        pygame.draw.polygon(screen, (255, 50, 50), 
                           [(heart_x - 15, 85), (heart_x, 100), (heart_x + 15, 85)])

    stamina_label = small_font.render("Stamina", True, (180, 200, 255))
    screen.blit(stamina_label, (30, 120))
    stamina_bar_bg = pygame.Rect(30, 150, 240, 20)
    pygame.draw.rect(screen, (40, 40, 40), stamina_bar_bg, border_radius=6)
    stamina_ratio = stamina / STAMINA_MAX if STAMINA_MAX else 0
    fill_width = int(stamina_bar_bg.width * max(0, min(1, stamina_ratio)))
    if fill_width > 0:
        stamina_bar_fill = pygame.Rect(stamina_bar_bg.left, stamina_bar_bg.top, fill_width, stamina_bar_bg.height)
        pygame.draw.rect(screen, (70, 170, 255), stamina_bar_fill, border_radius=6)
    pygame.draw.rect(screen, (120, 180, 255), stamina_bar_bg, 2, border_radius=6)

    if is_invulnerable:
        inv_text = small_font.render("⚡ INVULNÉRABLE", True, (255, 255, 0))
        screen.blit(inv_text, (30, 180))

    # Indicateur de cooldown spawn
    if monster_spawn_timer > 0:
        cooldown_text = small_font.render(f"Prochain spawn: {monster_spawn_timer:.1f}s", 
                                         True, (200, 200, 200))
        screen.blit(cooldown_text, (SCREEN_WIDTH - 350, 30))

    # Messages de fin
    if victory:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        big_text = pygame.font.SysFont(None, 120).render("VICTOIRE !", True, (255, 215, 0))
        sub_text = font.render("Félicitations !", True, (255, 255, 255))
        score_final = font.render(f"Score Final: {score}", True, (255, 255, 255))
        
        screen.blit(big_text, (SCREEN_WIDTH//2 - big_text.get_width()//2, SCREEN_HEIGHT//2 - 100))
        screen.blit(sub_text, (SCREEN_WIDTH//2 - sub_text.get_width()//2, SCREEN_HEIGHT//2 + 20))
        screen.blit(score_final, (SCREEN_WIDTH//2 - score_final.get_width()//2, SCREEN_HEIGHT//2 + 70))
        pygame.display.flip()
        pygame.time.delay(1500)
        # Retour au menu
        game_state = "MENU"
        victory = False

    if lives <= 0:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        
        over_text = pygame.font.SysFont(None, 96).render("GAME OVER", True, (255, 50, 50))
        score_final = font.render(f"Score: {score}", True, (255, 255, 255))
        
        screen.blit(over_text, (SCREEN_WIDTH//2 - over_text.get_width()//2, SCREEN_HEIGHT//2 - 60))
        screen.blit(score_final, (SCREEN_WIDTH//2 - score_final.get_width()//2, SCREEN_HEIGHT//2 + 20))
        pygame.display.flip()
        pygame.time.delay(1500)
        # Retour au menu
        game_state = "MENU"
        # Reset léger, le plein reset se fera quand on clique "Jouer"
        lives = 3
        score = 0
        projectiles = []
        particles = []

    pygame.display.flip()
    dt = clock.tick(FPS) / 1000

pygame.quit()
