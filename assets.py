import pygame
from settings import (
    BLUE,
    COIN_SIZE,
    GOLD,
    GRAY,
    PROFILE_SIZE,
    TITLE_SIZE,
    WHITE,
    FONT_SIZE,
)


class AssetManager:
    def __init__(self):
        pygame.font.init()
        self.font         = pygame.font.SysFont("Arial", FONT_SIZE)
        self.title_font   = pygame.font.SysFont("Arial", TITLE_SIZE, bold=True)
        self.small_font   = pygame.font.SysFont("Arial", 20)
        self.mystery_mark_font = pygame.font.SysFont("Arial", 44, bold=True)

        self.player_img = pygame.Surface((30, 30))
        self.player_img.fill(BLUE)

        self.coin_img = pygame.Surface((COIN_SIZE, COIN_SIZE))
        self.coin_img.fill(GOLD)

    def profile_avatar_me(self, color=BLUE, size=PROFILE_SIZE):
        """Draw the player's avatar circle with a smiley face."""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surf, color, (size // 2, size // 2), size // 2 - 2)
        pygame.draw.circle(surf, WHITE, (size // 2 - 12, size // 2 - 8), 5)
        pygame.draw.circle(surf, WHITE, (size // 2 + 12, size // 2 - 8), 5)
        pygame.draw.arc(surf, WHITE, (size // 2 - 14, size // 2 - 4, 28, 20), 3.4, 6.0, 2)
        return surf

    def profile_avatar_mystery(self, size=PROFILE_SIZE):
        """Draw the grey mystery '?' avatar for an unknown opponent."""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surf, GRAY, (size // 2, size // 2), size // 2 - 2)
        q    = self.mystery_mark_font.render("?", True, WHITE)
        qr   = q.get_rect(center=(size // 2, size // 2))
        surf.blit(q, qr)
        return surf