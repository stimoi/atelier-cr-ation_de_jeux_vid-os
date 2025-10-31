import pygame
import random
import math

# === Initialisation ===
pygame.init()
screen = pygame.display.set_mode((1366, 769))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 48)

# === Constantes ===
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
GROUND_Y = 680
GRAVITY = 800
JUMP_FORCE = -600
MOVE_SPEED = 300
PROJECTILE_SPEED = 600
FPS = 60

# === Caméra ===
camera_offset = pygame.Vector2(0, 0)
CAMERA_LAG = 0.05 


# === Joueur ===
player_pos = pygame.Vector2(SCREEN_WIDTH / 2, GROUND_Y)
head_radius = 20
body_height = 40
leg_height = 30
arm_length = 25
skin_color = (220, 180, 140)
player_vel_y = 0
direction = 1
walk_cycle = 0

player_pos.y = GROUND_Y - (head_radius + body_height + leg_height)
spawn_point = player_pos.copy() 

# === Projectiles ===
projectiles = []
projectile_radius = 8

# === Ennemis ===
MONSTER_PROPS = {
    # Type: [Radius, Speed, Color, Score, Y_Offset_from_Ground]
    "basic": {"radius": 25, "speed": 80, "color": "red", "score": 1, "y_offset": 0},
    "flyer": {"radius": 15, "speed": 150, "color": "blue", "score": 2, "y_offset": 150},
    "tank": {"radius": 40, "speed": 50, "color": "darkgreen", "score": 3, "y_offset": 0}
}
MAX_MONSTERS = 5 # Augmentation du nombre maximum

def spawn_monster():
    type_choice = random.choice(["basic", "flyer", "tank"])
    props = MONSTER_PROPS[type_choice]
    
    # Zone de spawn large dans le monde
    x = random.randint(100, 2500)
    # Position Y ajustée pour que le bas du monstre soit au sol + l'offset du type
    y_ground_level = GROUND_Y - (props["radius"] * 2) 
    y = y_ground_level - props["y_offset"]
    
    return {
        "pos": pygame.Vector2(x, y),
        "dir": random.choice([-1, 1]),
        "type": type_choice,
        "base_y": y, # Position Y de base pour l'oscillation du flyer
        "sin_offset": random.random() * math.pi * 2 # Décalage pour l'animation/mouvement périodique
    }

monsters = [spawn_monster() for _ in range(MAX_MONSTERS)]

# === Plateformes (parcours) ===
platforms = [
    pygame.Rect(100, 560, 200, 20),
    pygame.Rect(380, 480, 180, 20),
    pygame.Rect(620, 420, 160, 20),
    pygame.Rect(860, 360, 140, 20),
    pygame.Rect(1060, 300, 180, 20),
    pygame.Rect(1300, 200, 250, 20), 
    pygame.Rect(1600, 150, 300, 20), 
    pygame.Rect(2000, 100, 400, 20), # Dernière plateforme à Y=100
]

# Goal flag (coordonnées mondiales) - Agrandissement (80x100)
goal_rect = pygame.Rect(2300, 0, 80, 100) # (Y=0 pour que le bas soit à Y=100 sur la dernière plateforme)

# Respawn point (coordonnées mondiales)
spawn_point = pygame.Vector2(SCREEN_WIDTH / 2, GROUND_Y - (head_radius + body_height + leg_height))

