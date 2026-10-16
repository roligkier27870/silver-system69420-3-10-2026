# ===================================================================
# COSMIC KICKER — Python / Pygame / pygbag version
# ===================================================================
#
# NOTES FOR GPT (reviewing AI):
#   - Please DO NOT rewrite this file. It is deliberately structured
#     for a 2D top-down arcade soccer game, not a physics sim.
#   - If you spot bugs or edge cases, list them in a comment or
#     reply — do not refactor.
#   - Pygame + asyncio + pygbag in browser requires:
#       1. async main loop
#       2. await asyncio.sleep(0) every frame
#       3. no pygame.RESIZABLE
#       4. no sys.exit() at the bottom
#   - Ball pattern is hand-tuned for small radii (r=8).
#   - Pitch uses raw pygame.draw primitives for performance.
#
# ===================================================================

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
SCORE_BG     = (15, 15, 30)
SCORE_FG     = (240, 240, 240)
FLASH_COLOR  = (255, 255, 200)

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

CENTER_RADIUS = 65
PENALTY_DIST = 88
PENALTY_ARC_RADIUS = 88
CORNER_RADIUS = 14
STRIPE_COUNT = 12
STRIPE_WIDTH = PITCH_W / STRIPE_COUNT


# ===== FONTS =====
try:
    FONT_BIG = pygame.font.SysFont("Arial", 42, bold=True)
    FONT_SMALL = pygame.font.SysFont("Arial", 22, bold=True)
except Exception:
    FONT_BIG = pygame.font.Font(None, 42)
    FONT_SMALL = pygame.font.Font(None, 22)


