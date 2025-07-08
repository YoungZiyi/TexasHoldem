import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE_URL = 'http://localhost:8000'; // Our FastAPI backend

function App() {
  const [playerName, setPlayerName] = useState(localStorage.getItem('texasHoldemPlayerName') || '');
  const [inputPlayerName, setInputPlayerName] = useState('');
  const [gameId, setGameId] = useState('my_poker_game'); // Default game ID for simplicity
  const [gameState, setGameState] = useState(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [playerSeatIndex, setPlayerSeatIndex] = useState(null); // Track current player's seat

  // Effect to load player name from localStorage on initial render
  useEffect(() => {
    if (playerName) {
      setInputPlayerName(playerName);
      // Try to fetch game state if player name is already set and gameId exists
      fetchGameState(gameId);
    }
  }, [playerName, gameId]);

  // Effect to periodically refresh game state if player is in a game
  useEffect(() => {
    let interval;
    if (playerName && gameId) {
      interval = setInterval(() => {
        fetchGameState(gameId);
      }, 3000); // Refresh every 3 seconds
    }
    return () => clearInterval(interval); // Cleanup on unmount or dependency change
  }, [playerName, gameId]);


  const handleSetPlayerName = () => {
    if (inputPlayerName.trim()) {
      setPlayerName(inputPlayerName.trim());
      localStorage.setItem('texasHoldemPlayerName', inputPlayerName.trim());
      setMessage(`Welcome, ${inputPlayerName.trim()}!`);
    } else {
      setError('Please enter a valid player name.');
    }
  };

  const fetchGameState = async (id) => {
    try {
      const response = await fetch(`${API_BASE_URL}/games/${id}`);
      if (!response.ok) {
        if (response.status === 404) {
          setGameState(null); // Game not found, clear state
          setMessage(`Game ${id} does not exist. Create it first.`);
          return;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setGameState(data);
      setMessage('');

      // Update player's current seat index
      const currentPlayerSeat = data.seats.find(seat => seat.name === playerName);
      if (currentPlayerSeat) {
        setPlayerSeatIndex(currentPlayerSeat.seat_index);
      } else {
        setPlayerSeatIndex(null); // Player not in any seat
      }

    } catch (e) {
      setError(`Failed to fetch game state: ${e.message}`);
      setGameState(null);
    }
  };

  const handleCreateGame = async () => {
    setError('');
    setMessage('');
    if (!gameId) {
      setError('Please enter a Game ID.');
      return;
    }
    try {
      const response = await fetch(`${API_BASE_URL}/games/${gameId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || `HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setMessage(data.message);
      fetchGameState(gameId); // Fetch initial state after creation
    } catch (e) {
      setError(`Failed to create game: ${e.message}`);
    }
  };

  const handleJoinSeat = async (seatIndex) => {
    setError('');
    setMessage('');
    if (!playerName) {
      setError('Please set your player name first.');
      return;
    }
    try {
      const response = await fetch(`${API_BASE_URL}/games/${gameId}/join`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ player_name: playerName, seat_index: seatIndex }),
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || `HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setMessage(data.message);
      fetchGameState(gameId);
    } catch (e) {
      setError(`Failed to join seat: ${e.message}`);
    }
  };

  const handleLeaveSeat = async () => {
    setError('');
    setMessage('');
    if (!playerName) {
      setError('Player name not set.');
      return;
    }
    try {
      const response = await fetch(`${API_BASE_URL}/games/${gameId}/leave`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ player_name: playerName }),
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || `HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setMessage(data.message);
      fetchGameState(gameId);
    } catch (e) {
      setError(`Failed to leave seat: ${e.message}`);
    }
  };

  const handleDealCards = async () => {
    setError('');
    setMessage('');
    if (!gameId) {
      setError('Please enter a Game ID.');
      return;
    }
    try {
      const response = await fetch(`${API_BASE_URL}/games/${gameId}/deal`, {
        method: 'POST',
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || `HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setMessage(data.message);
      fetchGameState(gameId); // Update state after dealing
    } catch (e) {
      setError(`Failed to deal cards: ${e.message}`);
    }
  };

  const handleResetGameRound = async () => {
    setError('');
    setMessage('');
    if (!gameId) {
      setError('Please enter a Game ID.');
      return;
    }
    try {
      const response = await fetch(`${API_BASE_URL}/games/${gameId}/reset`, {
        method: 'POST',
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || `HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setMessage(data.message);
      fetchGameState(gameId); // Update state after reset
    } catch (e) {
      setError(`Failed to reset game round: ${e.message}`);
    }
  };

  if (!playerName) {
    return (
      <div className="App">
        <h1>Welcome to Texas Hold'em!</h1>
        <div className="player-name-input">
          <input
            type="text"
            placeholder="Enter your name"
            value={inputPlayerName}
            onChange={(e) => setInputPlayerName(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') handleSetPlayerName();
            }}
          />
          <button onClick={handleSetPlayerName}>Continue</button>
        </div>
        {error && <p className="error">{error}</p>}
      </div>
    );
  }

  return (
    <div className="App">
      <h1>Texas Hold'em Table</h1>
      <p className="current-player">Logged in as: <strong>{playerName}</strong></p>

      <div className="game-controls">
        <input
          type="text"
          placeholder="Game ID"
          value={gameId}
          onChange={(e) => setGameId(e.target.value)}
          disabled={gameState && gameState.game_id} // Disable if game exists
        />
        {!gameState && (
          <button onClick={handleCreateGame}>Create Game</button>
        )}
        {gameState && (
          <button onClick={() => fetchGameState(gameId)}>Refresh Game State</button>
        )}
      </div>

      {message && <p className="message">{message}</p>}
      {error && <p className="error">{error}</p>}

      {gameState && (
        <div className="game-table">
          <h2>Game ID: {gameState.game_id}</h2>
          {gameState.game_started && playerSeatIndex === null && (
            <p className="spectator-message">Game in progress. You are spectating. Join an empty seat for the next round!</p>
          )}
          {gameState.game_started && playerSeatIndex !== null && (
            <p className="in-game-message">Game in progress. You are playing!</p>
          )}
          {!gameState.game_started && (
            <p className="waiting-message">Waiting for players or next round to start.</p>
          )}

          <div className="seats-container">
            {Array.from({ length: 8 }).map((_, index) => {
              const seat = gameState.seats[index];
              const isOccupied = seat && seat.name;
              const isCurrentPlayer = isOccupied && seat.name === playerName;
              const canJoin = !isOccupied && !gameState.game_started && playerSeatIndex === null;
              const canLeave = isCurrentPlayer && !gameState.game_started; // Can only leave if game not started

              return (
                <div key={index} className={`seat ${isOccupied ? 'occupied' : 'empty'} ${isCurrentPlayer ? 'current-player-seat' : ''}`}>
                  <p className="seat-number">Seat {index + 1}</p>
                  {isOccupied ? (
                    <>
                      <p className="player-name">{seat.name}</p>
                      {isCurrentPlayer && (
                        <div className="player-hand-display">
                          {seat.hand.length > 0 ? (
                            seat.hand.map((card, cardIndex) => (
                              <span key={cardIndex} className="card">{card}</span>
                            ))
                          ) : (
                            <p>No cards</p>
                          )}
                        </div>
                      )}
                      {canLeave && (
                        <button onClick={handleLeaveSeat}>Leave</button>
                      )}
                    </>
                  ) : (
                    <>
                      <p>Empty</p>
                      {canJoin && (
                        <button onClick={() => handleJoinSeat(index)}>Join</button>
                      )}
                    </>
                  )}
                </div>
              );
            })}
          </div>

          <div className="community-cards">
            <h3>Community Cards:</h3>
            <div className="cards-container">
              {gameState.community_cards.length > 0 ? (
                gameState.community_cards.map((card, index) => (
                  <span key={index} className="card">{card}</span>
                ))
              ) : (
                <p>No community cards dealt yet.</p>
              )}
            </div>
          </div>

          <div className="game-actions">
            <button onClick={handleDealCards} disabled={gameState.game_started && gameState.community_cards.length === 5}>Deal Next Phase</button>
            <button onClick={handleResetGameRound}>Reset Round</button>
          </div>

          {gameState.winner && (
            <div className="winner-info">
              <h3>Winner: {gameState.winner.name}</h3>
              <p>Hand Rank: {gameState.winner.hand_rank}</p>
              <div className="cards-container">
                {gameState.winner.best_five_cards.map((card, index) => (
                  <span key={index} className="card">{card}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;