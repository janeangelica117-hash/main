import pygame
import sys
from settings import (
    BLACK, BLUE, FPS, GOLD, GRAY, HEIGHT,
    LIGHT_GRAY, LOBBY_SIDE_PANEL_W, PANEL_BORDER,
    PROFILE_SIZE, WIDTH, WHITE,
)
from assets import AssetManager
from connection import NetworkManager
from bot import Bot
from entities import Button, SearchBar, PlayerDirectory


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Guess Who?")
        self.clock  = pygame.time.Clock()
        self.assets = AssetManager()

        # ── Player / lobby data ────────────────────────────────
        self.player_directory    = PlayerDirectory()
        self.username            = self.player_directory.ensure_unique("You")
        self.friend_username     = ""
        self.connected_players   = []
        self.search_results      = []
        self.search_status       = "Type a username and press Enter to search."
        self.profile_status      = "Set your profile name (must be unique)."

        # ── Networking ─────────────────────────────────────────
        self.presence            = NetworkManager()
        self.last_presence_sync_ms = 0

        # ── Offline / bot mode ─────────────────────────────────
        self.play_offline        = False
        self.bot_opponent        = None

        # ── Game state ─────────────────────────────────────────
        self.state = "START"   # "START" | "LOBBY" | "PLAYING"

        # ── START screen widgets ───────────────────────────────
        self.enter_btn = Button(
            WIDTH // 2 - 75, HEIGHT // 2 - 40, 150, 50,
            "ENTER", GRAY, self.assets.font,
        )
        self.bot_btn = Button(
            WIDTH // 2 - 75, HEIGHT // 2 + 30, 150, 50,
            "PLAY BOT", GOLD, self.assets.font,
        )
        self.name_input             = SearchBar(WIDTH // 2 - 110, HEIGHT // 2 + 100, 220, 30, self.assets.small_font)
        self.name_input.text        = self.username
        self.name_input.placeholder = "Unique username"

        # ── LOBBY screen widgets ───────────────────────────────
        self.start_game_btn = Button(
            (WIDTH - LOBBY_SIDE_PANEL_W) // 2 - 75, HEIGHT - 72, 150, 50,
            "START", GOLD, self.assets.font,
        )
        self.back_btn = Button(20, 20, 80, 35, "BACK", GRAY, self.assets.small_font)

        search_x         = WIDTH - LOBBY_SIDE_PANEL_W + 10
        search_w         = LOBBY_SIDE_PANEL_W - 20
        self.search_bar  = SearchBar(search_x, 80, search_w, 25, self.assets.small_font)

        # ── Avatars ────────────────────────────────────────────
        self.avatar_colors = [BLUE, GOLD, GRAY, (255, 100, 100), (100, 255, 100)]
        self.color_index   = 0
        self.avatar_me     = self.assets.profile_avatar_me()
        self.avatar_friend = self.assets.profile_avatar_mystery()

    # ── Main loop ──────────────────────────────────────────────

    def run(self):
        while True:
            self.handle_events()
            self.sync_presence()
            self.draw()
            self.clock.tick(FPS)

    # ── Event handling ─────────────────────────────────────────

    def handle_events(self):
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.presence.remove_self()
                pygame.quit()
                sys.exit()

            # ── Per-state widget events ────────────────────────
            if self.state == "LOBBY":
                submitted = self.search_bar.handle_event(event)
                self.search_results = self.player_directory.find(self.search_bar.text)
                if submitted:
                    self._run_player_search()

            elif self.state == "START":
                if self.name_input.handle_event(event):
                    self.apply_profile_name()

            # ── Mouse clicks ───────────────────────────────────
            if event.type == pygame.MOUSEBUTTONDOWN:

                if self.state == "START":
                    # Online multiplayer
                    if self.enter_btn.is_clicked(event.pos):
                        if not self.apply_profile_name():
                            continue
                        if self.presence.connect(self.username):
                            self.play_offline        = False
                            self.friend_username     = ""
                            self.connected_players   = []
                            self.search_results      = []
                            self.search_status       = "No players connected."
                            self.state               = "LOBBY"
                        else:
                            self.profile_status = "Could not connect to server. Try again."

                    # Offline vs bot
                    elif self.bot_btn.is_clicked(event.pos):
                        if not self.apply_profile_name():
                            continue
                        self.play_offline  = True
                        self.bot_opponent  = Bot()
                        bot_name           = self.player_directory.ensure_unique(self.bot_opponent.name)
                        self.connected_players = [bot_name]
                        self.friend_username   = bot_name
                        self.bot_opponent.pick_character()
                        self.search_results    = self.connected_players[:]
                        self.search_status     = "1 player connected."
                        self.state             = "LOBBY"

                elif self.state == "LOBBY":
                    panel_left   = WIDTH - LOBBY_SIDE_PANEL_W
                    start_x      = (panel_left - (PROFILE_SIZE * 2 + 48)) // 2
                    av_y         = 88
                    avatar_hitbox = pygame.Rect(start_x, av_y, PROFILE_SIZE, PROFILE_SIZE)

                    # Click avatar to cycle colour
                    if avatar_hitbox.collidepoint(event.pos):
                        self.color_index = (self.color_index + 1) % len(self.avatar_colors)
                        self.avatar_me   = self.assets.profile_avatar_me(self.avatar_colors[self.color_index])

                    # Back to START
                    if self.back_btn.is_clicked(event.pos):
                        self.presence.remove_self()
                        self.connected_players = []
                        self.search_results    = []
                        self.friend_username   = ""
                        self.search_status     = "Type a username and press Enter to search."
                        self.play_offline      = False
                        self.state             = "START"

                    # Start the game
                    if self.start_game_btn.is_clicked(event.pos):
                        self.state = "PLAYING"

                elif self.state == "PLAYING":
                    # Click anywhere to return to lobby (placeholder behaviour)
                    self.state = "LOBBY"

    # ── Drawing ────────────────────────────────────────────────

    def draw(self):
        self.screen.fill(WHITE)

        if self.state == "START":
            self._draw_start()
        elif self.state == "LOBBY":
            self._draw_lobby()
        elif self.state == "PLAYING":
            self._draw_playing()

        pygame.display.flip()

    def _draw_start(self):
        title = self.assets.title_font.render("Guess Who?", True, BLUE)
        self.screen.blit(title, (WIDTH // 2 - 150, HEIGHT // 2 - 120))

        self.screen.blit(self.enter_btn.image, self.enter_btn.rect)
        self.screen.blit(self.bot_btn.image,   self.bot_btn.rect)
        self.name_input.draw(self.screen)

        status = self.assets.small_font.render(self.profile_status, True, (80, 80, 110))
        self.screen.blit(status, (WIDTH // 2 - status.get_width() // 2, HEIGHT // 2 + 140))

    def _draw_lobby(self):
        panel_left = WIDTH - LOBBY_SIDE_PANEL_W

        # ── Side panel background ──────────────────────────────
        pygame.draw.rect(self.screen, LIGHT_GRAY, (panel_left, 0, LOBBY_SIDE_PANEL_W, HEIGHT))
        pygame.draw.line(self.screen, PANEL_BORDER, (panel_left, 0), (panel_left, HEIGHT), 2)

        # ── Header ────────────────────────────────────────────
        lobby_text = self.assets.font.render("GAME LOBBY", True, BLACK)
        self.screen.blit(lobby_text, ((panel_left // 2) - lobby_text.get_width() // 2, 16))

        # ── Avatars ───────────────────────────────────────────
        gap     = 48
        block_w = PROFILE_SIZE * 2 + gap
        start_x = ((panel_left - block_w) // 2)
        av_y    = 88

        self.screen.blit(self.avatar_me,     (start_x, av_y))
        self.screen.blit(self.avatar_friend, (start_x + PROFILE_SIZE + gap, av_y))

        you_lbl    = self.assets.font.render(self.username, True, BLACK)
        friend_name = self.friend_username if self.friend_username else ""
        friend_lbl = self.assets.font.render(friend_name, True, BLACK)

        self.screen.blit(you_lbl,
            (start_x + PROFILE_SIZE // 2 - you_lbl.get_width() // 2,
             av_y + PROFILE_SIZE + 8))
        self.screen.blit(friend_lbl,
            (start_x + PROFILE_SIZE + gap + PROFILE_SIZE // 2 - friend_lbl.get_width() // 2,
             av_y + PROFILE_SIZE + 8))

        # ── Friend list panel ─────────────────────────────────
        fl_title = self.assets.font.render("Friend list", True, BLACK)
        self.screen.blit(fl_title,
            (panel_left + (LOBBY_SIDE_PANEL_W - fl_title.get_width()) // 2, 24))

        status_msg = self.assets.small_font.render(self.search_status, True, (90, 90, 110))
        self.screen.blit(status_msg, (panel_left + 8, 110))

        if not self.connected_players:
            empty_msg = self.assets.small_font.render("No connected players.", True, (120, 80, 80))
            self.screen.blit(empty_msg, (panel_left + 8, 135))
        else:
            for idx, player_name in enumerate(self.search_results[:7]):
                row = self.assets.small_font.render(f"- {player_name}", True, BLACK)
                self.screen.blit(row, (panel_left + 8, 135 + idx * 20))

        # ── Buttons & search bar ──────────────────────────────
        self.screen.blit(self.start_game_btn.image, self.start_game_btn.rect)
        self.screen.blit(self.back_btn.image,       self.back_btn.rect)
        self.search_bar.draw(self.screen)

    def _draw_playing(self):
        msg     = self.assets.font.render("Gameplay Canvas", True, GRAY)
        sub_msg = self.assets.small_font.render("Click anywhere to go back to Lobby", True, BLACK)
        self.screen.blit(msg,     (WIDTH // 2 - msg.get_width() // 2 - 80,     HEIGHT // 2 - 20))
        self.screen.blit(sub_msg, (WIDTH // 2 - sub_msg.get_width() // 2 - 80, HEIGHT // 2 + 20))

    # ── Helpers ────────────────────────────────────────────────

    def _run_player_search(self):
        query = self.search_bar.text.strip()
        if not query:
            self.search_results = self.connected_players[:]
            count = len(self.search_results)
            self.search_status = f"{count} player(s) connected." if count else "No players connected."
            return

        matches = [n for n in self.connected_players if query.lower() in n.lower()]
        self.search_results = matches
        if not matches:
            self.search_status = "Player not found."
            return

        self.friend_username = matches[0]
        self.search_status   = f"Found {len(matches)} player(s)."

    def apply_profile_name(self):
        requested = self.name_input.text.strip()
        if not requested:
            self.profile_status = "Username cannot be empty."
            return False

        if requested.lower() == self.username.lower():
            self.profile_status = f"Profile name ready: {self.username}"
            return True

        if self.presence.is_username_taken(requested):
            self.profile_status = "That username is already in use by another player."
            return False

        if self.player_directory.exists(requested):
            self.profile_status = "That username is already taken."
            return False

        old_name = self.username
        self.player_directory.unregister(old_name)
        if not self.player_directory.register(requested):
            self.player_directory.register(old_name)
            self.profile_status = "Could not update profile name."
            return False

        self.username       = requested
        self.search_results = self.player_directory.find(self.search_bar.text)
        self.profile_status = f"Profile name set: {self.username}"
        return True

    def sync_presence(self):
        """Pull the latest player list from the server every second."""
        now_ms = pygame.time.get_ticks()
        if now_ms - self.last_presence_sync_ms < 1000:
            return
        self.last_presence_sync_ms = now_ms

        if self.play_offline or self.state not in ("LOBBY", "PLAYING"):
            return

        self.connected_players = self.presence.list_other_players()

        if self.connected_players and self.friend_username not in self.connected_players:
            self.friend_username = self.connected_players[0]
        if not self.connected_players:
            self.friend_username = ""

        if self.state == "LOBBY":
            query = self.search_bar.text.strip()
            if query:
                self.search_results = [
                    n for n in self.connected_players if query.lower() in n.lower()
                ]
            else:
                self.search_results = self.connected_players[:]

            count = len(self.connected_players)
            self.search_status = f"{count} player(s) connected." if count else "No players connected."


if __name__ == "__main__":
    Game().run()