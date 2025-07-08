
from collections import Counter
from enum import Enum
from typing import List, Tuple

from .card import Card, Rank, Suit


class HandRank(Enum):
    ROYAL_FLUSH = 10
    STRAIGHT_FLUSH = 9
    FOUR_OF_A_KIND = 8
    FULL_HOUSE = 7
    FLUSH = 6
    STRAIGHT = 5
    THREE_OF_A_KIND = 4
    TWO_PAIR = 3
    ONE_PAIR = 2
    HIGH_CARD = 1


def get_numerical_rank_value(rank: Rank) -> int:
    """
    Returns the numerical value of a card rank (Ace can be 14).
    """
    if rank == Rank.ACE:
        return 14
    elif rank == Rank.KING:
        return 13
    elif rank == Rank.QUEEN:
        return 12
    elif rank == Rank.JACK:
        return 11
    elif rank == Rank.TEN:
        return 10
    else:
        return int(rank.value)


def get_rank_counts(cards: List[Card]) -> Counter:
    """
    Returns a Counter of card ranks.
    """
    return Counter([card.rank for card in cards])


def get_suit_counts(cards: List[Card]) -> Counter:
    """
    Returns a Counter of card suits.
    """
    return Counter([card.suit for card in cards])


def get_highest_cards(cards: List[Card], count: int) -> List[Card]:
    """
    Returns the highest 'count' cards from a list, sorted by numerical rank descending.
    """
    return sorted(cards, key=lambda card: get_numerical_rank_value(card.rank), reverse=True)[:count]


def get_straight_cards_from_numerical_ranks(all_cards: List[Card], straight_numerical_ranks: List[int]) -> List[Card]:
    """
    Given all available cards and the numerical ranks that form a straight,
    reconstruct the 5 actual Card objects.
    """
    straight_cards = []
    # Create a mutable copy of all_cards to remove cards as they are used
    available_cards = list(all_cards)

    for target_num_rank in straight_numerical_ranks:
        found_card = False
        for i, card in enumerate(available_cards):
            if card is None: # Card already used
                continue

            card_num_val = get_numerical_rank_value(card.rank)
            # Handle Ace as 1 for A-5 straight
            if card.rank == Rank.ACE and target_num_rank == 1:
                straight_cards.append(card)
                available_cards[i] = None # Mark as used
                found_card = True
                break
            elif card_num_val == target_num_rank:
                straight_cards.append(card)
                available_cards[i] = None # Mark as used
                found_card = True
                break
        if not found_card:
            # This should ideally not happen if straight_numerical_ranks is valid
            # and derived from the available cards.
            return []
    return sorted(straight_cards, key=lambda c: get_numerical_rank_value(c.rank), reverse=True)


def find_straight_cards(cards: List[Card]) -> List[Card] | None:
    """
    Finds if a straight exists within the given cards and returns the 5 cards forming it.
    Handles Ace as both high (14) and low (1).
    """
    # Get unique numerical ranks from the cards, handling Ace as both 1 and 14
    unique_numerical_ranks = set()
    for card in cards:
        unique_numerical_ranks.add(get_numerical_rank_value(card.rank))
        if card.rank == Rank.ACE:
            unique_numerical_ranks.add(1)  # For Ace-low straight (A,2,3,4,5)

    sorted_unique_ranks = sorted(list(unique_numerical_ranks), reverse=True)

    # Check for 5 consecutive ranks
    for i in range(len(sorted_unique_ranks) - 4):
        # Check if the current 5 ranks form a consecutive sequence
        is_consecutive = True
        for j in range(4):
            if sorted_unique_ranks[i + j] - sorted_unique_ranks[i + j + 1] != 1:
                is_consecutive = False
                break

        if is_consecutive:
            straight_numerical_ranks = sorted_unique_ranks[i : i + 5]
            # Reconstruct the actual Card objects that form this straight
            # Pass the original cards to ensure we pick from the available ones
            return get_straight_cards_from_numerical_ranks(cards, straight_numerical_ranks)
    return None


