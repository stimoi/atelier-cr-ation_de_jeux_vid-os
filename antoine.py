import pygame
import random
import math

# === Initialisation ===
pygame.init()
screen = pygame.display.set_mode((1366, 769))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 48)
small_font = pygame.font.SysFont(None, 32)

# === Constantes ===
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
GROUND_Y = 680
GRAVITY = 800
JUMP_FORCE = -600
MOVE_SPEED = 300
PROJECTILE_SPEED = 800
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
    y = GROUND_Y - (head_radius + body_height + leg_height)
    # 20% de chance de spawner un tank
    is_tank = random.random() < 0.2
    return {
        "pos": pygame.Vector2(x, y),
        "dir": random.choice([-1, 1]),
        "is_tank": is_tank,
        "hp": 2 if is_tank else 1,
        "hit_flash": 0.0
    }

monsters = [spawn_monster() for _ in range(MAX_MONSTERS)]

# === Plateformes ===
platforms = [
    pygame.Rect(100, 560, 200, 20),
    pygame.Rect(380, 480, 180, 20),
    pygame.Rect(620, 420, 160, 20),
    pygame.Rect(860, 360, 140, 20),
    pygame.Rect(1060, 300, 180, 20),
    pygame.Rect(1300, 200, 250, 20),
    pygame.Rect(1600, 600, 100, 20),
    pygame.Rect(1750, 500, 100, 20),
    pygame.Rect(1600, 400, 100, 20),
    pygame.Rect(1750, 300, 100, 20),
    pygame.Rect(1600, 200, 100, 20),
    pygame.Rect(1750, 100, 100, 20),
    pygame.Rect(1900, 60, 500, 20),
]

goal_rect = pygame.Rect(2300, 0, 40, 60)
spawn_point = pygame.Vector2(SCREEN_WIDTH / 2, GROUND_Y - (head_radius + body_height + leg_height))

# === Score, Vies, Victoire ===
score = 0
lives = 3
invuln_time = 1.5
invuln_timer = 0.0
is_invulnerable = False
victory = False

# === Boucle principale ===
running = True
dt = 0

