
from fastapi import FastAPI, HTTPException
from .texas_holdem.game import Game

app = FastAPI()

games: dict[str, Game] = {}


@app.post("/games/{game_id}")
def create_game(game_id: str, player_names: list[str]):
    """
    Creates a new game with the given ID and players.
    """
    if game_id in games:
        raise HTTPException(status_code=400, detail="Game already exists.")
    if len(player_names) < 2 or len(player_names) > 9:
        raise HTTPException(
            status_code=400, detail="A game must have between 2 and 9 players."
        )
    game = Game(player_names)
    games[game_id] = game
    return {"message": f"Game {game_id} created."}


@app.get("/games/{game_id}")
def get_game_state(game_id: str):
    """
    Retrieves the current state of the specified game.
    """
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found.")
    return games[game_id].get_game_state()


@app.post("/games/{game_id}/deal")
def deal_cards(game_id: str):
    """
    Deals cards in the specified game according to the game phase.
    """
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found.")

    game = games[game_id]

    if not game.players[0].hand:  # Pre-flop
        game.deal_hole_cards()
        return {"message": "Hole cards dealt."}
    elif len(game.community_cards) == 0:  # Flop
        game.deal_flop()
        return {"message": "Flop dealt."}
    elif len(game.community_cards) == 3:  # Turn
        game.deal_turn()
        return {"message": "Turn dealt."}
    elif len(game.community_cards) == 4:  # River
        game.deal_river()
        return {"message": "River dealt."}
    else:
        return {"message": "All cards have been dealt."}
