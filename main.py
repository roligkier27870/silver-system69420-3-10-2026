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


# ===== BALL =====
class Ball:
    def __init__(self):
        self.x = CX
        self.y = CY
        self.r = 12
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0
        self.friction = 0.985
        self.max_speed = 12.0
        self.spin = 0.0

        # Icosahedral pentagon centers (normalized)
        phi = (1 + math.sqrt(5)) / 2
        raw = [
            (0,  1,  phi), (0, -1,  phi), (0,  1, -phi), (0, -1, -phi),
            (1,  phi, 0), (-1,  phi, 0), (1, -phi, 0), (-1, -phi, 0),
            (phi, 0,  1), (phi, 0, -1), (-phi, 0,  1), (-phi, 0, -1),
        ]
        self.pentagon_dirs = []
        for v in raw:
            mag = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
            self.pentagon_dirs.append((v[0]/mag, v[1]/mag, v[2]/mag))

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

        in_goal_y_range = abs(self.y - CY) < GOAL_HEIGHT / 2

        if self.x - self.r < PITCH_LEFT and not in_goal_y_range:
            self.x = PITCH_LEFT + self.r
            self.vx *= -0.9
            self.spin *= -0.5
        if self.x + self.r > PITCH_RIGHT and not in_goal_y_range:
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

    def draw(self, surface):
        cx, cy, r = self.x, self.y, self.r

        # Shadow
        shadow = pygame.Surface((r * 2, r), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
        surface.blit(shadow, (cx - r, cy + r + 3))

        # Base white circle
        pygame.draw.circle(surface, (255, 255, 255), (int(cx), int(cy)), r)

        # Rotate pentagon dirs around Z
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)

        visible_pentagons = []
        for px, py, pz in self.pentagon_dirs:
            rx = px * cos_a - py * sin_a
            ry = px * sin_a + py * cos_a
            rz = pz
            if rz > 0.1:
                sx = cx + rx * r
                sy = cy + ry * r
                visible_pentagons.append((sx, sy, rz, rz))

        visible_pentagons.sort(key=lambda p: p[3])

        for sx, sy, scale, rz in visible_pentagons:
            self._draw_projected_pentagon(surface, sx, sy, scale)

        # Seams
        for px, py, pz in self.pentagon_dirs:
            rx = px * cos_a - py * sin_a
            ry = px * sin_a + py * cos_a
            rz = pz
            if rz < -0.2:
                continue
            sx = self.x + rx * self.r
            sy = self.y + ry * self.r
            radius = self.r * 0.40 * max(rz, 0.3)
            pygame.draw.circle(surface, (60, 60, 60),
                               (int(sx), int(sy)), int(radius), 1)

        # Shading overlay
        overlay = pygame.Surface((self.r * 2, self.r * 2), pygame.SRCALPHA)
        for i in range(6, 0, -1):
            alpha = int(20 * (i / 6))
            radius = int(self.r * (i / 6))
            pygame.draw.circle(overlay, (255, 255, 255, alpha),
                               (self.r - self.r // 3, self.r - self.r // 3), radius)
        for i in range(6, 0, -1):
            alpha = int(30 * (i / 6))
            radius = int(self.r * (i / 6))
            pygame.draw.circle(overlay, (0, 0, 0, alpha),
                               (self.r + self.r // 3, self.r + self.r // 3), radius)
        surface.blit(overlay, (self.x - self.r, self.y - self.r))

        # Rim
        pygame.draw.circle(surface, (40, 40, 40), (int(cx), int(cy)), r, 1)

    def _draw_projected_pentagon(self, surface, sx, sy, scale):
        radius = self.r * 0.32 * scale
        points = []
        for i in range(5):
            a = (math.tau / 5) * i - math.pi / 2
            px = sx + math.cos(a) * radius
            py = sy + math.sin(a) * radius
            points.append((px, py))
        pygame.draw.polygon(surface, (20, 20, 20), points)


# ===== PITCH DRAW =====
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
    arc_radius = PENALTY_ARC_RADIUS
    thickness = 3
    box_edge_left  = PITCH_LEFT + PENALTY_W
    box_edge_right = PITCH_RIGHT - PENALTY_W

    draw_arc_outside_box(
        PITCH_LEFT + PENALTY_DIST, CY,
        arc_radius,
        -math.pi / 2, math.pi / 2,
        LINE_WHITE, thickness,
        hide_left_of=box_edge_left
    )

    draw_arc_outside_box(
        PITCH_RIGHT - PENALTY_DIST, CY,
        arc_radius,
        math.pi / 2, 3 * math.pi / 2,
        LINE_WHITE, thickness,
        hide_right_of=box_edge_right
    )


def draw_corner_arcs():
    thickness = 2
    r = CORNER_RADIUS

    draw_arc_segment(PITCH_LEFT, PITCH_TOP, r, 0, math.pi / 2, LINE_WHITE, thickness)
    draw_arc_segment(PITCH_RIGHT, PITCH_TOP, r, math.pi / 2, math.pi, LINE_WHITE, thickness)
    draw_arc_segment(PITCH_LEFT, PITCH_BOTTOM, r, -math.pi / 2, 0, LINE_WHITE, thickness)
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


# ===== INSTANTIATE =====
ball = Ball()


# ===== MAIN LOOP =====
async def main():
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

        ball.update()

        draw_pitch()
        ball.draw(screen)
        pygame.display.flip()

        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())
