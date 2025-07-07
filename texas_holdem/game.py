
from texas_holdem.deck import Deck
from texas_holdem.player import Player


class Game:
    """
    Represents a game of Texas Hold'em.
    """

    def __init__(self, player_names: list[str]):
        self.players = [Player(name) for name in player_names]
        self.deck = Deck()
        self.community_cards: list = []

    def deal_hole_cards(self):
        """
        Deals two hole cards to each player.
        """
        for _ in range(2):
            for player in self.players:
                player.add_card(self.deck.deal())

    def deal_flop(self):
        """
        Deals the flop (three community cards).
        """
        self.deck.deal()  # Burn one card
        for _ in range(3):
            self.community_cards.append(self.deck.deal())

    def deal_turn(self):
        """
        Deals the turn (one community card).
        """
        self.deck.deal()  # Burn one card
        self.community_cards.append(self.deck.deal())

    def deal_river(self):
        """
        Deals the river (one community card).
        """
        self.deck.deal()  # Burn one card
        self.community_cards.append(self.deck.deal())

    def get_game_state(self) -> dict:
        """
        Returns the current state of the game.
        """
        return {
            "players": [
                {
                    "name": player.name,
                    "hand": [repr(card) for card in player.hand],
                }
                for player in self.players
            ],
            "community_cards": [repr(card) for card in self.community_cards],
        }
