import pygame
from settings import BLACK


class Button(pygame.sprite.Sprite):
    """A simple clickable rectangle with centred text."""

    def __init__(self, x, y, width, height, text, color, font):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect  = self.image.get_rect(topleft=(x, y))

        text_surf  = font.render(text, True, BLACK)
        text_rect  = text_surf.get_rect(center=(width // 2, height // 2))
        self.image.blit(text_surf, text_rect)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)


class FriendLabel(pygame.sprite.Sprite):
    """A single line label showing a player's name in the friend list."""

    def __init__(self, x, y, name, font):
        super().__init__()
        self.image = font.render(f"• {name}", True, BLACK)
        self.rect  = self.image.get_rect(topleft=(x, y))


class SearchBar:
    """A text input box with placeholder text."""

    def __init__(self, x, y, width, height, font):
        self.rect                = pygame.Rect(x, y, width, height)
        self.font                = font
        self.text                = ""
        self.active              = False
        self.bg_color            = (255, 255, 255)
        self.border_color        = (170, 170, 170)
        self.active_border_color = (80,  140, 255)
        self.text_color          = BLACK
        self.placeholder         = "Search..."

    def handle_event(self, event):
        """Returns True when the user presses Enter (submit)."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            return False

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return True
            elif event.unicode and event.unicode.isprintable():
                self.text += event.unicode
        return False

    def draw(self, surface):
        pygame.draw.rect(surface, self.bg_color, self.rect)
        border = self.active_border_color if self.active else self.border_color
        pygame.draw.rect(surface, border, self.rect, 2)

        shown_text = self.text if self.text else self.placeholder
        text_color = self.text_color if self.text else (130, 130, 130)
        text_surf  = self.font.render(shown_text, True, text_color)
        text_y     = self.rect.y + (self.rect.height - text_surf.get_height()) // 2
        surface.blit(text_surf, (self.rect.x + 8, text_y))


class PlayerDirectory:
    """Stores players with case-insensitive unique usernames."""

    def __init__(self):
        self._players = {}   # { normalized_key: original_name }

    @staticmethod
    def _normalize(username):
        return username.strip().lower()

    def register(self, username):
        clean = username.strip()
        key   = self._normalize(clean)
        if not clean or key in self._players:
            return False
        self._players[key] = clean
        return True

    def unregister(self, username):
        key = self._normalize(username)
        if key in self._players:
            del self._players[key]
            return True
        return False

    def exists(self, username):
        return self._normalize(username) in self._players

    def ensure_unique(self, preferred_name):
        """Register and return a unique version of the preferred name."""
        clean = preferred_name.strip() or "Player"
        if self.register(clean):
            return clean
        suffix = 2
        while True:
            candidate = f"{clean}{suffix}"
            if self.register(candidate):
                return candidate
            suffix += 1

    def find(self, query):
        q = query.strip().lower()
        if not q:
            return self.all_players()
        return sorted(
            [name for name in self._players.values() if q in name.lower()],
            key=str.lower,
        )

    def all_players(self):
        return sorted(self._players.values(), key=str.lower)