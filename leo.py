import pygame
import random
import math
import json
import os
from copy import deepcopy

# === Initialisation ===
pygame.init()
screen = pygame.display.set_mode((1366, 769))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 48)
small_font = pygame.font.SysFont(None, 32)
title_font = pygame.font.SysFont(None, 96)
fword_font = pygame.font.SysFont(None, 180)

tutorial_texts = {}
current_tutorial_texts = []
tutorial_visible = False
tutorial_index = 0
tutorial_button_rect = None
tutorial_image = None
tutorial_image_cache = {}

def _wrap_text_lines(text, font, max_width):
    lines = []
    if not text:
        return lines
    for raw_paragraph in text.split("\n"):
        paragraph = raw_paragraph.strip()
        if not paragraph:
            lines.append("")
            continue
        words = paragraph.split()
        current = words[0]
        for word in words[1:]:
            potential = f"{current} {word}"
            if font.size(potential)[0] <= max_width:
                current = potential
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines

def _get_tutorial_image(max_width, max_height):
    if tutorial_image is None:
        return None
    key = (max_width, max_height)
    cached = tutorial_image_cache.get(key)
    if cached:
        return cached
    src_w, src_h = tutorial_image.get_size()
    if src_w == 0 or src_h == 0:
        tutorial_image_cache[key] = tutorial_image
        return tutorial_image
    scale = min(max_width / src_w, max_height / src_h)
    scale = max(scale, 0.01)
    new_size = (max(1, int(src_w * scale)), max(1, int(src_h * scale)))
    scaled = pygame.transform.smoothscale(tutorial_image, new_size)
    tutorial_image_cache[key] = scaled
    return scaled


def _normalize_key(value):
    return "".join(ch for ch in str(value).lower() if ch.isalnum())

def _extract_text(entry):
    if isinstance(entry, str):
        text = entry.strip()
        return text if text else None
    if isinstance(entry, dict):
        for field in ("texte", "text", "message", "content"):
            if field in entry and isinstance(entry[field], str):
                text = entry[field].strip()
                if text:
                    return text
    return None

def _coerce_text_list(value):
    texts = []
    if isinstance(value, list):
        for item in value:
            text = _extract_text(item)
            if text:
                texts.append(text)
    elif isinstance(value, dict):
        try:
            items = sorted(value.items(), key=lambda kv: int(kv[0]))
        except Exception:
            items = value.items()
        for _, item in items:
            text = _extract_text(item)
            if text:
                texts.append(text)
    else:
        text = _extract_text(value)
        if text:
            texts.append(text)
    return texts

