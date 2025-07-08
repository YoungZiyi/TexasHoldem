
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .texas_holdem.game import Game

app = FastAPI()

# CORS middleware to allow frontend to communicate with backend
origins = [
    "http://localhost",
    "http://localhost:5173",  # Frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

games: dict[str, Game] = {}


class PlayerAction(BaseModel):
    player_name: str
    seat_index: int | None = None


class BettingAction(BaseModel):
    player_name: str
    amount: int | None = None  # For bet/raise actions


@app.post("/games/{game_id}")
def create_game(game_id: str):
    """
    Creates a new game with the given ID.
    """
    if game_id in games:
        raise HTTPException(status_code=400, detail="Game already exists.")
    game = Game(game_id)
    games[game_id] = game
    return {"message": f"Game {game_id} created."}


@app.post("/games/{game_id}/join")
def join_game(game_id: str, action: PlayerAction):
    """
    Allows a player to join a specific seat in the game.
    """
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found.")

    game = games[game_id]
    if action.seat_index is None:
        raise HTTPException(status_code=400, detail="Seat index is required to join.")

    if game.game_started:
        raise HTTPException(status_code=400, detail="Game already in progress. Please wait for the next round.")

    success = game.join_seat(action.player_name, action.seat_index)
    if not success:
        raise HTTPException(status_code=400, detail="Could not join seat. It might be occupied or player already in game.")
    return {"message": f"Player {action.player_name} joined seat {action.seat_index} in game {game_id}."}


@app.post("/games/{game_id}/leave")
def leave_game(game_id: str, action: PlayerAction):
    """
    Allows a player to leave their seat in the game.
    """
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found.")

    game = games[game_id]
    success = game.leave_seat(action.player_name)
    if not success:
        raise HTTPException(status_code=400, detail="Player not found in any seat.")
    return {"message": f"Player {action.player_name} left game {game_id}."}


@app.get("/games/{game_id}")
def get_game_state(game_id: str):
    """
    Retrieves the current state of the specified game.
    """
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found.")
    return games[game_id].get_game_state()


@app.post("/games/{game_id}/start")
def start_game_round(game_id: str):
    """
    Starts a new round of the game.
    """
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found.")
    game = games[game_id]
    try:
        game.start_new_round()
        return {"message": "New round started. Hole cards dealt."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/games/{game_id}/deal_community_cards")
def deal_community_cards(game_id: str):
    """
    Deals community cards (Flop, Turn, or River).
    """
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found.")
    game = games[game_id]

    if game.betting_round != "" and game.current_player_index != -1: # Betting round not finished
        raise HTTPException(status_code=400, detail="Current betting round not finished.")

    if len(game.community_cards) == 0:  # Flop
        game.deal_flop()
        return {"message": "Flop dealt."}
    elif len(game.community_cards) == 3:  # Turn
        game.deal_turn()
        return {"message": "Turn dealt."}
    elif len(game.community_cards) == 4:  # River
        game.deal_river()
        return {"message": "River dealt."}
    elif len(game.community_cards) == 5: # All community cards dealt, end round
        game.end_round_and_determine_winner()
        return {"message": "All community cards dealt. Winner determined."}
    else:
        raise HTTPException(status_code=400, detail="Invalid state for dealing community cards.")


@app.post("/games/{game_id}/action/bet")
def player_bet(game_id: str, action: BettingAction):
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found.")
    game = games[game_id]
    try:
        game.action_bet(action.player_name, action.amount)
        return {"message": f"Player {action.player_name} bet {action.amount}."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/games/{game_id}/action/call")
def player_call(game_id: str, action: BettingAction):
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found.")
    game = games[game_id]
    try:
        game.action_call(action.player_name)
        return {"message": f"Player {action.player_name} called."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/games/{game_id}/action/raise")
def player_raise(game_id: str, action: BettingAction):
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found.")
    game = games[game_id]
    try:
        game.action_raise(action.player_name, action.amount)
        return {"message": f"Player {action.player_name} raised to {action.amount}."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/games/{game_id}/action/fold")
def player_fold(game_id: str, action: BettingAction):
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found.")
    game = games[game_id]
    try:
        game.action_fold(action.player_name)
        return {"message": f"Player {action.player_name} folded."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/games/{game_id}/action/check")
def player_check(game_id: str, action: BettingAction):
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found.")
    game = games[game_id]
    try:
        game.action_check(action.player_name)
        return {"message": f"Player {action.player_name} checked."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/games/{game_id}/reset")
def reset_game_round(game_id: str):
    """
    Resets the game round, keeping players in their seats.
    """
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found.")
    game = games[game_id]
    game.reset_game_state_for_new_round()
    return {"message": f"Game {game_id} round reset."}
