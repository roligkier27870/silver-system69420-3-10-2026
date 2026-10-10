import pygame
import asyncio

# ===== SETUP =====
pygame.init()
WIDTH, HEIGHT = 960, 540
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cosmic Kicker")
clock = pygame.time.Clock()

# ===== COLORS =====
GRASS_LIGHT  = (56, 142, 60)
GRASS_DARK   = (46, 125, 50)
LINE_WHITE   = (240, 240, 240)
OUTLINE      = (200, 200, 200)
BG_COLOR     = (26, 26, 46)
NET_COLOR    = (180, 180, 180)

# ===== PITCH DIMENSIONS (better proportions) =====
PITCH_W = 840
PITCH_H = 480
PITCH_X = (WIDTH  - PITCH_W) // 2   # 60
PITCH_Y = (HEIGHT - PITCH_H) // 2   # 30

PITCH_LEFT   = PITCH_X
PITCH_RIGHT  = PITCH_X + PITCH_W
PITCH_TOP    = PITCH_Y
PITCH_BOTTOM = PITCH_Y + PITCH_H

CX = WIDTH  // 2
CY = HEIGHT // 2

# Goal
GOAL_HEIGHT = 58
GOAL_WIDTH  = 12
GOAL_TOP    = CY - GOAL_HEIGHT // 2
GOAL_BOTTOM = CY + GOAL_HEIGHT // 2

# Penalty box
PENALTY_W = 160
PENALTY_H = 280
PENALTY_TOP    = CY - PENALTY_H // 2
PENALTY_BOTTOM = CY + PENALTY_H // 2

# Goal area
GOAL_AREA_W = 73
GOAL_AREA_H = 140
GOAL_AREA_TOP    = CY - GOAL_AREA_H // 2
GOAL_AREA_BOTTOM = CY + GOAL_AREA_H // 2

# Center circle
CENTER_RADIUS = 65

# Penalty spot
PENALTY_DIST = 88
PENALTY_ARC_RADIUS = 65

# Corner arc
CORNER_RADIUS = 10

# Grass stripes
STRIPE_COUNT = 12
STRIPE_WIDTH = PITCH_W / STRIPE_COUNT


# ===== DRAW HELPERS =====
def draw_striped_grass():
    """Draw the pitch with vertical mowed stripes."""
    for i in range(STRIPE_COUNT):
        x = PITCH_LEFT + i * STRIPE_WIDTH
        color = GRASS_LIGHT if i % 2 == 0 else GRASS_DARK
        pygame.draw.rect(screen, color,
                         (x, PITCH_TOP, STRIPE_WIDTH + 1, PITCH_H))


def draw_outline():
    """Outer boundary rectangle."""
    pygame.draw.rect(screen, LINE_WHITE,
                     (PITCH_LEFT, PITCH_TOP, PITCH_W, PITCH_H), 3)


def draw_halfway_line():
    """Vertical halfway line."""
    pygame.draw.line(screen, LINE_WHITE,
                     (CX, PITCH_TOP), (CX, PITCH_BOTTOM), 3)


def draw_center_circle():
    """Center circle + center spot."""
    pygame.draw.circle(screen, LINE_WHITE, (CX, CY), CENTER_RADIUS, 3)
    pygame.draw.circle(screen, LINE_WHITE, (CX, CY), 4)


def draw_penalty_boxes():
    """Left and right penalty boxes."""
    # Left
    pygame.draw.rect(screen, LINE_WHITE,
                     (PITCH_LEFT, PENALTY_TOP, PENALTY_W, PENALTY_H), 3)
    # Right
    pygame.draw.rect(screen, LINE_WHITE,
                     (PITCH_RIGHT - PENALTY_W, PENALTY_TOP, PENALTY_W, PENALTY_H), 3)


def draw_goal_areas():
    """Small goal areas (6-yard boxes)."""
    # Left
    pygame.draw.rect(screen, LINE_WHITE,
                     (PITCH_LEFT, GOAL_AREA_TOP, GOAL_AREA_W, GOAL_AREA_H), 3)
    # Right
    pygame.draw.rect(screen, LINE_WHITE,
                     (PITCH_RIGHT - GOAL_AREA_W, GOAL_AREA_TOP, GOAL_AREA_W, GOAL_AREA_H), 3)