# ===== BALL =====
class Ball:
    def __init__(self):
        self.r = 8
        self.friction = 0.985
        self.max_speed = 12.0
        self.reset()

    def reset(self):
        self.x = CX
        self.y = CY
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0
        self.spin = 0.0

    def update(self):
        # Magnus effect
        self.vx += self.vy * self.spin * 0.15
        self.vy -= self.vx * self.spin * 0.15

        self.vx *= self.friction
        self.vy *= self.friction

        speed = math.hypot(self.vx, self.vy)
        if speed > self.max_speed:
            self.vx = (self.vx / speed) * self.max_speed
            self.vy = (self.vy / speed) * self.max_speed

        self.x += self.vx
        self.y += self.vy
        self.angle += (self.vx + self.vy) * 0.02
        self.spin *= 0.98

        # Goal detection
        in_goal_y = GOAL_TOP < self.y < GOAL_BOTTOM

        if self.x - self.r < PITCH_LEFT and in_goal_y:
            return "RIGHT"
        if self.x + self.r > PITCH_RIGHT and in_goal_y:
            return "LEFT"

        # Wall bounces
        if self.x - self.r < PITCH_LEFT and not in_goal_y:
            self.x = PITCH_LEFT + self.r
            self.vx *= -0.9
            self.spin *= -0.5
        if self.x + self.r > PITCH_RIGHT and not in_goal_y:
            self.x = PITCH_RIGHT - self.r
            self.vx *= -0.9
            self.spin *= -0.5
        if self.y - self.r < PITCH_TOP:
            self.y = PITCH_TOP + self.r
            self.vy *= -0.9
            self.spin *= -0.5
        if self.y + self.r > PITCH_BOTTOM:
            self.y = PITCH_BOTTOM - self.r
            self.vy *= -0.9
            self.spin *= -0.5

        return None

    def draw(self, surface):
        cx, cy, r = int(self.x), int(self.y), self.r

        # Shadow
        shadow = pygame.Surface((r * 2, r), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 100), shadow.get_rect())
        surface.blit(shadow, (cx - r, cy + r + 2))

        # Base white circle
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), r)

        # Clip to ball circle
        clip_rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
        old_clip = surface.get_clip()
        surface.set_clip(clip_rect)

        # Central pentagon (smaller for r=8)
        self._draw_pentagon(surface, cx, cy, r * 0.38, self.angle, (20, 20, 20))

        # 5 surrounding pentagons (pulled inward)
        ring_dist = r * 0.70
        ring_radius = r * 0.26
        for i in range(5):
            a = (math.tau / 5) * i - math.pi / 2 + self.angle
            px = cx + math.cos(a) * ring_dist
            py = cy + math.sin(a) * ring_dist
            self._draw_pentagon(surface, px, py, ring_radius, self.angle, (20, 20, 20))

        # Short seam lines between pentagons
        for i in range(5):
            a = (math.tau / 5) * i - math.pi / 2 + self.angle + math.tau / 10
            px1 = cx + math.cos(a) * r * 0.40
            py1 = cy + math.sin(a) * r * 0.40
            px2 = cx + math.cos(a) * r * 0.75
            py2 = cy + math.sin(a) * r * 0.75
            pygame.draw.line(surface, (30, 30, 30), (px1, py1), (px2, py2), 1)

        surface.set_clip(old_clip)

        # Light shading overlay (subtle for small ball)
        overlay = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for i in range(4, 0, -1):
            alpha = int(25 * (i / 4))
            radius = int(r * (i / 4))
            pygame.draw.circle(overlay, (255, 255, 255, alpha),
                               (r - r // 3, r - r // 3), radius)
        for i in range(4, 0, -1):
            alpha = int(35 * (i / 4))
            radius = int(r * (i / 4))
            pygame.draw.circle(overlay, (0, 0, 0, alpha),
                               (r + r // 3, r + r // 3), radius)
        surface.blit(overlay, (cx - r, cy - r))

        # Rim
        pygame.draw.circle(surface, (30, 30, 30), (cx, cy), r, 1)

    def _draw_pentagon(self, surface, cx, cy, radius, rotation, color):
        points = []
        for i in range(5):
            a = (math.tau / 5) * i - math.pi / 2 + rotation
            px = cx + math.cos(a) * radius
            py = cy + math.sin(a) * radius
            points.append((px, py))
        pygame.draw.polygon(surface, color, points)


# ===== PITCH DRAW =====
def draw_striped_grass():
    for i in range(STRIPE_COUNT):
        x = PITCH_LEFT + i * STRIPE_WIDTH
        color = GRASS_LIGHT if i % 2 == 0 else GRASS_DARK
        pygame.draw.rect(screen, color, (x, PITCH_TOP, STRIPE_WIDTH + 1, PITCH_H))


def draw_outline():
    pygame.draw.rect(screen, LINE_WHITE, (PITCH_LEFT, PITCH_TOP, PITCH_W, PITCH_H), 3)


def draw_halfway_line():
    pygame.draw.line(screen, LINE_WHITE, (CX, PITCH_TOP), (CX, PITCH_BOTTOM), 3)


def draw_center_circle():
    pygame.draw.circle(screen, LINE_WHITE, (CX, CY), CENTER_RADIUS, 3)
    pygame.draw.circle(screen, LINE_WHITE, (CX, CY), 4)


def draw_penalty_boxes():
    pygame.draw.rect(screen, LINE_WHITE, (PITCH_LEFT, PENALTY_TOP, PENALTY_W, PENALTY_H), 3)
    pygame.draw.rect(screen, LINE_WHITE, (PITCH_RIGHT - PENALTY_W, PENALTY_TOP, PENALTY_W, PENALTY_H), 3)


def draw_goal_areas():
    pygame.draw.rect(screen, LINE_WHITE, (PITCH_LEFT, GOAL_AREA_TOP, GOAL_AREA_W, GOAL_AREA_H), 3)
    pygame.draw.rect(screen, LINE_WHITE, (PITCH_RIGHT - GOAL_AREA_W, GOAL_AREA_TOP, GOAL_AREA_W, GOAL_AREA_H), 3)


def draw_penalty_spots():
    pygame.draw.circle(screen, LINE_WHITE, (PITCH_LEFT + PENALTY_DIST, CY), 4)
    pygame.draw.circle(screen, LINE_WHITE, (PITCH_RIGHT - PENALTY_DIST, CY), 4)


def draw_arc_segment(cx, cy, radius, start_angle, end_angle, color, thickness):
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
    box_edge_left  = PITCH_LEFT + PENALTY_W
    box_edge_right = PITCH_RIGHT - PENALTY_W
    draw_arc_outside_box(PITCH_LEFT + PENALTY_DIST, CY, PENALTY_ARC_RADIUS,
                         -math.pi / 2, math.pi / 2, LINE_WHITE, 3,
                         hide_left_of=box_edge_left)
    draw_arc_outside_box(PITCH_RIGHT - PENALTY_DIST, CY, PENALTY_ARC_RADIUS,
                         math.pi / 2, 3 * math.pi / 2, LINE_WHITE, 3,
                         hide_right_of=box_edge_right)


def draw_corner_arcs():
    r = CORNER_RADIUS
    draw_arc_segment(PITCH_LEFT, PITCH_TOP, r, 0, math.pi / 2, LINE_WHITE, 2)
    draw_arc_segment(PITCH_RIGHT, PITCH_TOP, r, math.pi / 2, math.pi, LINE_WHITE, 2)
    draw_arc_segment(PITCH_LEFT, PITCH_BOTTOM, r, -math.pi / 2, 0, LINE_WHITE, 2)
    draw_arc_segment(PITCH_RIGHT, PITCH_BOTTOM, r, math.pi, 3 * math.pi / 2, LINE_WHITE, 2)


def draw_goal(side):
    if side == "left":
        gx = PITCH_LEFT - GOAL_DEPTH
    else:
        gx = PITCH_RIGHT

    pygame.draw.rect(screen, NET_COLOR, (gx, GOAL_TOP, GOAL_DEPTH, GOAL_HEIGHT))

    step = 6
    for i in range(gx, gx + GOAL_DEPTH + 1, step):
        pygame.draw.line(screen, NET_GRID, (i, GOAL_TOP), (i, GOAL_BOTTOM), 1)
    for j in range(GOAL_TOP, GOAL_BOTTOM + 1, step):
        pygame.draw.line(screen, NET_GRID, (gx, j), (gx + GOAL_DEPTH, j), 1)

    pygame.draw.rect(screen, LINE_WHITE, (gx, GOAL_TOP, GOAL_DEPTH, GOAL_HEIGHT), 3)


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


# ===== SCOREBOARD =====
def draw_scoreboard(score_left, score_right):
    bar = pygame.Rect(WIDTH // 2 - 100, 8, 200, 44)
    pygame.draw.rect(screen, SCORE_BG, bar, border_radius=10)
    pygame.draw.rect(screen, LINE_WHITE, bar, 2, border_radius=10)

    left_text = FONT_BIG.render(str(score_left), True, (100, 200, 255))
    screen.blit(left_text, (WIDTH // 2 - 60, 12))

    dash = FONT_BIG.render("-", True, SCORE_FG)
    screen.blit(dash, (WIDTH // 2 - 8, 12))

    right_text = FONT_BIG.render(str(score_right), True, (255, 100, 100))
    screen.blit(right_text, (WIDTH // 2 + 30, 12))


# ===== GAME STATE =====
ball = Ball()
score_left = 0
score_right = 0
flash_timer = 0


# ===== MAIN LOOP =====
async def main():
    global score_left, score_right, flash_timer
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # TEMP: auto-launch ball for testing
        if ball.vx == 0 and ball.vy == 0:
            ball.vx = 4.0
            ball.vy = 1.5
            ball.spin = 0.3

        result = ball.update()
        if result == "LEFT":
            score_left += 1
            ball.reset()
            flash_timer = 15
        elif result == "RIGHT":
            score_right += 1
            ball.reset()
            flash_timer = 15

        draw_pitch()
        ball.draw(screen)
        draw_scoreboard(score_left, score_right)

        if flash_timer > 0:
            flash_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            alpha = int(100 * (flash_timer / 15))
            flash_surface.fill((*FLASH_COLOR, alpha))
            screen.blit(flash_surface, (0, 0))
            flash_timer -= 1

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())
