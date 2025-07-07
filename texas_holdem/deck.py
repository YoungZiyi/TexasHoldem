
import random

from texas_holdem.card import Card, Suit, Rank


class Deck:
    """
    Represents a deck of 52 playing cards.
    """

    def __init__(self):
        self.cards = [Card(suit, rank) for suit in Suit for rank in Rank]
        self.shuffle()

    def shuffle(self):
        """
        Shuffles the deck of cards.
        """
        random.shuffle(self.cards)

    def deal(self) -> Card:
        """
        Deals one card from the top of the deck.

        Returns:
            The card dealt from the deck.

        Raises:
            ValueError: If the deck is empty.
        """
        if not self.cards:
            raise ValueError("The deck is empty.")
        return self.cards.pop()

    def __len__(self):
        return len(self.cards)
