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
MAX_MONSTERS = 3

# === Caméra ===
# Le décalage de la caméra par rapport au coin supérieur gauche du monde
camera_offset = pygame.Vector2(0, 0)
# La caméra essaie de centrer le joueur
CAMERA_LAG = 0.05 # Facteur d'interpolation pour un suivi plus doux (entre 0 et 1)


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

# Position initiale
player_pos.y = GROUND_Y - (head_radius + body_height + leg_height)
spawn_point = player_pos.copy() # Mis à jour pour utiliser la position initiale

# === Projectiles ===
projectiles = []
projectile_radius = 8

# === Ennemis ===
monster_radius = 25
def spawn_monster():
    # Les monstres sont générés dans le monde entier, pas seulement sur l'écran visible
    x = random.randint(100, 2500) # Élargissement de la zone de spawn pour le monde
    y = GROUND_Y - (head_radius + body_height + leg_height)
    return pygame.Vector2(x, y)

monsters = [{"pos": spawn_monster(), "dir": random.choice([-1, 1])} for _ in range(MAX_MONSTERS)]

# === Plateformes (parcours) ===
# Les plateformes ont des coordonnées mondiales
platforms = [
    pygame.Rect(100, 560, 200, 20),
    pygame.Rect(380, 480, 180, 20),
    pygame.Rect(620, 420, 160, 20),
    pygame.Rect(860, 360, 140, 20),
    pygame.Rect(1060, 300, 180, 20),
    pygame.Rect(1300, 200, 250, 20), # Nouvelle plateforme
    pygame.Rect(1600, 150, 300, 20), # Nouvelle plateforme
    pygame.Rect(2000, 100, 400, 20), # Nouvelle plateforme
]

# Goal flag (coordonnées mondiales)
goal_rect = pygame.Rect(2300, 40, 40, 60)

# Respawn point (coordonnées mondiales)
spawn_point = pygame.Vector2(SCREEN_WIDTH / 2, GROUND_Y - (head_radius + body_height + leg_height))