# === Vies et Statut ===
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
            # Tir au clic gauche
            proj_x = player_pos.x + direction * (head_radius + 10)
            proj_y = player_pos.y
            projectiles.append({
                "pos": pygame.Vector2(proj_x, proj_y),
                "dir": direction
            })

    # --- LOGIQUE DU JEU ---

    # Mouvements joueur
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

    # Détection de plateforme / sol
    feet_y = player_pos.y + head_radius + body_height + leg_height
    on_ground = False
    
    # Vérification sol
    if feet_y >= GROUND_Y - 0.1:
        on_ground = True
    # Vérification plateformes
    else:
        for plat in platforms:
            # Check si les pieds sont juste au-dessus de la plateforme
            if plat.left - 5 < player_pos.x < plat.right + 5 and abs(feet_y - plat.top) <= 6:
                on_ground = True
                player_pos.y = plat.top - (head_radius + body_height + leg_height)
                player_vel_y = 0
                break

    # Saut
    if keys[pygame.K_SPACE] and on_ground:
        player_vel_y = JUMP_FORCE

    # Gravité et mouvement vertical
    player_vel_y += GRAVITY * dt
    player_pos.y += player_vel_y * dt

    # Collision sol (finale)
    feet_y = player_pos.y + head_radius + body_height + leg_height
    if feet_y > GROUND_Y:
        player_pos.y = GROUND_Y - (head_radius + body_height + leg_height)
        player_vel_y = 0

    # Collision plateformes (si on descend)
    player_rect = pygame.Rect(int(player_pos.x - head_radius), int(player_pos.y - head_radius), head_radius*2, head_radius*2 + body_height + leg_height)
    if player_vel_y >= 0:
        for plat in platforms:
            if player_rect.colliderect(plat):
                plat_top = plat.top
                if feet_y - player_vel_y * dt <= plat_top: # Si les pieds étaient au-dessus précédemment
                    player_pos.y = plat_top - (head_radius + body_height + leg_height)
                    player_vel_y = 0
                    break

    # Si on tombe trop bas -> respawn
    if player_pos.y > GROUND_Y + 500:
        player_pos = spawn_point.copy()
        player_vel_y = 0

    # === Mise à jour de la Caméra ===
    target_x = player_pos.x - SCREEN_WIDTH // 2
    target_y = player_pos.y - SCREEN_HEIGHT // 2

    camera_offset.x += (target_x - camera_offset.x) * CAMERA_LAG
    camera_offset.y += (target_y - camera_offset.y) * CAMERA_LAG


    # Projectiles
    for proj in projectiles[:]:
        proj["pos"].x += proj["dir"] * PROJECTILE_SPEED * dt
        # Vérification sortie d'écran monde
        if proj["pos"].x < camera_offset.x - 100 or proj["pos"].x > camera_offset.x + SCREEN_WIDTH + 100:
            projectiles.remove(proj)

    # Collision projectile-monstre
    for proj in projectiles[:]:
        for monster in monsters[:]:
            monster_props = MONSTER_PROPS[monster["type"]]
            monster_radius = monster_props["radius"]
            
            if proj["pos"].distance_to(monster["pos"]) < projectile_radius + monster_radius:
                monsters.remove(monster)
                if proj in projectiles:
                    projectiles.remove(proj)
                score += monster_props["score"]
                break # Le projectile a touché, on passe au suivant


    # Réapparition des monstres
    while len(monsters) < MAX_MONSTERS:
        monsters.append(spawn_monster())

    # Monstres (mouvement)
    for monster in monsters:
        props = MONSTER_PROPS[monster["type"]]
        
        if monster["type"] == "basic" or monster["type"] == "tank":
            # Patrouille simple au sol
            monster["pos"].x += monster["dir"] * props["speed"] * dt
            if monster["pos"].x < 50:
                monster["dir"] = 1
            if monster["pos"].x > 2500:
                monster["dir"] = -1
        
        elif monster["type"] == "flyer":
            # Patrouille horizontale + oscillation verticale
            monster["pos"].x += monster["dir"] * props["speed"] * dt
            
            # Oscillation verticale sinusoïdale (amplitude 50, fréquence 4)
            monster["pos"].y = monster["base_y"] + math.sin(pygame.time.get_ticks() / 1000 * 4 + monster["sin_offset"]) * 50
            
            if monster["pos"].x < 50 or monster["pos"].x > 2500:
                monster["dir"] *= -1

    # Collision joueur-ennemi (si pas invulnérable)
    p_center = (int(player_pos.x), int(player_pos.y))
    if not is_invulnerable:
        for monster in monsters[:]:
            monster_props = MONSTER_PROPS[monster["type"]]
            monster_radius = monster_props["radius"]
            
            if pygame.Vector2(p_center).distance_to(monster["pos"]) < head_radius + monster_radius:
                # Hit
                lives -= 1
                is_invulnerable = True
                invuln_timer = invuln_time
                # Respawn
                player_pos = spawn_point.copy()
                player_vel_y = 0
                break

    # Gérer timer d'invulnérabilité
    if is_invulnerable:
        invuln_timer -= dt
        if invuln_timer <= 0:
            is_invulnerable = False
    
    # Vérifier goal -> déclencher victoire
    if not victory and pygame.Rect(int(player_pos.x - head_radius), int(player_pos.y - head_radius), head_radius*2, head_radius*2).colliderect(goal_rect):
        victory = True


    # --- DESSIN ---

    # Efface l'écran
    screen.fill("purple")
    # Sol
    pygame.draw.rect(screen, "gray", (0 - camera_offset.x, GROUND_Y - camera_offset.y, 3000, 100))

    # Dessiner plateformes
    for plat in platforms:
        plat_rect_screen = plat.move(-camera_offset.x, -camera_offset.y)
        pygame.draw.rect(screen, (100, 100, 100), plat_rect_screen)

    # Dessiner objectif (Porte agrandie)
    goal_rect_screen = goal_rect.move(-camera_offset.x, -camera_offset.y)
    pygame.draw.rect(screen, (200, 160, 60), goal_rect_screen)  # door base
    pygame.draw.rect(screen, (80, 50, 20), goal_rect_screen, 4) # door frame
    # Bouton centré verticalement
    knob_pos = (goal_rect_screen.right - 12, goal_rect_screen.top + goal_rect_screen.height * 0.5) 
    pygame.draw.circle(screen, (30, 30, 30), knob_pos, 5)

    # Joueur
    p_center_screen_x = int(player_pos.x - camera_offset.x)
    p_center_screen_y = int(player_pos.y - camera_offset.y)
    p_center_screen = (p_center_screen_x, p_center_screen_y)

    # Rendu du joueur (clignotement si invulnérable)
    if not is_invulnerable or int(invuln_timer * 10) % 2 == 0:
        # Tête
        pygame.draw.circle(screen, skin_color, p_center_screen, head_radius)
        pygame.draw.circle(screen, "black", p_center_screen, head_radius, 2)
        # Bouche
        pygame.draw.arc(screen, "black", (p_center_screen[0] - head_radius, p_center_screen[1] - head_radius, head_radius*2, head_radius*2), 3.8, 5.0, 3)

        # Corps
        body_start = (p_center_screen[0], p_center_screen[1] + head_radius)
        body_end = (p_center_screen[0], p_center_screen[1] + head_radius + body_height)
        pygame.draw.line(screen, "black", body_start, body_end, 4)

        # Bras animés
        arm_y = p_center_screen[1] + head_radius + 15
        arm_angle = math.sin(walk_cycle * 10) * 10
        arm_offset = arm_length * math.cos(math.radians(arm_angle))
        pygame.draw.line(screen, "black", (p_center_screen[0] - arm_offset, arm_y), (p_center_screen[0] + arm_offset, arm_y), 4)

        # Jambes animées
        leg_offset = 15
        leg_swing = math.sin(walk_cycle * 10) * 10
        leg_left = (p_center_screen[0] - leg_offset, body_end[1] + leg_height + leg_swing)
        leg_right = (p_center_screen[0] + leg_offset, body_end[1] + leg_height - leg_swing)
        pygame.draw.line(screen, "black", body_end, leg_left, 4)
        pygame.draw.line(screen, "black", body_end, leg_right, 4)
        
        # Yeux
        pygame.draw.arc(screen, "black", (p_center_screen[0] - 10, p_center_screen[1] - 5, 20, 20), 3.7, 5.6, 2)


    # Projectiles
    for proj in projectiles:
        proj_screen_x = int(proj["pos"].x - camera_offset.x)
        proj_screen_y = int(proj["pos"].y - camera_offset.y)
        pygame.draw.circle(screen, (0, 255, 0), (proj_screen_x, proj_screen_y), projectile_radius)

    # Monstres
    for monster in monsters:
        props = MONSTER_PROPS[monster["type"]]
        monster_screen_x = int(monster["pos"].x - camera_offset.x)
        monster_screen_y = int(monster["pos"].y - camera_offset.y)
        
        # Dessiner le monstre
        pygame.draw.circle(screen, props["color"], (monster_screen_x, monster_screen_y), props["radius"])
        
        # Effet visuel pour le Tank (cercle noir intérieur)
        if monster["type"] == "tank":
            pygame.draw.circle(screen, "black", (monster_screen_x, monster_screen_y), props["radius"], 3)
        
        # Effet visuel pour le Flyer (petit point blanc intérieur)
        if monster["type"] == "flyer":
             pygame.draw.circle(screen, "white", (monster_screen_x, monster_screen_y), 5)


    # --- HUD ---
    score_text = font.render(f"Score : {score}", True, (255, 255, 255))
    screen.blit(score_text, (30, 30))
    lives_text = font.render(f"Vies : {lives}", True, (255, 50, 50))
    screen.blit(lives_text, (30, 70))

    if is_invulnerable:
        inv_text = font.render("Invulnérable", True, (255, 255, 0))
        screen.blit(inv_text, (30, 110))

    # Messages de fin de jeu
    if victory:
        big_text = pygame.font.SysFont(None, 96).render("VICTOIRE !", True, (255, 215, 0))
        sub_text = font.render("Tu as terminé le parcours", True, (255, 255, 255))
        screen.blit(big_text, (SCREEN_WIDTH//2 - big_text.get_width()//2, SCREEN_HEIGHT//2 - 80))
        screen.blit(sub_text, (SCREEN_WIDTH//2 - sub_text.get_width()//2, SCREEN_HEIGHT//2 + 20))
        pygame.display.flip()
        pygame.time.delay(2500)
        running = False

    # Game Over et reset
    if lives <= 0:
        over_text = font.render("Game Over", True, (255, 0, 0))
        screen.blit(over_text, (SCREEN_WIDTH//2 - over_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
        pygame.display.flip()
        pygame.time.delay(1500)
        
        # Reset
        lives = 3
        score = 0
        monsters = [spawn_monster() for _ in range(MAX_MONSTERS)] # Remplir les monstres
        player_pos = spawn_point.copy()
        player_vel_y = 0
        camera_offset = pygame.Vector2(0, 0)

    pygame.display.flip()
    dt = clock.tick(FPS) / 1000

pygame.quit()
