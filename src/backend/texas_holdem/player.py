from .card import Card


class Player:
    """
    Represents a player in the game.
    """

    def __init__(self, name: str, initial_chips: int = 1000):
        self.name = name
        self.hand: list[Card] = []
        self.chips = initial_chips
        self.current_bet_in_round = 0 # Chips committed in the current betting round
        self.has_folded = False
        self.is_all_in = False

    def __repr__(self):
        return f"Player({self.name}, Chips: {self.chips})"

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

    def bet(self, amount: int) -> int:
        """
        Player places a bet. Returns the actual amount bet.
        """
        if amount < 0:
            raise ValueError("Bet amount cannot be negative.")

        actual_bet = min(amount, self.chips) # Cannot bet more than available chips
        self.chips -= actual_bet
        self.current_bet_in_round += actual_bet

        if self.chips == 0:
            self.is_all_in = True

        return actual_bet

    def add_chips(self, amount: int):
        """
        Adds chips to the player's stack.
        """
        if amount < 0:
            raise ValueError("Amount to add cannot be negative.")
        self.chips += amount

    def reset_bet_for_new_round(self):
        """
        Resets the player's bet for a new betting round.
        """
        self.current_bet_in_round = 0
        self.has_folded = False
        self.is_all_in = False