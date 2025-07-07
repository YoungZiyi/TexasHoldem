
from src.backend.texas_holdem.game import Game


def test_game_creation():
    """
    Tests that a game is created with the correct number of players.
    """
    game = Game(player_names=["Alice", "Bob"])
    assert len(game.players) == 2
    assert game.players[0].name == "Alice"


def test_deal_hole_cards():
    """
    Tests that each player receives two hole cards.
    """
    game = Game(player_names=["Alice", "Bob"])
    game.deal_hole_cards()
    for player in game.players:
        assert len(player.hand) == 2
    assert len(game.deck) == 52 - 4  # 2 players * 2 cards


def test_deal_flop():
    """
    Tests that the flop consists of three community cards.
    """
    game = Game(player_names=["Alice", "Bob"])
    game.deal_flop()
    assert len(game.community_cards) == 3
    assert len(game.deck) == 52 - 4  # 1 burn card + 3 flop cards


def test_deal_turn():
    """
    Tests that the turn adds one community card.
    """
    game = Game(player_names=["Alice", "Bob"])
    game.deal_flop()
    game.deal_turn()
    assert len(game.community_cards) == 4
    assert len(game.deck) == 52 - 6  # Flop (4) + Burn (1) + Turn (1)


def test_deal_river():
    """
    Tests that the river adds the final community card.
    """
    game = Game(player_names=["Alice", "Bob"])
    game.deal_flop()
    game.deal_turn()
    game.deal_river()
    assert len(game.community_cards) == 5
    assert len(game.deck) == 52 - 8  # Flop (4) + Turn (2) + River (2)
