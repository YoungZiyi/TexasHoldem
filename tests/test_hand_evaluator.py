
import pytest
from src.backend.texas_holdem.card import Card, Suit, Rank
from src.backend.texas_holdem.hand_evaluator import get_hand_rank_and_kickers, compare_hands, HandRank


def create_cards(card_strings: list[str]) -> list[Card]:
    """
    Helper to create Card objects from string representations (e.g., "AS" for Ace of Spades).
    """
    cards = []
    for s in card_strings:
        rank_str = s[:-1]
        suit_str = s[-1]

        rank = None
        for r in Rank:
            if r.value == rank_str:
                rank = r
                break
        if rank is None: # Handle 10
            if rank_str == "10":
                rank = Rank.TEN
            else:
                raise ValueError(f"Invalid rank string: {rank_str}")

        suit = None
        if suit_str == "S":
            suit = Suit.SPADES
        elif suit_str == "H":
            suit = Suit.HEARTS
        elif suit_str == "D":
            suit = Suit.DIAMONDS
        elif suit_str == "C":
            suit = Suit.CLUBS
        else:
            raise ValueError(f"Invalid suit string: {suit_str}")
        cards.append(Card(suit, rank))
    return cards


# Test cases for get_hand_rank_and_kickers
@pytest.mark.parametrize(
    "seven_cards_str, expected_rank, expected_kickers_str",
    [
        # High Card
        (["2S", "3H", "5D", "7C", "9S", "JH", "QH"], HandRank.HIGH_CARD, ["QH", "JH", "9S", "7C", "5D"]),
        (["2S", "3H", "5D", "7C", "9S", "JH", "AH"], HandRank.HIGH_CARD, ["AH", "JH", "9S", "7C", "5D"]),
        # One Pair
        (["2S", "2H", "5D", "7C", "9S", "JH", "QH"], HandRank.ONE_PAIR, ["2S", "2H", "QH", "JH", "9S"]),
        (["AS", "AH", "5D", "7C", "9S", "JH", "QH"], HandRank.ONE_PAIR, ["AS", "AH", "QH", "JH", "9S"]),
        # Two Pair
        (["2S", "2H", "3D", "3C", "9S", "JH", "QH"], HandRank.TWO_PAIR, ["3D", "3C", "2S", "2H", "QH"]),
        (["AS", "AH", "KD", "KC", "5S", "7H", "9D"], HandRank.TWO_PAIR, ["AS", "AH", "KD", "KC", "9D"]),
        # Three of a Kind
        (["2S", "2H", "2D", "7C", "9S", "JH", "QH"], HandRank.THREE_OF_A_KIND, ["2S", "2H", "2D", "QH", "JH"]),
        (["AS", "AH", "AD", "7C", "9S", "JH", "QH"], HandRank.THREE_OF_A_KIND, ["AS", "AH", "AD", "QH", "JH"]),
        # Straight
        (["2S", "3H", "4D", "5C", "6S", "JH", "QH"], HandRank.STRAIGHT, ["6S", "5C", "4D", "3H", "2S"]),
        (["AS", "2H", "3D", "4C", "5S", "JH", "QH"], HandRank.STRAIGHT, ["5S", "4C", "3D", "2H", "AS"]),
        (["10S", "JH", "QD", "KC", "AS", "2H", "3D"], HandRank.STRAIGHT, ["AS", "KC", "QD", "JH", "10S"]),
        # Flush
        (["2S", "4S", "6S", "8S", "10S", "JH", "QH"], HandRank.FLUSH, ["10S", "8S", "6S", "4S", "2S"]),
        (["AS", "KS", "QS", "JS", "9S", "2H", "3D"], HandRank.FLUSH, ["AS", "KS", "QS", "JS", "9S"]),
        # Full House
        (["2S", "2H", "2D", "3C", "3S", "9H", "QH"], HandRank.FULL_HOUSE, ["2S", "2H", "2D", "3C", "3S"]),
        (["AS", "AH", "AD", "KC", "KS", "9H", "QH"], HandRank.FULL_HOUSE, ["AS", "AH", "AD", "KC", "KS"]),
        # Four of a Kind
        (["2S", "2H", "2D", "2C", "9S", "JH", "QH"], HandRank.FOUR_OF_A_KIND, ["2S", "2H", "2D", "2C", "QH"]),
        (["AS", "AH", "AD", "AC", "9S", "JH", "QH"], HandRank.FOUR_OF_A_KIND, ["AS", "AH", "AD", "AC", "QH"]),
        # Straight Flush
        (["2S", "3S", "4S", "5S", "6S", "JH", "QH"], HandRank.STRAIGHT_FLUSH, ["6S", "5S", "4S", "3S", "2S"]),
        (["AS", "2S", "3S", "4S", "5S", "JH", "QH"], HandRank.STRAIGHT_FLUSH, ["5S", "4S", "3S", "2S", "AS"]),
        # Royal Flush
        (["10S", "JS", "QS", "KS", "AS", "2H", "3D"], HandRank.ROYAL_FLUSH, ["AS", "KS", "QS", "JS", "10S"]),
    ]
)
def test_get_hand_rank_and_kickers(seven_cards_str, expected_rank, expected_kickers_str):
    seven_cards = create_cards(seven_cards_str)
    expected_kickers = create_cards(expected_kickers_str)
    rank, kickers = get_hand_rank_and_kickers(seven_cards)
    assert rank == expected_rank
    # Compare kickers by their string representation for simplicity
    assert sorted([repr(c) for c in kickers]) == sorted([repr(c) for c in expected_kickers])


# Test cases for compare_hands
@pytest.mark.parametrize(
    "hand1_str, hand2_str, expected_result",
    [
        # Different Ranks
        (["AS", "AH", "2S", "3H", "4D", "5C", "6S"], ["KS", "KH", "2S", "3H", "4D", "5C", "7S"], 1), # Pair A vs Pair K
        (["2S", "3H", "4D", "5C", "6S", "7H", "8D"], ["AS", "AH", "AD", "2C", "3S", "4H", "5D"], 1), # Straight vs Three of a Kind
        (["AS", "KS", "QS", "JS", "10S", "2H", "3D"], ["AS", "AH", "AD", "AC", "2S", "3H", "4D"], 1), # Royal Flush vs Four of a Kind

        # Same Ranks, Different Kickers
        (["AS", "AH", "KD", "QC", "9S", "7H", "5D"], ["AS", "AH", "JD", "10C", "9S", "7H", "5D"], 1), # Pair A, K kicker vs Pair A, J kicker
        (["AS", "AH", "AD", "2C", "3S", "4H", "5D"], ["KS", "KH", "KD", "2C", "3S", "4H", "5D"], 1), # Three A vs Three K
        (["2S", "3H", "4D", "5C", "6S", "7H", "8D"], ["2S", "3H", "4D", "5C", "6S", "7H", "9D"], 1), # Straight (8 high) vs Straight (7 high)

        # Tie
        (["AS", "AH", "KD", "QC", "9S", "7H", "5D"], ["AS", "AH", "KD", "QC", "9S", "7H", "5D"], 0), # Exact same hand
        (["AS", "AH", "KD", "QC", "9S", "7H", "5D"], ["AD", "AC", "KH", "QH", "9C", "7S", "5H"], 0), # Same hand, different suits
    ]
)
def test_compare_hands(hand1_str, hand2_str, expected_result):
    hand1_cards = create_cards(hand1_str)
    hand2_cards = create_cards(hand2_str)
    result = compare_hands(hand1_cards, hand2_cards)
    assert result == expected_result
