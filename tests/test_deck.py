
import pytest

from src.backend.texas_holdem.deck import Deck
from src.backend.texas_holdem.card import Card


def test_deck_creation():
    """
    Tests that a new deck has 52 cards.
    """
    deck = Deck()
    assert len(deck) == 52


def test_deck_shuffle():
    """
    Tests that the deck is shuffled.
    """
    deck1 = Deck()
    deck2 = Deck()
    # The probability of two shuffled decks being identical is extremely low
    assert deck1.cards != deck2.cards


def test_deck_deal():
    """
    Tests that dealing a card reduces the deck size by one.
    """
    deck = Deck()
    card = deck.deal()
    assert isinstance(card, Card)
    assert len(deck) == 51


def test_deal_from_empty_deck():
    """
    Tests that dealing from an empty deck raises a ValueError.
    """
    deck = Deck()
    # Deal all cards
    for _ in range(52):
        deck.deal()

    with pytest.raises(ValueError, match="The deck is empty."):
        deck.deal()
