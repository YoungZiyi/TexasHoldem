
from texas_holdem.card import Card


class Player:
    """
    Represents a player in the game.
    """

    def __init__(self, name: str):
        self.name = name
        self.hand: list[Card] = []

    def __repr__(self):
        return f"Player({self.name})"

    def add_card(self, card: Card):
        """
        Adds a card to the player's hand.
        """
        self.hand.append(card)

    def clear_hand(self):
        """
        Removes all cards from the player's hand.
        """
        self.hand = []