# === Score ===
score = 0
# === Vies ===
lives = 3
invuln_time = 1.5  # secondes d'invulnérabilité après hit
invuln_timer = 0.0
is_invulnerable = False
# Victoire
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

    # Détection si on est sur le sol ou sur une plateforme (avant application de la gravité)
    feet_y = player_pos.y + head_radius + body_height + leg_height
    on_ground = False
    # sol
    if feet_y >= GROUND_Y - 0.1:
        on_ground = True
    # plateformes
    else:
        for plat in platforms:
            if plat.left - 5 < player_pos.x < plat.right + 5 and abs(feet_y - plat.top) <= 6:
                on_ground = True
                # Align exactly on top to avoid small sinking
                player_pos.y = plat.top - (head_radius + body_height + leg_height)
                player_vel_y = 0
                break

    # Saut uniquement si on est au sol ou sur une plateforme
    if keys[pygame.K_SPACE] and on_ground:
        player_vel_y = JUMP_FORCE

    # Gravité et mouvement vertical
    player_vel_y += GRAVITY * dt
    player_pos.y += player_vel_y * dt

    # Collision sol
    feet_y = player_pos.y + head_radius + body_height + leg_height
    if feet_y > GROUND_Y:
        player_pos.y = GROUND_Y - (head_radius + body_height + leg_height)
        player_vel_y = 0

    # Collision plateformes (si on descend)
    player_rect = pygame.Rect(int(player_pos.x - head_radius), int(player_pos.y - head_radius), head_radius*2, head_radius*2 + body_height + leg_height)
    if player_vel_y >= 0:  # seulement si on descend
        for plat in platforms:
            # vérifier si les pieds traversent la plateforme
            if player_rect.colliderect(plat):
                # si les pieds étaient au-dessus de la plateforme précédemment
                plat_top = plat.top
                if feet_y - player_vel_y * dt <= plat_top:
                    # placer les pieds sur la plateforme
                    player_pos.y = plat_top - (head_radius + body_height + leg_height)
                    player_vel_y = 0
                    break

    # Limites écran (optionnel : dépend si le monde a des bords)
    # player_pos.x = max(head_radius, min(SCREEN_WIDTH - head_radius, player_pos.x))
    player_pos.y = max(head_radius, player_pos.y)

    # Si on tombe trop bas -> respawn
    if player_pos.y > GROUND_Y + 500: # Tombe loin sous le sol visible
        player_pos = spawn_point.copy()
        player_vel_y = 0

    # === Mise à jour de la Caméra ===
    # Position du centre de l'écran par rapport au monde (où la caméra devrait être)
    target_x = player_pos.x - SCREEN_WIDTH // 2
    target_y = player_pos.y - SCREEN_HEIGHT // 2

    # Assouplissement (Lag) de la caméra pour un mouvement plus agréable
    camera_offset.x += (target_x - camera_offset.x) * CAMERA_LAG
    camera_offset.y += (target_y - camera_offset.y) * CAMERA_LAG

    # Limites de la caméra (empêche de voir en dehors des limites du monde si nécessaire)
    # Pour l'instant, on laisse la caméra suivre librement pour montrer le monde élargi.

    # Projectiles
    for proj in projectiles[:]:
        proj["pos"].x += proj["dir"] * PROJECTILE_SPEED * dt
        # La vérification de sortie d'écran doit se faire par rapport aux limites du MONDE
        # ou aux limites de la vue actuelle si le monde est infini
        if proj["pos"].x < camera_offset.x - 100 or proj["pos"].x > camera_offset.x + SCREEN_WIDTH + 100:
            projectiles.remove(proj)

    # Collision projectile-monstre
    for proj in projectiles[:]:
        for monster in monsters[:]:
            if proj["pos"].distance_to(monster["pos"]) < projectile_radius + monster_radius:
                monsters.remove(monster)
                if proj in projectiles:
                    projectiles.remove(proj)
                score += 1

    # Réapparition des monstres
    while len(monsters) < MAX_MONSTERS:
        monsters.append({"pos": spawn_monster(), "dir": random.choice([-1, 1])})

    # Monstres (mouvement)
    for monster in monsters:
        # simple patrol, élargir la zone de patrouille
        monster["pos"].x += monster["dir"] * 80 * dt
        if monster["pos"].x < 50:
            monster["dir"] = 1
        if monster["pos"].x > 2500: # Utiliser une limite plus large
            monster["dir"] = -1

    # Collision joueur-ennemi (si pas invulnérable)
    p_center = (int(player_pos.x), int(player_pos.y))
    if not is_invulnerable:
        for monster in monsters[:]:
            if pygame.Vector2(p_center).distance_to(monster["pos"]) < head_radius + monster_radius:
                # On subit un hit
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
    # Sol (coordonnées écran = coordonnées monde - décalage)
    pygame.draw.rect(screen, "gray", (0 - camera_offset.x, GROUND_Y - camera_offset.y, 3000, 100))

    # Dessiner plateformes
    for plat in platforms:
        # Appliquer l'offset à la position de la plateforme
        plat_rect_screen = plat.move(-camera_offset.x, -camera_offset.y)
        pygame.draw.rect(screen, (100, 100, 100), plat_rect_screen)

    # Dessiner objectif
    goal_rect_screen = goal_rect.move(-camera_offset.x, -camera_offset.y)
    pygame.draw.rect(screen, (200, 160, 60), goal_rect_screen)  # door base
    pygame.draw.rect(screen, (80, 50, 20), goal_rect_screen, 4) # door frame
    knob_pos = (goal_rect_screen.right - 12, goal_rect_screen.centery)
    pygame.draw.circle(screen, (30, 30, 30), knob_pos, 5)

    # Joueur animé (p_center est la position du joueur à l'écran)
    p_center_screen_x = int(player_pos.x - camera_offset.x)
    p_center_screen_y = int(player_pos.y - camera_offset.y)
    p_center_screen = (p_center_screen_x, p_center_screen_y)

    # Rendu du joueur (sauf si invulnérable et en phase de clignotement)
    if not is_invulnerable or int(invuln_timer * 10) % 2 == 0:
        pygame.draw.circle(screen, skin_color, p_center_screen, head_radius)
        pygame.draw.circle(screen, "black", p_center_screen, head_radius, 2)
        pygame.draw.arc(screen, "black", (p_center_screen[0] - head_radius, p_center_screen[1] - head_radius, head_radius*2, head_radius*2), 3.8, 5.0, 3)

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

        pygame.draw.arc(screen, "black", (p_center_screen[0] - 10, p_center_screen[1] - 5, 20, 20), 3.7, 5.6, 2)


    # Projectiles
    for proj in projectiles:
        proj_screen_x = int(proj["pos"].x - camera_offset.x)
        proj_screen_y = int(proj["pos"].y - camera_offset.y)
        pygame.draw.circle(screen, (0, 255, 0), (proj_screen_x, proj_screen_y), projectile_radius)

    # Monstres
    for monster in monsters:
        monster_screen_x = int(monster["pos"].x - camera_offset.x)
        monster_screen_y = int(monster["pos"].y - camera_offset.y)
        pygame.draw.circle(screen, "red", (monster_screen_x, monster_screen_y), monster_radius)


    # --- HUD (Interface utilisateur, NE BOUGE PAS AVEC LA CAMÉRA) ---

    # Score & Lives
    score_text = font.render(f"Score : {score}", True, (255, 255, 255))
    screen.blit(score_text, (30, 30))
    lives_text = font.render(f"Vies : {lives}", True, (255, 50, 50))
    screen.blit(lives_text, (30, 70))

    # Indicateur d'invulnérabilité
    if is_invulnerable:
        inv_text = font.render("Invulnérable", True, (255, 255, 0))
        screen.blit(inv_text, (30, 110))

    # Messages de fin de jeu (ne bougent pas non plus)
    if victory:
        big_text = pygame.font.SysFont(None, 96).render("VICTOIRE !", True, (255, 215, 0))
        sub_text = font.render("Tu as terminé le parcours", True, (255, 255, 255))
        screen.blit(big_text, (SCREEN_WIDTH//2 - big_text.get_width()//2, SCREEN_HEIGHT//2 - 80))
        screen.blit(sub_text, (SCREEN_WIDTH//2 - sub_text.get_width()//2, SCREEN_HEIGHT//2 + 20))
        pygame.display.flip()
        pygame.time.delay(2500)
        running = False

    # Si vies à 0 -> Game Over et reset lvl
    if lives <= 0:
        over_text = font.render("Game Over", True, (255, 0, 0))
        screen.blit(over_text, (SCREEN_WIDTH//2 - over_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
        pygame.display.flip()
        pygame.time.delay(1500)
        # Reset
        lives = 3
        score = 0
        player_pos = spawn_point.copy()
        player_vel_y = 0
        camera_offset = pygame.Vector2(0, 0) # Réinitialiser la caméra aussi

    pygame.display.flip()
    dt = clock.tick(FPS) / 1000

pygame.quit()
