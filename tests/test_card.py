
from src.backend.texas_holdem.card import Card, Suit, Rank


def test_card_creation():
    """
    Tests that a card is created with the correct suit and rank.
    """
    card = Card(Suit.HEARTS, Rank.ACE)
    assert card.suit == Suit.HEARTS
    assert card.rank == Rank.ACE


def test_card_representation():
    """
    Tests that the card's string representation is correct.
    """
    card = Card(Suit.SPADES, Rank.KING)
    assert repr(card) == "K♠"


def test_card_equality():
    """
    Tests that two cards with the same suit and rank are considered equal.
    """
    card1 = Card(Suit.DIAMONDS, Rank.QUEEN)
    card2 = Card(Suit.DIAMONDS, Rank.QUEEN)
    card3 = Card(Suit.CLUBS, Rank.QUEEN)
    assert card1 == card2
    assert card1 != card3