def get_hand_rank_and_kickers(seven_cards: List[Card]) -> Tuple[HandRank, List[Card]]:
    """
    Evaluates a 7-card hand and returns its poker rank and the best 5 cards forming that hand.
    """
    # Sort cards by numerical rank (descending) for easier evaluation
    sorted_cards = sorted(seven_cards, key=lambda card: get_numerical_rank_value(card.rank), reverse=True)

    # --- Check for Royal Flush / Straight Flush / Flush ---
    flush_suit = None
    for suit in Suit:
        suited_cards = [card for card in sorted_cards if card.suit == suit]
        if len(suited_cards) >= 5:
            flush_suit = suit
            break

    if flush_suit:
        flush_cards = [card for card in sorted_cards if card.suit == flush_suit]
        straight_in_flush = find_straight_cards(flush_cards)
        if straight_in_flush and len(straight_in_flush) == 5: # Ensure 5 cards are returned for straight
            # Check for Royal Flush (A, K, Q, J, 10 of same suit)
            if (get_numerical_rank_value(straight_in_flush[0].rank) == 14 and
                get_numerical_rank_value(straight_in_flush[1].rank) == 13 and
                get_numerical_rank_value(straight_in_flush[2].rank) == 12 and
                get_numerical_rank_value(straight_in_flush[3].rank) == 11 and
                get_numerical_rank_value(straight_in_flush[4].rank) == 10):
                return HandRank.ROYAL_FLUSH, straight_in_flush
            else:
                return HandRank.STRAIGHT_FLUSH, straight_in_flush
        # If no straight, it's a Flush
        return HandRank.FLUSH, get_highest_cards(flush_cards, 5)

    # --- Check for Four of a Kind, Full House, Three of a Kind, Two Pair, One Pair ---
    rank_counts = get_rank_counts(sorted_cards)
    # Sort ranks by count (descending) then by numerical value (descending)
    # This ensures we prioritize higher counts and then higher ranks for ties
    sorted_ranks_by_count = sorted(rank_counts.items(), key=lambda item: (item[1], get_numerical_rank_value(item[0])), reverse=True)

    # Extract ranks based on counts
    fours = [rank for rank, count in sorted_ranks_by_count if count == 4]
    threes = [rank for rank, count in sorted_ranks_by_count if count == 3]
    pairs = [rank for rank, count in sorted_ranks_by_count if count == 2]

    if fours:
        # Four of a Kind
        four_of_a_kind_rank = fours[0]
        hand_cards = [card for card in sorted_cards if card.rank == four_of_a_kind_rank]
        remaining_cards = [card for card in sorted_cards if card.rank != four_of_a_kind_rank]
        kicker = get_highest_cards(remaining_cards, 1)
        return HandRank.FOUR_OF_A_KIND, hand_cards + kicker
    elif threes and pairs:
        # Full House
        three_rank = threes[0]
        # Find the best pair for the full house.
        # It could be from the 'pairs' list or a second 'three-of-a-kind' acting as a pair.
        best_pair_rank = None
        if pairs:
            best_pair_rank = pairs[0]

        if len(threes) > 1:  # If there's a second three-of-a-kind
            # Ensure we pick the highest rank for the pair part of the full house
            if best_pair_rank is None or get_numerical_rank_value(threes[1]) > get_numerical_rank_value(best_pair_rank):
                best_pair_rank = threes[1]  # Use the second three-of-a-kind as the pair

        hand_cards = [card for card in sorted_cards if card.rank == three_rank]
        # Add two cards for the pair
        # Ensure we pick unique cards for the pair part
        pair_cards_added = 0
        for card in sorted_cards:
            if card.rank == best_pair_rank and card not in hand_cards and pair_cards_added < 2:
                hand_cards.append(card)
                pair_cards_added += 1
        return HandRank.FULL_HOUSE, hand_cards
    elif threes:
        # Three of a Kind
        three_of_a_kind_rank = threes[0]
        hand_cards = [card for card in sorted_cards if card.rank == three_of_a_kind_rank]
        remaining_cards = [card for card in sorted_cards if card.rank != three_of_a_kind_rank]
        kickers = get_highest_cards(remaining_cards, 2)
        return HandRank.THREE_OF_A_KIND, hand_cards + kickers
    elif len(pairs) >= 2:
        # Two Pair
        high_pair_rank = pairs[0]
        low_pair_rank = pairs[1]
        hand_cards = [card for card in sorted_cards if card.rank == high_pair_rank]
        hand_cards.extend([card for card in sorted_cards if card.rank == low_pair_rank])
        remaining_cards = [card for card in sorted_cards if card.rank != high_pair_rank and card.rank != low_pair_rank]
        kicker = get_highest_cards(remaining_cards, 1)
        return HandRank.TWO_PAIR, hand_cards + kicker
    elif len(pairs) == 1:
        # One Pair
        pair_rank = pairs[0]
        hand_cards = [card for card in sorted_cards if card.rank == pair_rank]
        remaining_cards = [card for card in sorted_cards if card.rank != pair_rank]
        kickers = get_highest_cards(remaining_cards, 3)
        return HandRank.ONE_PAIR, hand_cards + kickers

    # --- Check for Straight ---
    straight_cards = find_straight_cards(sorted_cards)
    if straight_cards and len(straight_cards) == 5: # Ensure 5 cards are returned for straight
        return HandRank.STRAIGHT, straight_cards

    # --- High Card ---
    return HandRank.HIGH_CARD, get_highest_cards(sorted_cards, 5)


def compare_hands(hand1_cards: List[Card], hand2_cards: List[Card]) -> int:
    """
    Compares two 7-card hands.
    Returns 1 if hand1 wins, -1 if hand2 wins, 0 if tie.
    """
    rank1, best_five_1 = get_hand_rank_and_kickers(hand1_cards)
    rank2, best_five_2 = get_hand_rank_and_kickers(hand2_cards)

    if rank1.value > rank2.value:
        return 1
    elif rank1.value < rank2.value:
        return -1
    else:
        # Ranks are equal, compare the best five cards
        # Sort by numerical rank (descending)
        sorted_best_five_1 = sorted(best_five_1, key=lambda card: get_numerical_rank_value(card.rank), reverse=True)
        sorted_best_five_2 = sorted(best_five_2, key=lambda card: get_numerical_rank_value(card.rank), reverse=True)

        for i in range(5):  # Compare up to 5 cards
            # Ensure both lists have at least 5 cards, though they should if logic is correct
            if i >= len(sorted_best_five_1) or i >= len(sorted_best_five_2):
                # This case indicates an issue in get_hand_rank_and_kickers if it returns less than 5 cards for a valid hand
                # For now, assume it returns 5 cards. If not, this needs more robust handling.
                break

            val1 = get_numerical_rank_value(sorted_best_five_1[i].rank)
            val2 = get_numerical_rank_value(sorted_best_five_2[i].rank)
            if val1 > val2:
                return 1
            elif val1 < val2:
                return -1
        return 0  # All 5 cards are equal, it's a tie
