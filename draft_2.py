import pygame
import sys
from pygame.math import Vector2

pygame.init()
pygame.display.set_caption("Tiny Town — Enter Buildings")
WIDTH, HEIGHT = 960, 640
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("consolas", 18)

# ---------- SETTINGS ----------
TILE_SIZE = 64
PLAYER_SPEED = 240
INTERACT_DISTANCE = 48

# Colors
BG_COLOR = (150, 200, 255)
GROUND_COLOR = (200, 230, 200)
BUILDING_COLOR = (120, 80, 40)
PLAYER_COLOR = (255, 100, 100)
NPC_COLOR = (100, 100, 255)
DIALOG_BG = (20, 20, 20)
DIALOG_TEXT = (230, 230, 230)
INTERIOR_COLOR = (230, 230, 180)

# ---------- TILE TYPES ----------
GROUND = 0
BUILDING = 1
NPC_SPAWN = 2
ENTRANCE = 3
EXIT = 4
ROAD = 5
TREE = 6
PARK = 7

# ---------- UTILITIES ----------
def clamp(value, mini, maxi):
    return max(mini, min(maxi, value))

def wrap_text(text, font, max_width):
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if font.size(test)[0] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

# ---------- TILE CLASS ----------
class Tile:
    def __init__(self, tile_type, rect):
        self.tile_type = tile_type
        self.rect = rect

# ---------- WORLD MAP ----------
# Create a larger 40x40 grid with various tile types
tile_map = [
    [GROUND, GROUND, GROUND, GROUND, ROAD, ROAD, GROUND, TREE, TREE, GROUND, BUILDING, BUILDING, GROUND, GROUND, GROUND, PARK, PARK, GROUND, GROUND, GROUND, NPC_SPAWN],
    [GROUND, GROUND, GROUND, ROAD, ROAD, ROAD, GROUND, GROUND, GROUND, GROUND, GROUND, BUILDING, BUILDING, GROUND, GROUND, PARK, PARK, GROUND, TREE, GROUND, NPC_SPAWN],
    [GROUND, GROUND, GROUND, ROAD, ROAD, ROAD, GROUND, GROUND, GROUND, GROUND, GROUND, GROUND, GROUND, GROUND, TREE, TREE, GROUND, GROUND, GROUND, GROUND, NPC_SPAWN],
    [GROUND, GROUND, GROUND, GROUND, GROUND, ROAD, GROUND, TREE, GROUND, GROUND, GROUND, ROAD, ROAD, GROUND, TREE, GROUND, GROUND, GROUND, GROUND, GROUND, GROUND],
    [GROUND, BUILDING, BUILDING, GROUND, GROUND, GROUND, TREE, GROUND, TREE, GROUND, ROAD, ROAD, BUILDING, GROUND, GROUND, GROUND, GROUND, GROUND, TREE, GROUND, EXIT],
    [GROUND, BUILDING, GROUND, GROUND, GROUND, TREE, ROAD, GROUND, GROUND, GROUND, ROAD,  TREE, NPC_SPAWN],
]

# ---------- TILE INITIALIZATION ----------
tiles = []
tile_width = TILE_SIZE
tile_height = TILE_SIZE

for row_idx, row in enumerate(tile_map):
    for col_idx, tile_type in enumerate(row):
        x = col_idx * tile_width
        y = row_idx * tile_height
        rect = pygame.Rect(x, y, tile_width, tile_height)
        tiles.append(Tile(tile_type, rect))

# ---------- PLAYER ----------
player = {"rect": pygame.Rect(60, 100, 36, 52), "vel": Vector2(0, 0), "name": "You"}
active_npc = None
dialog_open = False

# ---------- NPC SETUP ----------
npc_list = []

def add_npc(x, y, name, lines):
    npc = {
        "rect": pygame.Rect(x, y, 32, 48),
        "name": name,
        "lines": lines,
        "line_index": 0
    }
    npc_list.append(npc)

# Town NPCs
add_npc(120, 180, "Sam", ["Hey! Nice to see you.", "This town is pretty sleepy today."])
add_npc(300, 180, "Alex", ["Watch out for the park geese.", "They don't like being stepped on."])

