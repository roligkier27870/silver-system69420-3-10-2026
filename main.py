import pygame
import asyncio
import math

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
NET_GRID     = (120, 120, 120)

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

# Goal
GOAL_HEIGHT = 68
GOAL_DEPTH  = 18
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
PENALTY_ARC_RADIUS = 88

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


def draw_arc_segment(cx, cy, radius, start_angle, end_angle, color, thickness):
    """Draw a clean arc segment (Y-down screen coords)."""
    prev = None
    steps = 40
    for i in range(steps + 1):
        a = start_angle + (end_angle - start_angle) * (i / steps)
        x = cx + radius * math.cos(a)
        y = cy + radius * math.sin(a)
        if prev is not None:
            pygame.draw.line(screen, color, prev, (x, y), thickness)
        prev = (x, y)


def draw_arc_outside_box(center_x, center_y, radius, start_angle, end_angle,
                          color, thickness, hide_left_of=None, hide_right_of=None):
    """Draw an arc as line segments, skipping segments inside the hidden region."""
    prev_point = None
    steps = 80
    for i in range(steps + 1):
        angle = start_angle + (end_angle - start_angle) * (i / steps)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)

        hide = False
        if hide_left_of is not None and x < hide_left_of:
            hide = True
        if hide_right_of is not None and x > hide_right_of:
            hide = True

        if hide:
            prev_point = None
            continue

        if prev_point is not None:
            pygame.draw.line(screen, color, prev_point, (x, y), thickness)
        prev_point = (x, y)


def draw_penalty_arcs():
    arc_radius = PENALTY_ARC_RADIUS
    thickness = 3
    box_edge_left  = PITCH_LEFT + PENALTY_W
    box_edge_right = PITCH_RIGHT - PENALTY_W

    # LEFT penalty arc
    draw_arc_outside_box(
        PITCH_LEFT + PENALTY_DIST, CY,
        arc_radius,
        -math.pi / 2, math.pi / 2,
        LINE_WHITE, thickness,
        hide_left_of=box_edge_left
    )

    # RIGHT penalty arc
    draw_arc_outside_box(
        PITCH_RIGHT - PENALTY_DIST, CY,
        arc_radius,
        math.pi / 2, 3 * math.pi / 2,
        LINE_WHITE, thickness,
        hide_right_of=box_edge_right
    )


def draw_corner_arcs():
    """Four corner quarter-circles drawn as clean segments."""
    thickness = 2
    r = CORNER_RADIUS

    # TOP-LEFT: arc from top edge to left edge
    draw_arc_segment(PITCH_LEFT, PITCH_TOP, r, 0, math.pi / 2, LINE_WHITE, thickness)

    # TOP-RIGHT: arc from right edge to top edge
    draw_arc_segment(PITCH_RIGHT, PITCH_TOP, r, math.pi / 2, math.pi, LINE_WHITE, thickness)

    # BOTTOM-LEFT: arc from left edge to bottom edge
    draw_arc_segment(PITCH_LEFT, PITCH_BOTTOM, r, -math.pi / 2, 0, LINE_WHITE, thickness)

    # BOTTOM-RIGHT: arc from bottom edge to right edge
    draw_arc_segment(PITCH_RIGHT, PITCH_BOTTOM, r, math.pi, 3 * math.pi / 2, LINE_WHITE, thickness)


def draw_goal(side):
    if side == "left":
        gx = PITCH_LEFT - GOAL_DEPTH
    else:
        gx = PITCH_RIGHT

    gy = GOAL_TOP
    gw = GOAL_DEPTH
    gh = GOAL_HEIGHT

    pygame.draw.rect(screen, NET_COLOR, (gx, gy, gw, gh))

    step = 6
    for i in range(gx, gx + gw + 1, step):
        pygame.draw.line(screen, NET_GRID, (i, gy), (i, gy + gh), 1)
    for j in range(gy, gy + gh + 1, step):
        pygame.draw.line(screen, NET_GRID, (gx, j), (gx + gw, j), 1)

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
