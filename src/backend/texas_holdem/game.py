
from typing import List, Tuple, Optional

from .deck import Deck
from .player import Player
from .hand_evaluator import get_hand_rank_and_kickers, compare_hands, HandRank


class Game:
    """
    Represents a game of Texas Hold'em.
    """
    MAX_PLAYERS = 8
    DEFAULT_SMALL_BLIND = 10
    DEFAULT_BIG_BLIND = 20

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.seats: List[Optional[Player]] = [None] * self.MAX_PLAYERS
        self.deck = Deck()
        self.community_cards: list = []
        self.winner: dict | None = None
        self.game_started = False  # True if a round is actively in progress
        self.pot = 0
        self.current_bet = 0  # The highest bet made in the current betting round
        self.minimum_raise = self.DEFAULT_BIG_BLIND
        self.dealer_button = -1  # Index of the player with the dealer button
        self.current_player_index = -1  # Index of the player whose turn it is to act
        self.betting_round = ""  # "pre-flop", "flop", "turn", "river", "showdown"
        self.last_raiser_index: Optional[int] = None  # Index of the last player who raised
        self.players_to_act_count = 0 # Number of players who still need to act in the current round

    def join_seat(self, player_name: str, seat_index: int) -> bool:
        """
        Allows a player to join a specific seat.
        Returns True if successful, False otherwise.
        """
        if not (0 <= seat_index < self.MAX_PLAYERS):
            return False  # Invalid seat index
        if self.seats[seat_index] is not None:
            return False  # Seat already occupied

        # Check if player already in another seat
        for i, player in enumerate(self.seats):
            if player and player.name == player_name:
                return False  # Player already in a seat

        self.seats[seat_index] = Player(player_name)
        return True

    def leave_seat(self, player_name: str) -> bool:
        """
        Allows a player to leave their seat.
        Returns True if successful, False otherwise.
        """
        for i, player in enumerate(self.seats):
            if player and player.name == player_name:
                self.seats[i] = None
                return True
        return False

    def get_players_in_game(self) -> List[Player]:
        """
        Returns a list of actual Player objects currently in seats.
        """
        return [player for player in self.seats if player is not None]

    def _get_next_active_player_index(self, start_index: int) -> int:
        """
        Helper to find the next active player in a circular manner.
        An active player is one who has not folded and is not all-in (unless they need to act).
        """
        num_players = len(self.seats)
        for i in range(1, num_players + 1):
            next_index = (start_index + i) % num_players
            player = self.seats[next_index]
            if player and not player.has_folded and not player.is_all_in:
                return next_index
        return -1 # Should not happen if there are active players

    def _get_next_player_to_act_index(self, start_index: int) -> int:
        """
        Finds the next player who needs to act in the current betting round.
        A player needs to act if they haven't folded, aren't all-in, and haven't matched the current bet.
        """
        num_players = len(self.seats)
        for i in range(1, num_players + 1):
            next_index = (start_index + i) % num_players
            player = self.seats[next_index]
            if player and not player.has_folded and not player.is_all_in and player.current_bet_in_round < self.current_bet:
                return next_index
            # Special case: if all players are all-in or folded, round ends
            if len([p for p in self.get_players_in_game() if not p.has_folded and not p.is_all_in]) == 0:
                return -1
        return -1 # No one else needs to act

    def _collect_bets_to_pot(self):
        """
        Moves chips from players' current_bet_in_round to the main pot.
        """
        for player in self.get_players_in_game():
            self.pot += player.current_bet_in_round
            player.current_bet_in_round = 0
        self.current_bet = 0 # Reset current bet for next round

    def _start_betting_round(self):
        """
        Initializes a new betting round.
        """
        self._collect_bets_to_pot()
        self.current_bet = 0
        self.minimum_raise = self.DEFAULT_BIG_BLIND
        self.last_raiser_index = None

        # Reset player betting states for the new round
        for player in self.get_players_in_game():
            player.reset_bet_for_new_round()

        # Determine who acts first in this round
        # Pre-flop: Player after Big Blind
        # Flop, Turn, River: Player after Dealer Button (first active player clockwise)
        if self.betting_round == "pre-flop":
            # Find big blind position, then next active player
            big_blind_pos = (self.dealer_button + 2) % self.MAX_PLAYERS
            self.current_player_index = self._get_next_active_player_index(big_blind_pos)
        else:
            self.current_player_index = self._get_next_active_player_index(self.dealer_button)

        # Count players who need to act
        self.players_to_act_count = len([p for p in self.get_players_in_game() if not p.has_folded and not p.is_all_in])

    def _end_betting_round(self) -> bool:
        """
        Checks if the current betting round has ended.
        A betting round ends when:
        1. All active players have matched the current bet.
        2. Only one player remains (others folded).
        Returns True if the round ended, False otherwise.
        """
        active_players = [p for p in self.get_players_in_game() if not p.has_folded]

        if len(active_players) <= 1:
            return True # Only one player left, round ends

        # Check if all active players have matched the current bet or are all-in
        all_matched = True
        for player in active_players:
            if not player.is_all_in and player.current_bet_in_round < self.current_bet:
                all_matched = False
                break
        
        # If all matched and current player is the last raiser or no one raised yet
        if all_matched and (self.current_player_index == self.last_raiser_index or self.last_raiser_index is None):
            return True

        return False

    def start_new_round(self):
        """
        Initializes a new game round.
        """
        active_players = self.get_players_in_game()
        if len(active_players) < 2:
            raise ValueError("Need at least two players to start a game.")

        self.reset_game_state_for_new_round()
        self.game_started = True

        # Rotate dealer button
        self.dealer_button = (self.dealer_button + 1) % self.MAX_PLAYERS
        while self.seats[self.dealer_button] is None: # Skip empty seats
            self.dealer_button = (self.dealer_button + 1) % self.MAX_PLAYERS

        # Assign blinds
        small_blind_player_index = self._get_next_active_player_index(self.dealer_button)
        big_blind_player_index = self._get_next_active_player_index(small_blind_player_index)

        small_blind_player = self.seats[small_blind_player_index]
        big_blind_player = self.seats[big_blind_player_index]

        # Place blinds
        small_blind_player.bet(self.DEFAULT_SMALL_BLIND)
        big_blind_player.bet(self.DEFAULT_BIG_BLIND)

        self.pot += small_blind_player.current_bet_in_round + big_blind_player.current_bet_in_round
        self.current_bet = self.DEFAULT_BIG_BLIND

        # Deal hole cards
        for _ in range(2):
            for player in active_players:
                player.add_card(self.deck.deal())

        self.betting_round = "pre-flop"
        # First player to act pre-flop is after big blind
        self.current_player_index = self._get_next_active_player_index(big_blind_player_index)
        self.last_raiser_index = big_blind_player_index # Big blind is considered the last raiser initially
        self.players_to_act_count = len([p for p in active_players if not p.has_folded and not p.is_all_in and p.current_bet_in_round < self.current_bet])

    def deal_flop(self):
        """
        Deals the flop (three community cards) and starts flop betting round.
        """
        self.deck.deal()  # Burn one card
        for _ in range(3):
            self.community_cards.append(self.deck.deal())
        self.betting_round = "flop"
        self._start_betting_round()

    def deal_turn(self):
        """
        Deals the turn (one community card) and starts turn betting round.
        """
        self.deck.deal()  # Burn one card
        self.community_cards.append(self.deck.deal())
        self.betting_round = "turn"
        self._start_betting_round()

    def deal_river(self):
        """
        Deals the river (one community card) and starts river betting round.
        """
        self.deck.deal()  # Burn one card
        self.community_cards.append(self.deck.deal())
        self.betting_round = "river"
        self._start_betting_round()

    def end_round_and_determine_winner(self):
        """
        Ends the current round, determines winner, and prepares for next round.
        """
        self.betting_round = "showdown"
        self.determine_winner()
        self.game_started = False  # Game round ends

    def determine_winner(self):
        """
        Determines the winner of the game based on hand rankings.
        This should only be called after the river card is dealt.
        """
        active_players = [p for p in self.get_players_in_game() if not p.has_folded]

        if len(active_players) == 1:
            self.winner = {"name": active_players[0].name, "hand_rank": "Last Player Standing", "best_five_cards": []}
            # TODO: Award pot to this player
            return

        if len(self.community_cards) < 5:  # Only determine winner after river
            self.winner = None
            return

        best_hand_rank = HandRank.HIGH_CARD
        winning_player = None
        winning_hand_cards = []

        for player in active_players:
            # Combine player's hole cards with community cards
            seven_cards = player.hand + self.community_cards
            current_hand_rank, current_best_five = get_hand_rank_and_kickers(seven_cards)

            if winning_player is None or current_hand_rank.value > best_hand_rank.value:
                best_hand_rank = current_hand_rank
                winning_player = player
                winning_hand_cards = seven_cards  # Store all 7 cards for evaluation
            elif current_hand_rank.value == best_hand_rank.value:
                # Compare best five cards if hand ranks are the same
                comparison_result = compare_hands(seven_cards, winning_hand_cards)
                if comparison_result == 1:  # Current player wins tie-breaker
                    winning_player = player
                    winning_hand_cards = seven_cards
                # If comparison_result is -1, current player loses tie-breaker, do nothing
                # If comparison_result is 0, it's a tie, current winner remains

        if winning_player:
            self.winner = {
                "name": winning_player.name,
                "hand_rank": best_hand_rank.name,
                "best_five_cards": [repr(card) for card in get_hand_rank_and_kickers(winning_hand_cards)[1]]
            }
        # TODO: Award pot to winner(s)

    def reset_game_state_for_new_round(self):
        """
        Resets the game state for a new round, keeping players in their seats.
        """
        self.deck = Deck()
        self.community_cards = []
        self.winner = None
        self.pot = 0
        self.current_bet = 0
        self.minimum_raise = self.DEFAULT_BIG_BLIND
        self.current_player_index = -1
        self.betting_round = ""
        self.last_raiser_index = None
        self.players_to_act_count = 0

        for player in self.get_players_in_game():
            player.clear_hand()
            player.reset_bet_for_new_round()

    def get_game_state(self) -> dict:
        """
        Returns the current state of the game.
        """
        players_data = []
        for i, player in enumerate(self.seats):
            if player:
                players_data.append({
                    "seat_index": i,
                    "name": player.name,
                    "hand": [repr(card) for card in player.hand],
                    "chips": player.chips,
                    "current_bet_in_round": player.current_bet_in_round,
                    "has_folded": player.has_folded,
                    "is_all_in": player.is_all_in,
                })
            else:
                players_data.append({"seat_index": i, "name": None, "hand": [], "chips": 0, "current_bet_in_round": 0, "has_folded": False, "is_all_in": False})

        state = {
            "game_id": self.game_id,
            "seats": players_data,
            "community_cards": [repr(card) for card in self.community_cards],
            "winner": self.winner,
            "game_started": self.game_started,
            "pot": self.pot,
            "current_bet": self.current_bet,
            "minimum_raise": self.minimum_raise,
            "dealer_button": self.dealer_button,
            "current_player_index": self.current_player_index,
            "betting_round": self.betting_round,
            "last_raiser_index": self.last_raiser_index,
            "players_to_act_count": self.players_to_act_count
        }
        return state

    def _get_player_by_name(self, player_name: str) -> Optional[Player]:
        for player in self.get_players_in_game():
            if player.name == player_name:
                return player
        return None

    def _get_player_seat_index(self, player_name: str) -> int:
        for i, player in enumerate(self.seats):
            if player and player.name == player_name:
                return i
        return -1

    def _advance_player_turn(self):
        """
        Advances the current_player_index to the next player who needs to act.
        """
        self.players_to_act_count -= 1
        if self.players_to_act_count <= 0: # All players acted or round ended
            return # Betting round will end

        start_index = self.current_player_index
        next_player_index = self._get_next_active_player_index(start_index)

        # If the next player is the last raiser and everyone else has acted, round ends
        if next_player_index == self.last_raiser_index and self.last_raiser_index is not None:
            self.current_player_index = -1 # Indicate betting round ended
            return

        self.current_player_index = next_player_index

    def action_bet(self, player_name: str, amount: int) -> bool:
        player_index = self._get_player_seat_index(player_name)
        if player_index != self.current_player_index:
            raise ValueError("Not player's turn.")

        player = self.seats[player_index]
        if not player or player.has_folded or player.is_all_in:
            raise ValueError("Player cannot act.")

        if amount < self.current_bet - player.current_bet_in_round: # Cannot bet less than current bet to call
            raise ValueError(f"Bet must be at least {self.current_bet - player.current_bet_in_round} to call.")

        if amount < self.current_bet + self.minimum_raise - player.current_bet_in_round and amount != player.chips:
            raise ValueError(f"Bet must be at least {self.current_bet + self.minimum_raise - player.current_bet_in_round} to raise, or go all-in.")

        actual_bet_amount = player.bet(amount)
        self.current_bet = player.current_bet_in_round # Update current bet to player's total bet in round
        self.last_raiser_index = player_index
        self.minimum_raise = actual_bet_amount - (self.current_bet - actual_bet_amount) # This needs careful calculation

        self._advance_player_turn()
        return True

    def action_call(self, player_name: str) -> bool:
        player_index = self._get_player_seat_index(player_name)
        if player_index != self.current_player_index:
            raise ValueError("Not player's turn.")

        player = self.seats[player_index]
        if not player or player.has_folded or player.is_all_in:
            raise ValueError("Player cannot act.")

        amount_to_call = self.current_bet - player.current_bet_in_round
        if amount_to_call <= 0: # Cannot call if already matched or raised
            raise ValueError("Cannot call. Current bet is not higher than your bet.")

        player.bet(amount_to_call)
        self._advance_player_turn()
        return True

    def action_raise(self, player_name: str, amount: int) -> bool:
        player_index = self._get_player_seat_index(player_name)
        if player_index != self.current_player_index:
            raise ValueError("Not player's turn.")

        player = self.seats[player_index]
        if not player or player.has_folded or player.is_all_in:
            raise ValueError("Player cannot act.")

        # Amount is the total bet for the round, not just the raise amount
        amount_to_raise_to = amount
        if amount_to_raise_to < self.current_bet + self.minimum_raise:
            raise ValueError(f"Raise must be at least {self.current_bet + self.minimum_raise}.")

        actual_bet_amount = player.bet(amount_to_raise_to - player.current_bet_in_round)
        self.minimum_raise = actual_bet_amount - (self.current_bet - player.current_bet_in_round) # This needs careful calculation
        self.current_bet = player.current_bet_in_round
        self.last_raiser_index = player_index

        self._advance_player_turn()
        return True

    def action_fold(self, player_name: str) -> bool:
        player_index = self._get_player_seat_index(player_name)
        if player_index != self.current_player_index:
            raise ValueError("Not player's turn.")

        player = self.seats[player_index]
        if not player:
            raise ValueError("Player not found.")

        player.has_folded = True
        self._advance_player_turn()
        return True

    def action_check(self, player_name: str) -> bool:
        player_index = self._get_player_seat_index(player_name)
        if player_index != self.current_player_index:
            raise ValueError("Not player's turn.")

        player = self.seats[player_index]
        if not player or player.has_folded or player.is_all_in:
            raise ValueError("Player cannot act.")

        if player.current_bet_in_round < self.current_bet:
            raise ValueError("Cannot check when current bet is higher than your bet. You must call or raise.")

        self._advance_player_turn()
        return True
