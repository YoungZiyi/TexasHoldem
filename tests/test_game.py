
import pytest
from src.backend.texas_holdem.game import Game
from src.backend.texas_holdem.player import Player
from src.backend.texas_holdem.card import Card, Suit, Rank


def test_game_creation():
    """
    Tests that a game is created with the correct ID and empty seats.
    """
    game = Game(game_id="test_game_1")
    assert game.game_id == "test_game_1"
    assert len(game.seats) == Game.MAX_PLAYERS
    assert all(seat is None for seat in game.seats)
    assert game.pot == 0
    assert game.current_bet == 0
    assert game.betting_round == ""
    assert game.dealer_button == -1


def test_join_seat():
    """
    Tests that a player can join an empty seat.
    """
    game = Game(game_id="test_game_2")
    assert game.join_seat("Alice", 0) is True
    assert game.seats[0].name == "Alice"
    assert game.join_seat("Bob", 1) is True
    assert game.seats[1].name == "Bob"


def test_join_occupied_seat_fails():
    """
    Tests that a player cannot join an occupied seat.
    """
    game = Game(game_id="test_game_3")
    game.join_seat("Alice", 0)
    assert game.join_seat("Bob", 0) is False


def test_player_already_in_game_fails():
    """
    Tests that a player cannot join if they are already in another seat.
    """
    game = Game(game_id="test_game_4")
    game.join_seat("Alice", 0)
    assert game.join_seat("Alice", 1) is False


def test_leave_seat():
    """
    Tests that a player can leave their seat.
    """
    game = Game(game_id="test_game_5")
    game.join_seat("Alice", 0)
    assert game.leave_seat("Alice") is True
    assert game.seats[0] is None


def test_leave_non_existent_player_fails():
    """
    Tests that leaving a non-existent player fails.
    """
    game = Game(game_id="test_game_6")
    game.join_seat("Alice", 0)
    assert game.leave_seat("Bob") is False


def test_start_new_round_blinds_and_hole_cards():
    """
    Tests that a new round starts correctly, blinds are placed, and hole cards are dealt.
    """
    game = Game(game_id="test_game_7")
    game.join_seat("Alice", 0) # Dealer
    game.join_seat("Bob", 1)   # Small Blind
    game.join_seat("Charlie", 2) # Big Blind

    game.start_new_round()

    assert game.game_started is True
    assert game.betting_round == "pre-flop"
    assert game.dealer_button == 0 # Alice is dealer

    # Bob (SB) and Charlie (BB) should have placed blinds
    assert game.seats[1].chips == Player.initial_chips - game.DEFAULT_SMALL_BLIND
    assert game.seats[1].current_bet_in_round == game.DEFAULT_SMALL_BLIND
    assert game.seats[2].chips == Player.initial_chips - game.DEFAULT_BIG_BLIND
    assert game.seats[2].current_bet_in_round == game.DEFAULT_BIG_BLIND

    assert game.pot == game.DEFAULT_SMALL_BLIND + game.DEFAULT_BIG_BLIND
    assert game.current_bet == game.DEFAULT_BIG_BLIND

    # Hole cards dealt
    assert len(game.seats[0].hand) == 2
    assert len(game.seats[1].hand) == 2
    assert len(game.seats[2].hand) == 2

    # Current player to act should be after Big Blind (Alice in this case)
    assert game.current_player_index == 0


def test_action_fold():
    game = Game(game_id="test_game_fold")
    game.join_seat("Alice", 0)
    game.join_seat("Bob", 1)
    game.join_seat("Charlie", 2)
    game.start_new_round()

    # Alice (current player) folds
    game.action_fold("Alice")
    assert game.seats[0].has_folded is True
    # Next player to act should be Bob
    assert game.current_player_index == 1


def test_action_call():
    game = Game(game_id="test_game_call")
    game.join_seat("Alice", 0) # Dealer
    game.join_seat("Bob", 1)   # Small Blind
    game.join_seat("Charlie", 2) # Big Blind
    game.start_new_round()

    # Alice (current player) calls
    game.action_call("Alice")
    assert game.seats[0].chips == Player.initial_chips - game.DEFAULT_BIG_BLIND # Alice calls BB
    assert game.seats[0].current_bet_in_round == game.DEFAULT_BIG_BLIND
    assert game.current_player_index == 1 # Bob's turn


