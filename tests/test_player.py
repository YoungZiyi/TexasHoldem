
from texas_holdem.player import Player
from texas_holdem.card import Card, Suit, Rank


def test_player_creation():
    """
    Tests that a player is created with the correct name and an empty hand.
    """
    player = Player(name="Alice")
    assert player.name == "Alice"
    assert player.hand == []


def test_add_card_to_hand():
    """
    Tests that a card can be added to a player's hand.
    """
    player = Player(name="Bob")
    card = Card(Suit.HEARTS, Rank.ACE)
    player.add_card(card)
    assert player.hand == [card]


def test_clear_hand():
    """
    Tests that the player's hand can be cleared.
    """
    player = Player(name="Charlie")
    player.add_card(Card(Suit.CLUBS, Rank.KING))
    player.clear_hand()
    assert player.hand == []
