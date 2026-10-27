"""
games package - Registry of supported game profiles
"""
from typing import Dict, List, Optional
from src.games.base import BaseGame
from src.games.overwatch import OverwatchGame
from src.games.deadlock import DeadlockGame

_GAMES: Dict[str, BaseGame] = {}


def init_games() -> Dict[str, BaseGame]:
    global _GAMES
    if not _GAMES:
        ow = OverwatchGame()
        dl = DeadlockGame()
        _GAMES = {
            ow.game_id: ow,
            dl.game_id: dl,
        }
    return _GAMES


def get_game(game_id: str) -> Optional[BaseGame]:
    games = init_games()
    return games.get(game_id)


def get_all_games() -> List[BaseGame]:
    return list(init_games().values())


__all__ = [
    "BaseGame",
    "OverwatchGame",
    "DeadlockGame",
    "init_games",
    "get_game",
    "get_all_games",
]
