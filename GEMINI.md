# Texas Hold'em Backend

This project implements a basic Texas Hold'em poker game backend using Python and FastAPI. It includes core game logic (cards, deck, players, game flow) and a RESTful API for interaction. Automated tests are set up using Pytest and GitHub Actions.

## Project Structure

```
.
├── .github/                 # GitHub Actions workflows
│   └── workflows/
│       └── ci.yml           # CI/CD pipeline for running tests
├── src/
│   ├── backend/             # All backend-related code
│   │   ├── texas_holdem/    # Core Texas Hold'em game logic
│   │   │   ├── __init__.py
│   │   │   ├── card.py      # Card definition (Suit, Rank, Card classes)
│   │   │   ├── deck.py      # Deck management (shuffle, deal)
│   │   │   ├── player.py    # Player definition (name, hand)
│   │   │   └── game.py      # Game logic (dealing, community cards)
│   │   ├── main.py          # FastAPI application entry point
│   │   └── requirements.txt # Python dependencies for the backend
│   └── __init__.py          # Makes 'src' a Python package
├── tests/                   # Unit tests for the game logic
│   ├── __init__.py
│   ├── test_card.py
│   ├── test_deck.py
│   ├── test_game.py
│   └── test_player.py
├── .gitignore               # Specifies intentionally untracked files to ignore
└── GEMINI.md                # This file
```

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd TexasHoldem
    ```

2.  **Create and activate a Conda environment** (recommended):
    ```bash
    conda create --name texas_holdem_env python=3.10 -y
    conda activate texas_holdem_env
    ```
    *(If you prefer `venv` or `virtualenv`, you can use those instead.)*

3.  **Install dependencies:**
    ```bash
    pip install -r src/backend/requirements.txt
    ```

## Running the Backend Server

To start the FastAPI development server:

```bash
uvicorn src.backend.main:app --reload
```

The API will be accessible at `http://127.0.0.1:8000`.

## Running with Docker

You can containerize and run the application using Docker and Docker Compose.

1.  **Build the Docker image:**
    ```bash
    docker-compose build
    ```

2.  **Run the container:**
    ```bash
    docker-compose up
    ```
    The application will be available at `http://localhost:8000`. The `--reload` flag is enabled in `docker-compose.yml` for development, so changes to the code will automatically restart the server inside the container.

3.  **Run tests in Docker (optional):**
    ```bash
    docker-compose run backend pytest
    ```

## API Endpoints

*   **`POST /games/{game_id}`**: Create a new game.
    *   **Body:** `["Player1Name", "Player2Name", ...]`
*   **`GET /games/{game_id}`**: Get the current state of a game.
*   **`POST /games/{game_id}/deal`**: Deal cards based on the current game phase (hole cards, flop, turn, river). After the river card is dealt, the backend will automatically determine and return the winner based on poker hand rankings.

## Running the Frontend

To run the frontend application:

1.  **Navigate to the frontend directory:**
    ```bash
    cd src/frontend
    ```

2.  **Install frontend dependencies:**
    ```bash
    npm install
    ```

3.  **Start the development server:**
    ```bash
    npm run dev
    ```
    The frontend application will typically be available at `http://localhost:5173` (or another port if 5173 is in use).

## Running Tests

To run the unit tests:

```bash
export PYTHONPATH=./src && pytest
```

## Automated Testing (GitHub Actions)

This project is configured with GitHub Actions. Any push to the `main` branch or pull request targeting `main` will automatically trigger the test suite defined in `.github/workflows/ci.yml`. This ensures that all code changes are validated against the existing tests.