# ---------- CAMERA ----------
def get_camera_offset(player_rect, w, h):
    cx = player_rect.centerx - WIDTH // 2
    cy = player_rect.centery - HEIGHT // 2
    cx = clamp(cx, 0, w - WIDTH)
    cy = clamp(cy, 0, h - HEIGHT)
    return Vector2(cx, cy)

# ---------- DRAW FUNCTIONS ----------
def draw_world():
    for tile in tiles:
        if tile.tile_type == GROUND:
            pygame.draw.rect(screen, GROUND_COLOR, tile.rect)
        elif tile.tile_type == BUILDING:
            pygame.draw.rect(screen, BUILDING_COLOR, tile.rect)
        elif tile.tile_type == NPC_SPAWN:
            pygame.draw.rect(screen, NPC_COLOR, tile.rect)
        elif tile.tile_type == ENTRANCE:
            pygame.draw.rect(screen, (255, 255, 0), tile.rect)
        elif tile.tile_type == EXIT:
            pygame.draw.rect(screen, (0, 255, 0), tile.rect)

def draw_dialog(surface, npc):
    box_h = 140
    margin = 10
    box_rect = pygame.Rect(30, HEIGHT - box_h - 30, WIDTH - 60, box_h)
    pygame.draw.rect(surface, DIALOG_BG, box_rect, border_radius=8)
    name_surf = FONT.render(npc["name"], True, (255, 210, 120))
    surface.blit(name_surf, (box_rect.x + margin, box_rect.y + margin))
    lines = wrap_text(npc["lines"][npc["line_index"]], FONT, box_rect.width - margin*2)
    for i, line in enumerate(lines):
        line_s = FONT.render(line, True, DIALOG_TEXT)
        surface.blit(line_s, (box_rect.x + margin, box_rect.y + margin + 24 + i * 22))
    hint = FONT.render("(Space to continue, E to close)", True, (180, 180, 180))
    surface.blit(hint, (box_rect.right - hint.get_width() - margin, box_rect.bottom - hint.get_height() - margin))

# ---------- MAIN LOOP ----------
running = True
while running:
    dt = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: running = False
            if event.key == pygame.K_e:
                if dialog_open:
                    dialog_open = False
                    active_npc = None
                else:
                    # Check for NPC interaction
                    for tile in tiles:
                        if tile.tile_type == NPC_SPAWN and tile.rect.colliderect(player["rect"]):
                            active_npc = npc_list[0]  # Using the first NPC as an example
                            dialog_open = True
                            break
                    # Check for entrance interaction
                    if not dialog_open:
                        for tile in tiles:
                            if tile.tile_type == ENTRANCE and tile.rect.colliderect(player["rect"]):
                                player["rect"].center = (WIDTH//2, HEIGHT - 80)
                                break
                    # Check for exit interaction
                    if not dialog_open:
                        for tile in tiles:
                            if tile.tile_type == EXIT and tile.rect.colliderect(player["rect"]):
                                player["rect"].center = (60, 100)  # Example for exit behavior
                                break
            elif event.key == pygame.K_SPACE:
                if dialog_open and active_npc is not None:
                    active_npc["line_index"] += 1
                    if active_npc["line_index"] >= len(active_npc["lines"]):
                        dialog_open = False
                        active_npc = None

    # Movement
    keys = pygame.key.get_pressed()
    move = Vector2(0, 0)
    if not dialog_open:
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: move.x = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: move.x = 1
        if keys[pygame.K_w] or keys[pygame.K_UP]: move.y = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: move.y = 1
        if move.length_squared() > 0:
            move = move.normalize() * PLAYER_SPEED * dt

    # Update player position
    player["rect"].x += int(move.x)
    player["rect"].y += int(move.y)

    # ---------- DRAW ----------
    screen.fill(BG_COLOR)
    draw_world()

    # Draw player
    pygame.draw.rect(screen, PLAYER_COLOR, player["rect"])

    if dialog_open and active_npc is not None:
        draw_dialog(screen, active_npc)

    pygame.display.flip()

pygame.quit()
sys.exit()
