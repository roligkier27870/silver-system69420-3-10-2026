import pygame
import asyncio

# ===== SETUP =====
pygame.init()
WIDTH, HEIGHT = 960, 540
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cosmic Kicker")
clock = pygame.time.Clock()

# ===== COLORS =====
GREEN = (46, 139, 87)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK = (26, 26, 46)

# ===== MAIN LOOP (async for pygbag) =====
async def main():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- draw ---
        screen.fill(DARK)
        pygame.draw.rect(screen, GREEN, (60, 60, WIDTH - 120, HEIGHT - 120))
        pygame.display.flip()

        # --- pygbag needs this every frame ---
        await asyncio.sleep(0)

    pygame.quit()

# ===== RUN =====
asyncio.run(main())
