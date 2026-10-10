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
BG_COLOR     = (26, 26, 46)
NET_COLOR    = (60, 60, 60)

# ===== PITCH DIMENSIONS =====
PITCH_W = 840
PITCH_H = 480
PITCH_X = (WIDTH  - PITCH_W) // 2
PITCH_Y = (HEIGHT - PITCH_H) // 2

PITCH_LEFT   = PITCH_X
PITCH_RIGHT  = PITCH_X + PITCH_W
PITCH_TOP    = PITCH_Y
PITCH_BOTTOM = PITCH_Y + PITCH_H

CX = WIDTH  // 2
CY = HEIGHT // 2

# Goal (net extends OUTWARD, away from pitch)
GOAL_HEIGHT = 68          # taller
GOAL_DEPTH  = 18          # how far the net extends outward
GOAL_TOP    = CY - GOAL_HEIGHT // 2
GOAL_BOTTOM = CY + GOAL_HEIGHT // 2

# Penalty box
PENALTY_W = 160
PENALTY_H = 280
PENALTY_TOP    = CY - PENALTY_H // 2
PENALTY_BOTTOM = CY + PENALTY_H // 2

# Goal area (6-yard box)
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
CORNER_RADIUS = 14

# Grass stripes
STRIPE_COUNT = 12
STRIPE_WIDTH = PITCH_W / STRIPE_COUNT


# ===== DRAW HELPERS =====
def draw_striped_grass():
    for i in range(STRIPE_COUNT):
        x = PITCH_LEFT + i * STRIPE_WIDTH
        color = GRASS_LIGHT if i % 2 == 0 else GRASS_DARK
        pygame.draw.rect(screen, color,
                         (x, PITCH_TOP, STRIPE_WIDTH + 1, PITCH_H))


def draw_outline():
    pygame.draw.rect(screen, LINE_WHITE,
                     (PITCH_LEFT, PITCH_TOP, PITCH_W, PITCH_H), 3)


def draw_halfway_line():
    pygame.draw.line(screen, LINE_WHITE,
                     (CX, PITCH_TOP), (CX, PITCH_BOTTOM), 3)


def draw_center_circle():
    pygame.draw.circle(screen, LINE_WHITE, (CX, CY), CENTER_RADIUS, 3)
    pygame.draw.circle(screen, LINE_WHITE, (CX, CY), 4)


def draw_penalty_boxes():
    pygame.draw.rect(screen, LINE_WHITE,
                     (PITCH_LEFT, PENALTY_TOP, PENALTY_W, PENALTY_H), 3)
    pygame.draw.rect(screen, LINE_WHITE,
                     (PITCH_RIGHT - PENALTY_W, PENALTY_TOP, PENALTY_W, PENALTY_H), 3)


def draw_goal_areas():
    pygame.draw.rect(screen, LINE_WHITE,
                     (PITCH_LEFT, GOAL_AREA_TOP, GOAL_AREA_W, GOAL_AREA_H), 3)
    pygame.draw.rect(screen, LINE_WHITE,
                     (PITCH_RIGHT - GOAL_AREA_W, GOAL_AREA_TOP, GOAL_AREA_W, GOAL_AREA_H), 3)


def draw_penalty_spots():
    left_spot_x  = PITCH_LEFT + PENALTY_DIST
    right_spot_x = PITCH_RIGHT - PENALTY_DIST
    pygame.draw.circle(screen, LINE_WHITE, (left_spot_x, CY), 4)
    pygame.draw.circle(screen, LINE_WHITE, (right_spot_x, CY), 4)


def draw_penalty_arcs():
    """
    Draw the arcs that bulge OUT from the penalty box.
    Left: arc opens to the RIGHT (toward midfield)
    Right: arc opens to the LEFT (toward midfield)
    """
    arc_thickness = 3

    # LEFT penalty arc — bulges into midfield (right side of the box)
    left_arc_center = (PITCH_LEFT + PENALTY_DIST, CY)
    left_rect = pygame.Rect(
        left_arc_center[0] - PENALTY_ARC_RADIUS,
        left_arc_center[1] - PENALTY_ARC_RADIUS,
        PENALTY_ARC_RADIUS * 2,
        PENALTY_ARC_RADIUS * 2
    )
    # Angles: -60° to +60° (in radians) → bulges right
    pygame.draw.arc(screen, LINE_WHITE, left_rect,
                    -1.0472, 1.0472, arc_thickness)

    # RIGHT penalty arc — bulges into midfield (left side of the box)
    right_arc_center = (PITCH_RIGHT - PENALTY_DIST, CY)
    right_rect = pygame.Rect(
        right_arc_center[0] - PENALTY_ARC_RADIUS,
        right_arc_center[1] - PENALTY_ARC_RADIUS,
        PENALTY_ARC_RADIUS * 2,
        PENALTY_ARC_RADIUS * 2
    )
    # Angles: 120° to 240° (in radians) → bulges left
    pygame.draw.arc(screen, LINE_WHITE, right_rect,
                    2.0944, 4.1888, arc_thickness)


def draw_corner_arcs():
    """Four corner quarter-circles with thinner lines."""
    thickness = 2

    # Top-left
    pygame.draw.arc(screen, LINE_WHITE,
                    (PITCH_LEFT, PITCH_TOP,
                     CORNER_RADIUS * 2, CORNER_RADIUS * 2),
                    0, 1.5708, thickness)

    # Top-right
    pygame.draw.arc(screen, LINE_WHITE,
                    (PITCH_RIGHT - CORNER_RADIUS * 2, PITCH_TOP,
                     CORNER_RADIUS * 2, CORNER_RADIUS * 2),
                    1.5708, 3.1416, thickness)

    # Bottom-left
    pygame.draw.arc(screen, LINE_WHITE,
                    (PITCH_LEFT, PITCH_BOTTOM - CORNER_RADIUS * 2,
                     CORNER_RADIUS * 2, CORNER_RADIUS * 2),
                    4.7124, 6.2832, thickness)

    # Bottom-right
    pygame.draw.arc(screen, LINE_WHITE,
                    (PITCH_RIGHT - CORNER_RADIUS * 2, PITCH_BOTTOM - CORNER_RADIUS * 2,
                     CORNER_RADIUS * 2, CORNER_RADIUS * 2),
                    3.1416, 4.7124, thickness)


def draw_goal(side):
    """Draw a goal with proper depth and a grid net."""
    if side == "left":
        # Net extends to the LEFT (away from pitch)
        gx = PITCH_LEFT - GOAL_DEPTH
    else:
        # Net extends to the RIGHT (away from pitch)
        gx = PITCH_RIGHT

    gy = GOAL_TOP
    gw = GOAL_DEPTH
    gh = GOAL_HEIGHT

    # Net background (dark)
    pygame.draw.rect(screen, NET_COLOR, (gx, gy, gw, gh))

    # Net grid lines
    step = 6
    for i in range(gx, gx + gw + 1, step):
        pygame.draw.line(screen, (120, 120, 120), (i, gy), (i, gy + gh), 1)
    for j in range(gy, gy + gh + 1, step):
        pygame.draw.line(screen, (120, 120, 120), (gx, j), (gx + gw, j), 1)

    # Goal frame (thick white outline)
    pygame.draw.rect(screen, LINE_WHITE, (gx, gy, gw, gh), 3)


def draw_pitch():
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


# ===== MAIN LOOP =====
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
