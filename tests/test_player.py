import pytest
from src.backend.texas_holdem.player import Player
from src.backend.texas_holdem.card import Card, Suit, Rank


def test_player_creation():
    """
    Tests that a player is created with the correct name, initial chips, and empty hand.
    """
    player = Player(name="Alice")
    assert player.name == "Alice"
    assert player.hand == []
    assert player.chips == 1000
    assert player.current_bet_in_round == 0
    assert player.has_folded is False
    assert player.is_all_in is False


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


def test_bet():
    """
    Tests that a player can place a bet and chips are deducted.
    """
    player = Player(name="David", initial_chips=500)
    bet_amount = player.bet(100)
    assert bet_amount == 100
    assert player.chips == 400
    assert player.current_bet_in_round == 100
    assert player.is_all_in is False


def test_bet_all_in():
    """
    Tests that a player goes all-in when betting all their chips.
    """
    player = Player(name="Eve", initial_chips=50)
    bet_amount = player.bet(100) # Try to bet more than chips
    assert bet_amount == 50
    assert player.chips == 0
    assert player.current_bet_in_round == 50
    assert player.is_all_in is True


def test_add_chips():
    """
    Tests that chips can be added to a player's stack.
    """
    player = Player(name="Frank", initial_chips=200)
    player.add_chips(300)
    assert player.chips == 500


def test_add_negative_chips_raises_error():
    """
    Tests that adding negative chips raises a ValueError.
    """
    player = Player(name="Grace")
    with pytest.raises(ValueError, match="Amount to add cannot be negative."):
        player.add_chips(-100)


def test_bet_negative_amount_raises_error():
    """
    Tests that betting a negative amount raises a ValueError.
    """
    player = Player(name="Heidi")
    with pytest.raises(ValueError, match="Bet amount cannot be negative."):
        player.bet(-10)


def test_reset_bet_for_new_round():
    """
    Tests that player's betting state is reset for a new round.
    """
    player = Player(name="Ivan", initial_chips=1000)
    player.bet(50)
    player.has_folded = True
    player.is_all_in = True # Simulate all-in for testing reset

    player.reset_bet_for_new_round()
    assert player.current_bet_in_round == 0
    assert player.has_folded is False
    assert player.is_all_in is False
    assert player.chips == 950 # Chips should not be reset