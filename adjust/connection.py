import socketio as sio_lib

SERVER_URL = ""


class NetworkManager:
    def __init__(self):
        self.sio          = sio_lib.Client()
        self.is_connected = False
        self.players      = []   # list of OTHER players currently in the lobby

        # ── Socket event handlers ──────────────────────────────

        @self.sio.on("update_players")
        def on_update_players(data):
            """Server broadcasts the full player list whenever someone joins/leaves."""
            self.players = data if isinstance(data, list) else []

        @self.sio.on("disconnect")
        def on_disconnect():
            self.is_connected = False
            self.players      = []

    # ── Public API ─────────────────────────────────────────────

    def connect(self, username):
        """Connect to the hosted server and announce our username."""
        try:
            self.sio.connect(SERVER_URL)
            self.sio.emit("join", {"username": username.strip()})
            self.is_connected = True
            return True
        except Exception as e:
            print(f"[NetworkManager] Connection failed: {e}")
            return False

    def remove_self(self):
        """Gracefully disconnect from the server."""
        if self.is_connected:
            try:
                self.sio.disconnect()
            except Exception:
                pass
            self.is_connected = False
            self.players      = []

    def heartbeat(self, username):
        """Not needed for socket connections — the socket stays alive automatically."""
        pass

    def list_other_players(self):
        """Return the current list of other players in the lobby."""
        return list(self.players)

    def is_username_taken(self, username):
        """Check whether a username is already in use on the server."""
        desired = username.strip().lower()
        return any(p.strip().lower() == desired for p in self.players)