def draw_penalty_spots():
    """Penalty spots on both sides."""
    left_spot_x  = PITCH_LEFT + PENALTY_DIST
    right_spot_x = PITCH_RIGHT - PENALTY_DIST
    pygame.draw.circle(screen, LINE_WHITE, (left_spot_x, CY), 4)
    pygame.draw.circle(screen, LINE_WHITE, (right_spot_x, CY), 4)


def draw_penalty_arcs():
    """Semicircular arcs at the top of each penalty box."""
    # Left penalty arc — only the part outside the box
    arc_center_left = (PITCH_LEFT + PENALTY_DIST, CY)
    pygame.draw.arc(screen, LINE_WHITE,
                    (arc_center_left[0] - PENALTY_ARC_RADIUS,
                     arc_center_left[1] - PENALTY_ARC_RADIUS,
                     PENALTY_ARC_RADIUS * 2,
                     PENALTY_ARC_RADIUS * 2),
                    -1.0, 1.0, 3)  # radians (roughly right side)

    # Right penalty arc
    arc_center_right = (PITCH_RIGHT - PENALTY_DIST, CY)
    pygame.draw.arc(screen, LINE_WHITE,
                    (arc_center_right[0] - PENALTY_ARC_RADIUS,
                     arc_center_right[1] - PENALTY_ARC_RADIUS,
                     PENALTY_ARC_RADIUS * 2,
                     PENALTY_ARC_RADIUS * 2),
                    2.14, 4.14, 3)  # radians (roughly left side)


def draw_corner_arcs():
    """Four corner quarter-circles."""
    # Top-left
    pygame.draw.arc(screen, LINE_WHITE,
                    (PITCH_LEFT, PITCH_TOP, CORNER_RADIUS * 2, CORNER_RADIUS * 2),
                    0, 1.5708, 3)
    # Top-right
    pygame.draw.arc(screen, LINE_WHITE,
                    (PITCH_RIGHT - CORNER_RADIUS * 2, PITCH_TOP,
                     CORNER_RADIUS * 2, CORNER_RADIUS * 2),
                    1.5708, 3.1416, 3)
    # Bottom-left
    pygame.draw.arc(screen, LINE_WHITE,
                    (PITCH_LEFT, PITCH_BOTTOM - CORNER_RADIUS * 2,
                     CORNER_RADIUS * 2, CORNER_RADIUS * 2),
                    4.7124, 6.2832, 3)
    # Bottom-right
    pygame.draw.arc(screen, LINE_WHITE,
                    (PITCH_RIGHT - CORNER_RADIUS * 2, PITCH_BOTTOM - CORNER_RADIUS * 2,
                     CORNER_RADIUS * 2, CORNER_RADIUS * 2),
                    3.1416, 4.7124, 3)


def draw_goal(side):
    """Draw a goal with a net."""
    if side == "left":
        gx = PITCH_LEFT - GOAL_WIDTH
    else:
        gx = PITCH_RIGHT

    gy = GOAL_TOP
    gw = GOAL_WIDTH
    gh = GOAL_HEIGHT

    # Net background
    pygame.draw.rect(screen, NET_COLOR, (gx, gy, gw, gh))

    # Net lines (grid)
    step = 6
    for i in range(gx, gx + gw + 1, step):
        pygame.draw.line(screen, LINE_WHITE, (i, gy), (i, gy + gh), 1)
    for j in range(gy, gy + gh + 1, step):
        pygame.draw.line(screen, LINE_WHITE, (gx, j), (gx + gw, j), 1)

    # Goal frame
    pygame.draw.rect(screen, LINE_WHITE, (gx, gy, gw, gh), 3)


def draw_pitch():
    """Draw the entire pitch."""
    screen.fill(BG_COLOR)

    draw_striped_grass()
    draw_outline()
    draw_halfway_line()
    draw_center_circle()
    draw_penalty_boxes()
    draw_goal_areas()
    draw_penalty_spots()
    draw_penalty_arcs()
    draw_corner_arcs()
    draw_goal("left")
    draw_goal("right")


# ===== MAIN LOOP (async for pygbag) =====
async def main():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        draw_pitch()
        pygame.display.flip()

        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())
