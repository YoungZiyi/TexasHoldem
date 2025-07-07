
import enum


class Suit(enum.Enum):
    """
    Represents the suit of a card.
    """
    SPADES = "♠"
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"


class Rank(enum.Enum):
    """
    Represents the rank of a card.
    """
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"


class Card:
    """
    Represents a playing card with a suit and a rank.
    """

    def __init__(self, suit: Suit, rank: Rank):
        self.suit = suit
        self.rank = rank

    def __repr__(self):
        return f"{self.rank.value}{self.suit.value}"

    def __eq__(self, other):
        return self.suit == other.suit and self.rank == other.rank