def load_tutorial_texts():
    texts = {}
    tutoriel_dir = os.path.join(os.path.dirname(__file__), "tutoriel")
    texte_path = os.path.join(tutoriel_dir, "texte.json")
    if not os.path.isfile(texte_path):
        return texts
    try:
        with open(texte_path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
    except Exception:
        return texts

    if isinstance(data, dict):
        for key, value in data.items():
            entries = _coerce_text_list(value)
            if entries:
                texts[_normalize_key(key)] = entries
    else:
        entries = _coerce_text_list(data)
        if entries:
            texts[_normalize_key("niveau1")] = entries
    return texts

def load_tutorial_image():
    tutoriel_dir = os.path.join(os.path.dirname(__file__), "tutoriel")
    image_path = os.path.join(tutoriel_dir, "photo.png")
    if os.path.isfile(image_path):
        try:
            return pygame.image.load(image_path).convert_alpha()
        except Exception:
            pass
    placeholder = pygame.Surface((200, 200), pygame.SRCALPHA)
    placeholder.fill((210, 210, 210, 255))
    pygame.draw.rect(placeholder, (160, 160, 160, 255), placeholder.get_rect(), 6, border_radius=12)
    pygame.draw.line(placeholder, (160, 160, 160, 255), (30, 30), (170, 170), 6)
    pygame.draw.line(placeholder, (160, 160, 160, 255), (170, 30), (30, 170), 6)
    return placeholder

tutorial_texts = load_tutorial_texts()
tutorial_image = load_tutorial_image()


def select_tutorial_for_level(level):
    global current_tutorial_texts, tutorial_visible, tutorial_index
    if not level:
        current_tutorial_texts = []
        tutorial_visible = False
        tutorial_index = 0
        return
    key = _normalize_key(level.get("name", ""))
    entries = tutorial_texts.get(key)
    if not entries:
        fallback_key = _normalize_key("niveau1")
        entries = tutorial_texts.get(fallback_key, [])
    current_tutorial_texts = list(entries)
    tutorial_index = 0
    tutorial_visible = False


def draw_tutorial_overlay():
    global tutorial_button_rect
    if not tutorial_visible or not current_tutorial_texts:
        tutorial_button_rect = None
        return

    panel_margin_x = 50
    panel_margin_y = 30
    panel_width = SCREEN_WIDTH - panel_margin_x * 2
    panel_height = 200
    panel_x = panel_margin_x
    panel_y = SCREEN_HEIGHT - panel_height - panel_margin_y
    panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

    tutorial_button_rect = panel_rect

    panel_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
    panel_surface.fill((12, 23, 42, 220))
    pygame.draw.rect(panel_surface, (56, 130, 203, 220), panel_surface.get_rect(), 3, border_radius=18)

    content_padding = 24
    text_area_width = panel_rect.width - content_padding * 2
    image_surface = _get_tutorial_image(220, panel_height - content_padding * 2)
    image_width = image_surface.get_width() if image_surface else 0
    if image_surface:
        text_area_width -= image_width + 24

    current_text = current_tutorial_texts[min(tutorial_index, len(current_tutorial_texts) - 1)]
    wrapped_lines = _wrap_text_lines(current_text, small_font, text_area_width)

    text_x = content_padding
    text_y = content_padding
    text_color = (235, 245, 255)
    for line in wrapped_lines:
        line_surf = small_font.render(line, True, text_color)
        panel_surface.blit(line_surf, (text_x, text_y))
        text_y += line_surf.get_height() + 6

    progress_text = f"{tutorial_index + 1}/{len(current_tutorial_texts)}"
    progress_surf = small_font.render(progress_text, True, (180, 210, 255))
    panel_surface.blit(progress_surf, (text_x, panel_rect.height - content_padding - progress_surf.get_height()))

    hint_text = "Cliquez pour continuer"
    hint_surf = small_font.render(hint_text, True, (120, 180, 255))
    hint_pos_x = panel_rect.width - content_padding - hint_surf.get_width() - (image_width + 24 if image_surface else 0)
    panel_surface.blit(hint_surf, (max(text_x, hint_pos_x), panel_rect.height - content_padding - hint_surf.get_height()))

    if image_surface:
        img_x = panel_rect.width - content_padding - image_surface.get_width()
        img_y = (panel_rect.height - image_surface.get_height()) // 2
        panel_surface.blit(image_surface, (img_x, img_y))

    screen.blit(panel_surface, panel_rect.topleft)

def start_tutorial():
    global tutorial_visible, tutorial_index
    if current_tutorial_texts:
        tutorial_index = 0
        tutorial_visible = True
    else:
        tutorial_visible = False


def hide_tutorial():
    global tutorial_visible
    tutorial_visible = False


def toggle_tutorial_visibility():
    global tutorial_visible
    if current_tutorial_texts:
        tutorial_visible = not tutorial_visible


def advance_tutorial_text():
    global tutorial_visible, tutorial_index
    if not tutorial_visible or not current_tutorial_texts:
        return
    tutorial_index += 1
    if tutorial_index >= len(current_tutorial_texts):
        tutorial_visible = False
        tutorial_index = len(current_tutorial_texts) - 1
    tutorial_index = max(0, tutorial_index)

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
SKIN_COLOR = (255, 220, 177)

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
spawn_point = player_pos

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

MONSTER_TYPE_DEFAULTS = {
    "tank": {"radius": 32, "speed": 60, "hp": 3, "dir": 1},
    "fast": {"radius": 18, "speed": 140, "hp": 1, "dir": 1},
    "flyer": {"radius": 22, "speed": 110, "hp": 1, "dir": 1},
    "basic": {"radius": 20, "speed": 100, "hp": 1, "dir": 1},
}

level_enemy_configs = []
current_monster_cap = MAX_MONSTERS
monsters = []


def _canonical_monster_type(raw_type):
    if not raw_type:
        return "basic"
    t = str(raw_type).lower()
    if t in MONSTER_TYPE_DEFAULTS:
        return t
    if t in ("walker", "ground"):
        return "basic"
    return "basic"


def create_monster_from_config(config, template_id=None):
    cfg = deepcopy(config)
    m_type = _canonical_monster_type(cfg.get("type"))
    defaults = MONSTER_TYPE_DEFAULTS[m_type]

    x = float(cfg.get("x", 0))
    y = float(cfg.get("y", 0))
    width = cfg.get("w") or cfg.get("width")
    height = cfg.get("h") or cfg.get("height")

    radius = cfg.get("radius")
    if radius is None:
        if width and height:
            radius = max(width, height) / 2
        else:
            radius = defaults["radius"]

    speed = cfg.get("speed", defaults["speed"])
    hp = int(cfg.get("hp", defaults["hp"]))
    dir_val = cfg.get("dir", defaults["dir"])
    direction = -1 if float(dir_val) < 0 else 1

    monster = {
        "pos": pygame.Vector2(x, y),
        "dir": direction,
        "type": m_type,
        "radius": radius,
        "speed": speed,
        "hp": hp,
        "hit_flash": 0.0,
    }

    if m_type == "flyer":
        base_y = float(cfg.get("base_y", y))
        monster.update({
            "fly_phase": float(cfg.get("fly_phase", 0.0)),
            "base_y": base_y,
        })
    else:
        monster["vel_y"] = float(cfg.get("vel_y", 0.0))

    if template_id is not None:
        monster["template_id"] = template_id

    return monster


def instantiate_level_enemies():
    global monsters, current_monster_cap, monster_spawn_timer
    if level_enemy_configs:
        monsters = []
        for idx, cfg in enumerate(level_enemy_configs):
            monsters.append(create_monster_from_config(cfg, template_id=idx))
        current_monster_cap = len(level_enemy_configs)
    else:
        monsters = [spawn_monster() for _ in range(MAX_MONSTERS)]
        current_monster_cap = MAX_MONSTERS
    monster_spawn_timer = 0.0

# === Multi-niveaux: chargement levels.json et application d'un niveau ===
def _default_level():
    return {
        "name": "Niveau 1",
        "ground": {"y": 0, "start_x": 0, "end_x": 10000},
        "spawn": {"x": 40, "y": -40},
        "goal": {"x": 1000, "y": -110, "w": 70, "h": 110},
        "platforms": [],
    }

levels = []
levels_dir = os.path.dirname(__file__)
level_filenames = ["levels.json"]  # support ancien et nouveau nommage
for name in level_filenames:
    level_path = os.path.join(levels_dir, name)
    if not os.path.isfile(level_path):
        continue
    try:
        with open(level_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and isinstance(data.get("levels"), list) and data["levels"]:
                levels = data["levels"]
                break
    except Exception:
        continue

if not levels:
    levels = [_default_level()]

selected_level_idx = 0

platforms = []
goal_rect = pygame.Rect(0, 0, 0, 0)
spawn_point = pygame.Vector2(0, 0)

def apply_level(level):
    global GROUND_Y, GROUND_START_X, GROUND_END_X, platforms, goal_rect, spawn_point, level_enemy_configs
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
    # Ennemis
    level_enemy_configs = []
    raw_enemies = level.get("enemies", [])
    if isinstance(raw_enemies, list):
        for entry in raw_enemies:
            if isinstance(entry, dict):
                level_enemy_configs.append(deepcopy(entry))
    select_tutorial_for_level(level)

# Appliquer le niveau initial
apply_level(levels[selected_level_idx])
instantiate_level_enemies()
init_clouds()

# === Score, Vies, Victoire ===
score = 0
lives = 3
invuln_time = 1.5
invuln_timer = 0.0
is_invulnerable = False
victory = False

LEVEL_TRANSITION_FADE_OUT = 0.6
LEVEL_TRANSITION_FADE_IN = 0.6
level_transition_active = False
level_transition_phase = "fade_out"
level_transition_timer = 0.0
level_transition_next_idx = None

# === Etat du jeu ===
game_state = "MENU"  # MENU, PLAYING, PAUSED
fword_timer = 0.0

# === Boucle principale ===
running = True
dt = 0
cnt = 0

while running:
    cnt = (cnt+1)%4
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
            break
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if game_state == "MENU":
                running = False
                break
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
            if tutorial_visible and tutorial_button_rect and tutorial_button_rect.collidepoint(event.pos):
                advance_tutorial_text()
                continue
            if game_state == "MENU":
                if play_rect.collidepoint(event.pos):
                    # Reset du jeu
                    score = 0
                    lives = 3
                    invuln_timer = 0.0
                    is_invulnerable = False
                    victory = False
                    level_transition_active = False
                    level_transition_phase = "fade_out"
                    level_transition_timer = 0.0
                    level_transition_next_idx = None
                    # Appliquer le niveau sélectionné au démarrage
                    apply_level(levels[selected_level_idx])
                    instantiate_level_enemies()
                    player_pos = spawn_point
                    player_vel_y = 0
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
                    start_tutorial()
                elif quit_rect.collidepoint(event.pos):
                    running = False
                    break
            elif game_state == "PAUSED":
                if pause_resume_rect.collidepoint(event.pos):
                    game_state = "PLAYING"
                    start_tutorial()
                elif pause_menu_rect.collidepoint(event.pos):
                    game_state = "MENU"
                    hide_tutorial()
                elif pause_quit_rect.collidepoint(event.pos):
                    running = False
                    break
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
                level_transition_active = False
                level_transition_phase = "fade_out"
                level_transition_timer = 0.0
                level_transition_next_idx = None
                # Appliquer le niveau sélectionné au démarrage
                apply_level(levels[selected_level_idx])
                instantiate_level_enemies()
                player_pos = spawn_point
                player_vel_y = 0
                game_state = "PLAYING"
                projectiles = []
                particles = []
                monster_spawn_timer = 0.0
                stamina = STAMINA_MAX
                stamina_idle_timer = 0.0
                jump_was_pressed = False
                dash_was_pressed = False
                dash_timer = 0.0
                dash_direction = 1
                game_state = "PLAYING"
                start_tutorial()
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
        walk_cycle = 10 * dt
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

    blink_timer = 0.0-dt
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
        player_pos = spawn_point
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
    monster_spawn_timer = 0-dt
    if monster_spawn_timer <= 0:
        spawned = False
        if level_enemy_configs:
            active_ids = {m.get("template_id") for m in monsters if m.get("template_id") is not None}
            next_id = None
            for idx in range(len(level_enemy_configs)):
                if idx not in active_ids:
                    next_id = idx
                    break
            if next_id is not None:
                monsters.append(create_monster_from_config(level_enemy_configs[next_id], template_id=next_id))
                spawned = True
        else:
            if len(monsters) < MAX_MONSTERS:
                monsters.append(spawn_monster())
                spawned = True
        if spawned:
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
                player_pos = spawn_point
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
    if (not victory and not level_transition_active and
        pygame.Rect(int(player_pos.x - head_radius), int(player_pos.y - head_radius),
                    head_radius*2, head_radius*2).colliderect(goal_rect)):
        hide_tutorial()
        if selected_level_idx < len(levels) - 1:
            level_transition_active = True
            level_transition_phase = "fade_out"
            level_transition_timer = 0.0
            level_transition_next_idx = selected_level_idx + 1
        else:
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
        if moving:
            movement = ''
            if cnt == 0:
                movement = 'perso.png'
            elif cnt == 1:
                movement = 'perso2.png'
            elif cnt == 2:
                movement = 'perso4.png'
            elif cnt == 3:
                movement = 'perso3.png'
        else:
            movement = 'perso.png'
        # Chargement de l'image
        try:
            image = pygame.image.load(movement).convert_alpha()
        except pygame.error as e:
            print(f"Impossible de charger l'image : {e}")
            pygame.quit()
            sys.exit()

        # Définir les coordonnées de départ pour l'image
        # Nous centrons l'image ici à titre d'exemple
        image_rect = pygame.Rect(p_center_screen[0]+image.get_width(), p_center_screen[1]+image.get_height(), 40, 40)
        image = pygame.transform.scale(image, (image.get_width()*2, image.get_height()*2))

        # Dessiner l'image
        screen.blit(image, image_rect)

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
            try:
                image = pygame.image.load('monster.png').convert_alpha()
            except pygame.error as e:
                print(f"Impossible de charger l'image : {e}")
                pygame.quit()
                sys.exit()

            image_rect = pygame.Rect(monster_screen[0]-image.get_width(), monster_screen[1]-image.get_height(), 40, 40)
            image = pygame.transform.scale(image, (image.get_width()*2, image.get_height()*2))

            # Dessiner l'image
            screen.blit(image, image_rect)

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

    stamina_label = small_font.render("Endurance", True, (180, 200, 255))
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

    if level_transition_active:
        level_transition_timer += dt
        overlay_alpha = 0
        if level_transition_phase == "fade_out":
            if LEVEL_TRANSITION_FADE_OUT > 0:
                overlay_alpha = min(255, int((level_transition_timer / LEVEL_TRANSITION_FADE_OUT) * 255))
            else:
                overlay_alpha = 255
            if level_transition_timer >= LEVEL_TRANSITION_FADE_OUT:
                selected_level_idx = level_transition_next_idx
                apply_level(levels[selected_level_idx])
                instantiate_level_enemies()
                player_pos = spawn_point
                player_vel_y = 0
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
                shoot_recoil = 0.0
                prev_on_ground = True
                is_invulnerable = False
                invuln_timer = 0.0
                camera_offset.x = player_pos.x - SCREEN_WIDTH // 2
                camera_offset.y = player_pos.y - SCREEN_HEIGHT // 2
                start_tutorial
                level_transition_phase = "fade_in"
                level_transition_timer = 0.0
                overlay_alpha = 255
        else:
            if LEVEL_TRANSITION_FADE_IN > 0:
                overlay_alpha = max(0, 255 - int((level_transition_timer / LEVEL_TRANSITION_FADE_IN) * 255))
            else:
                overlay_alpha = 0
            if level_transition_timer >= LEVEL_TRANSITION_FADE_IN:
                level_transition_active = False
                level_transition_next_idx = None
                level_transition_phase = "fade_out"
                level_transition_timer = 0.0
                overlay_alpha = 0
        if overlay_alpha > 0:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, overlay_alpha))
            screen.blit(overlay, (0, 0))

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
        level_transition_active = False
        level_transition_next_idx = None
        level_transition_phase = "fade_out"
        level_transition_timer = 0.0

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
        level_transition_active = False
        level_transition_next_idx = None
        level_transition_phase = "fade_out"
        level_transition_timer = 0.0

    draw_tutorial_overlay()
    pygame.display.flip()
    dt = clock.tick(FPS) / 1000

pygame.quit()
