"""
helper/flood_control.py
Anti-flood : limite le nombre de requêtes par utilisateur.
"""
import time
import logging

logger = logging.getLogger(__name__)

# {user_id: [timestamp, timestamp, ...]}
_history: dict[int, list[float]] = {}

# Paramètres : max 5 fichiers par fenêtre de 60 secondes
MAX_REQUESTS = 5
WINDOW_SEC   = 60


def is_flood(user_id: int) -> bool:
    """Retourne True si l'utilisateur dépasse la limite."""
    now = time.time()
    timestamps = _history.get(user_id, [])

    # Nettoie les timestamps hors fenêtre
    timestamps = [t for t in timestamps if now - t < WINDOW_SEC]
    _history[user_id] = timestamps

    if len(timestamps) >= MAX_REQUESTS:
        logger.warning(f"[Flood] Utilisateur {user_id} bloqué ({len(timestamps)} requêtes/{WINDOW_SEC}s)")
        return True

    _history[user_id].append(now)
    return False


def remaining_wait(user_id: int) -> int:
    """Retourne le nombre de secondes à attendre avant la prochaine requête."""
    now = time.time()
    timestamps = _history.get(user_id, [])
    timestamps = [t for t in timestamps if now - t < WINDOW_SEC]
    if not timestamps:
        return 0
    oldest = min(timestamps)
    return max(0, int(WINDOW_SEC - (now - oldest)))