def test_action_bet_and_raise():
    game = Game(game_id="test_game_bet_raise")
    game.join_seat("Alice", 0) # Dealer
    game.join_seat("Bob", 1)   # Small Blind
    game.join_seat("Charlie", 2) # Big Blind
    game.start_new_round()

    # Alice (current player) raises to 50
    game.action_raise("Alice", 50)
    assert game.seats[0].chips == Player.initial_chips - 50
    assert game.seats[0].current_bet_in_round == 50
    assert game.current_bet == 50
    assert game.last_raiser_index == 0
    assert game.current_player_index == 1 # Bob's turn

    # Bob (SB) calls the raise
    game.action_call("Bob")
    assert game.seats[1].chips == Player.initial_chips - game.DEFAULT_SMALL_BLIND - (50 - game.DEFAULT_SMALL_BLIND)
    assert game.seats[1].current_bet_in_round == 50
    assert game.current_player_index == 2 # Charlie's turn

    # Charlie (BB) folds
    game.action_fold("Charlie")
    assert game.seats[2].has_folded is True
    # Betting round should end as Alice and Bob matched, Charlie folded
    # This test needs to be more robust to check end of round conditions


def test_deal_flop_starts_new_betting_round():
    game = Game(game_id="test_game_flop_betting")
    game.join_seat("Alice", 0)
    game.join_seat("Bob", 1)
    game.join_seat("Charlie", 2)
    game.start_new_round()

    # Simulate pre-flop betting round completion (e.g., all call)
    game.action_call("Alice")
    game.action_call("Bob") # Bob already has SB, just needs to match BB
    game.action_check("Charlie") # Charlie already has BB, can check

    # Now deal flop
    game.deal_flop()
    assert len(game.community_cards) == 3
    assert game.betting_round == "flop"
    assert game.pot > 0 # Blinds and calls should be in pot
    assert game.current_bet == 0 # New betting round, current bet resets
    assert game.current_player_index == 1 # Bob (SB) acts first on flop


def test_deal_river_determines_winner():
    game = Game(game_id="test_game_river_winner")
    game.join_seat("Alice", 0)
    game.join_seat("Bob", 1)
    game.join_seat("Charlie", 2)
    game.start_new_round()

    # Simulate betting rounds and dealing all community cards
    game.action_call("Alice")
    game.action_call("Bob")
    game.action_check("Charlie")
    game.deal_flop()
    game.action_check("Bob")
    game.action_check("Charlie")
    game.action_check("Alice")
    game.deal_turn()
    game.action_check("Bob")
    game.action_check("Charlie")
    game.action_check("Alice")
    game.deal_river()

    assert len(game.community_cards) == 5
    assert game.winner is not None
    assert game.game_started is False


def test_reset_game_round_resets_betting_state():
    """
    Tests that the game state can be reset for a new round, including betting states.
    """
    game = Game(game_id="test_game_reset_betting")
    game.join_seat("Alice", 0)
    game.join_seat("Bob", 1)
    game.start_new_round()
    game.action_call("Alice")
    game.action_check("Bob")

    game.reset_game_state_for_new_round()
    assert game.pot == 0
    assert game.current_bet == 0
    assert game.betting_round == ""
    assert game.current_player_index == -1
    assert game.last_raiser_index is None
    assert game.seats[0].current_bet_in_round == 0
    assert game.seats[0].has_folded is False
    assert game.seats[0].is_all_in is False
    assert game.seats[1].current_bet_in_round == 0
    assert game.seats[1].has_folded is False
    assert game.seats[1].is_all_in is False


def test_get_game_state_serialization_with_betting_info():
    """
    Tests that get_game_state returns serializable data including new betting info.
    """
    game = Game(game_id="test_game_state_betting")
    game.join_seat("Alice", 0)
    game.join_seat("Bob", 1)
    game.start_new_round()

    state = game.get_game_state()
    assert "pot" in state
    assert "current_bet" in state
    assert "minimum_raise" in state
    assert "dealer_button" in state
    assert "current_player_index" in state
    assert "betting_round" in state
    assert "last_raiser_index" in state
    assert "players_to_act_count" in state
    assert state["seats"][0]["chips"] is not None
    assert state["seats"][0]["current_bet_in_round"] is not None
    assert state["seats"][0]["has_folded"] is not None
    assert state["seats"][0]["is_all_in"] is not None


# Helper to set initial chips for Player class for testing
Player.initial_chips = 1000
