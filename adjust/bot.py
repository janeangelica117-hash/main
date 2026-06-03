import random


class Bot:
    def __init__(self, name="Computer Bot"):
        self.name             = name
        self.secret_character = None
        self.characters       = ["Peter", "Danlie", "Vince", "Chow", "Erwin"]

    def pick_character(self):
        """The bot secretly picks one character at the start of the game."""
        self.secret_character = random.choice(self.characters)
        print("[Bot] I have chosen my secret character!")

    def answer_question(self, trait):
        """Simulates the bot answering a yes/no trait question."""
        return random.choice([True, False])