while running:
    # Événements
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (
            event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
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

    # --- LOGIQUE DU JEU ---

    # Mouvements
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
    if feet_y >= GROUND_Y - 0.1:
        on_ground = True
    else:
        for plat in platforms:
            if plat.left - 5 < player_pos.x < plat.right + 5 and abs(feet_y - plat.top) <= 6:
                on_ground = True
                player_pos.y = plat.top - (head_radius + body_height + leg_height)
                player_vel_y = 0
                break

    if keys[pygame.K_SPACE] and on_ground:
        player_vel_y = JUMP_FORCE

    player_vel_y += GRAVITY * dt
    player_pos.y += player_vel_y * dt

    feet_y = player_pos.y + head_radius + body_height + leg_height
    if feet_y > GROUND_Y:
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

    player_pos.x = max(head_radius, player_pos.x)

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
            if proj["pos"].distance_to(monster["pos"]) < projectile_radius + monster_radius:
                monster["hp"] -= 1
                monster["hit_flash"] = 0.2
                
                if monster["hp"] <= 0:
                    create_particles(monster["pos"], (255, 50, 50), 12)
                    monsters.remove(monster)
                    score += 2 if monster["is_tank"] else 1
                
                if proj in projectiles:
                    projectiles.remove(proj)
                break

    # Spawn avec cooldown
    monster_spawn_timer -= dt
    if monster_spawn_timer <= 0 and len(monsters) < MAX_MONSTERS:
        monsters.append(spawn_monster())
        monster_spawn_timer = MONSTER_SPAWN_COOLDOWN

    # Monstres (mouvement et flash)
    for monster in monsters:
        monster["pos"].x += monster["dir"] * 80 * dt
        if monster["pos"].x < 50:
            monster["dir"] = 1
        if monster["pos"].x > 2500:
            monster["dir"] = -1
        
        if monster["hit_flash"] > 0:
            monster["hit_flash"] -= dt

    # Collision joueur-ennemi
    p_center = (int(player_pos.x), int(player_pos.y))
    if not is_invulnerable:
        for monster in monsters[:]:
            if pygame.Vector2(p_center).distance_to(monster["pos"]) < head_radius + monster_radius:
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
    ground_rect = pygame.Rect(0 - camera_offset.x, GROUND_Y - camera_offset.y, 3000, 100)
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

    # Joueur
    p_center_screen = (int(player_pos.x - camera_offset.x), int(player_pos.y - camera_offset.y))

    if not is_invulnerable or int(invuln_timer * 10) % 2 == 0:
        # Tête avec contour
        pygame.draw.circle(screen, skin_color, p_center_screen, head_radius)
        pygame.draw.circle(screen, (0, 0, 0), p_center_screen, head_radius, 3)
        
        # Visage
        eye_offset = 7
        pygame.draw.circle(screen, (0, 0, 0), 
                          (p_center_screen[0] - eye_offset * direction, p_center_screen[1] - 5), 3)
        pygame.draw.arc(screen, (0, 0, 0), 
                       (p_center_screen[0] - head_radius, p_center_screen[1] - head_radius, 
                        head_radius*2, head_radius*2), 3.8, 5.0, 3)

        # Corps
        body_start = (p_center_screen[0], p_center_screen[1] + head_radius)
        body_end = (p_center_screen[0], p_center_screen[1] + head_radius + body_height)
        pygame.draw.line(screen, (0, 0, 0), body_start, body_end, 5)

        # Bras
        arm_y = p_center_screen[1] + head_radius + 15
        arm_angle = math.sin(walk_cycle * 10) * 15
        arm_offset = arm_length * math.cos(math.radians(arm_angle))
        pygame.draw.line(screen, (0, 0, 0), 
                        (p_center_screen[0] - arm_offset, arm_y), 
                        (p_center_screen[0] + arm_offset, arm_y), 5)

        # Jambes
        leg_offset = 15
        leg_swing = math.sin(walk_cycle * 10) * 12
        leg_left = (p_center_screen[0] - leg_offset, body_end[1] + leg_height + leg_swing)
        leg_right = (p_center_screen[0] + leg_offset, body_end[1] + leg_height - leg_swing)
        pygame.draw.line(screen, (0, 0, 0), body_end, leg_left, 5)
        pygame.draw.line(screen, (0, 0, 0), body_end, leg_right, 5)

    # Projectiles avec traînée
    for proj in projectiles:
        proj_screen = (int(proj["pos"].x - camera_offset.x), int(proj["pos"].y - camera_offset.y))
        pygame.draw.circle(screen, (150, 255, 150), proj_screen, projectile_radius + 2)
        pygame.draw.circle(screen, (0, 255, 0), proj_screen, projectile_radius)
        pygame.draw.circle(screen, (255, 255, 255), proj_screen, projectile_radius - 3)

    # Monstres (normaux et tanks)
    for monster in monsters:
        monster_screen = (int(monster["pos"].x - camera_offset.x), 
                         int(monster["pos"].y - camera_offset.y))
        
        # Couleur selon flash
        monster_color = (255, 200, 200) if monster["hit_flash"] > 0 else (220, 20, 20)
        
        if monster["is_tank"]:
            # Tank: corps plus gros
            pygame.draw.circle(screen, monster_color, monster_screen, monster_radius + 5)
            pygame.draw.circle(screen, (0, 0, 0), monster_screen, monster_radius + 5, 3)
            
            # Sac à dos
            backpack_x = monster_screen[0] - 15
            backpack_y = monster_screen[1]
            backpack_rect = pygame.Rect(backpack_x - 10, backpack_y - 15, 20, 30)
            pygame.draw.rect(screen, (60, 40, 20), backpack_rect)
            pygame.draw.rect(screen, (0, 0, 0), backpack_rect, 2)
            pygame.draw.circle(screen, (100, 80, 50), (backpack_x, backpack_y - 5), 5)
            
            # Yeux méchants
            pygame.draw.circle(screen, (255, 255, 0), (monster_screen[0] - 8, monster_screen[1] - 5), 4)
            pygame.draw.circle(screen, (255, 255, 0), (monster_screen[0] + 8, monster_screen[1] - 5), 4)
            pygame.draw.circle(screen, (0, 0, 0), (monster_screen[0] - 8, monster_screen[1] - 5), 2)
            pygame.draw.circle(screen, (0, 0, 0), (monster_screen[0] + 8, monster_screen[1] - 5), 2)
            
            # Indicateur HP
            if monster["hp"] == 2:
                pygame.draw.circle(screen, (0, 255, 0), (monster_screen[0], monster_screen[1] - 40), 5)
                pygame.draw.circle(screen, (0, 255, 0), (monster_screen[0] + 12, monster_screen[1] - 40), 5)
            else:
                pygame.draw.circle(screen, (255, 165, 0), (monster_screen[0], monster_screen[1] - 40), 5)
        else:
            # Monstre normal
            pygame.draw.circle(screen, monster_color, monster_screen, monster_radius)
            pygame.draw.circle(screen, (0, 0, 0), monster_screen, monster_radius, 3)
            
            # Yeux
            pygame.draw.circle(screen, (0, 0, 0), (monster_screen[0] - 8, monster_screen[1] - 5), 4)
            pygame.draw.circle(screen, (0, 0, 0), (monster_screen[0] + 8, monster_screen[1] - 5), 4)

    # Particules
    for part in particles:
        if part["life"] > 0:
            part_screen = (int(part["pos"].x - camera_offset.x), int(part["pos"].y - camera_offset.y))
            alpha = int(255 * part["life"])
            color = tuple(min(255, max(0, int(c * part["life"]))) for c in part["color"])
            pygame.draw.circle(screen, color, part_screen, 3)

    # --- HUD ---
    # Panneau semi-transparent
    hud_panel = pygame.Surface((300, 150), pygame.SRCALPHA)
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

    if is_invulnerable:
        inv_text = small_font.render("⚡ INVULNÉRABLE", True, (255, 255, 0))
        screen.blit(inv_text, (30, 120))

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
        pygame.time.delay(3000)
        running = False

    if lives <= 0:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        
        over_text = pygame.font.SysFont(None, 96).render("GAME OVER", True, (255, 50, 50))
        score_final = font.render(f"Score: {score}", True, (255, 255, 255))
        
        screen.blit(over_text, (SCREEN_WIDTH//2 - over_text.get_width()//2, SCREEN_HEIGHT//2 - 60))
        screen.blit(score_final, (SCREEN_WIDTH//2 - score_final.get_width()//2, SCREEN_HEIGHT//2 + 20))
        pygame.display.flip()
        pygame.time.delay(2000)
        
        lives = 3
        score = 0
        player_pos = spawn_point.copy()
        player_vel_y = 0
        camera_offset = pygame.Vector2(0, 0)
        monsters = [spawn_monster() for _ in range(MAX_MONSTERS)]
        projectiles = []
        particles = []

    pygame.display.flip()
    dt = clock.tick(FPS) / 1000

pygame.quit()
