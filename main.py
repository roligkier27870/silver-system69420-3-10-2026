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

        # --- Icosahedral pentagon centers (unit sphere coords) ---
        # Standard 12 vertices of an icosahedron, then we use them as
        # pentagon centers on the sphere.
        phi = (1 + math.sqrt(5)) / 2
        raw = [
            (0,  1,  phi), (0, -1,  phi), (0,  1, -phi), (0, -1, -phi),
            (1,  phi, 0), (-1,  phi, 0), (1, -phi, 0), (-1, -phi, 0),
            (phi, 0,  1), (phi, 0, -1), (-phi, 0,  1), (-phi, 0, -1),
        ]
        # Normalize each to unit length
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

        # Rotate ball visually based on movement (in screen plane)
        self.angle += (self.vx + self.vy) * 0.02
        self.spin *= 0.98

        # Wall bounces
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

        # --- Shadow ---
        shadow = pygame.Surface((r * 2, r), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
        surface.blit(shadow, (cx - r, cy + r + 3))

        # --- Base white circle ---
        pygame.draw.circle(surface, (255, 255, 255), (int(cx), int(cy)), r)

        # --- Rotate pentagon directions by ball.angle around Z axis ---
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)

        visible_pentagons = []
        for px, py, pz in self.pentagon_dirs:
            # rotate around Z axis
            rx = px * cos_a - py * sin_a
            ry = px * sin_a + py * cos_a
            rz = pz

            # Only draw pentagons on the visible hemisphere
            # (in view space, camera looks down -Z... but here we fake top-down)
            # Treat rz as "depth". Positive rz = facing camera.
            if rz > 0.1:
                # Project to 2D
                sx = cx + rx * r
                sy = cy + ry * r
                # Scale radius by rz (foreshortening)
                scale = rz
                visible_pentagons.append((sx, sy, scale, rz))

        # Sort so front-most pentagons are drawn last
        visible_pentagons.sort(key=lambda p: p[3])

        for sx, sy, scale, rz in visible_pentagons:
            self._draw_projected_pentagon(surface, sx, sy, scale)

        # --- Curved seams (connect adjacent pentagons) ---
        self._draw_seams(surface, cos_a, sin_a)

        # --- Sphere shading overlay ---
        self._draw_shading(surface)

        # --- Rim ---
        pygame.draw.circle(surface, (40, 40, 40), (int(cx), int(cy)), r, 1)

    def _draw_projected_pentagon(self, surface, sx, sy, scale):
        """Draw a pentagon at screen position (sx, sy), sized by scale."""
        radius = self.r * 0.32 * scale
        points = []
        for i in range(5):
            a = (math.tau / 5) * i - math.pi / 2
            px = sx + math.cos(a) * radius
            py = sy + math.sin(a) * radius
            points.append((px, py))
        pygame.draw.polygon(surface, (20, 20, 20), points)

    def _draw_seams(self, surface, cos_a, sin_a):
        """Draw curved seams between pentagons."""
        for px, py, pz in self.pentagon_dirs:
            rx = px * cos_a - py * sin_a
            ry = px * sin_a + py * cos_a
            rz = pz
            if rz < -0.2:
                continue

            sx = self.x + rx * self.r
            sy = self.y + ry * self.r

            # Draw a small circle outline around the pentagon (the seam)
            radius = self.r * 0.40 * max(rz, 0.3)
            pygame.draw.circle(
                surface, (60, 60, 60),
                (int(sx), int(sy)),
                int(radius),
                1
            )

    def _draw_shading(self, surface):
        """Radial shading for depth."""
        overlay = pygame.Surface((self.r * 2, self.r * 2), pygame.SRCALPHA)
        # Highlight top-left
        for i in range(6, 0, -1):
            alpha = int(20 * (i / 6))
            radius = int(self.r * (i / 6))
            pygame.draw.circle(
                overlay,
                (255, 255, 255, alpha),
                (self.r - self.r // 3, self.r - self.r // 3),
                radius
            )
        # Shadow bottom-right
        for i in range(6, 0, -1):
            alpha = int(30 * (i / 6))
            radius = int(self.r * (i / 6))
            pygame.draw.circle(
                overlay,
                (0, 0, 0, alpha),
                (self.r + self.r // 3, self.r + self.r // 3),
                radius
            )
        surface.blit(overlay, (self.x - self.r, self.y - self.r))
