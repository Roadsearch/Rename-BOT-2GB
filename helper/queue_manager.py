"""
helper/queue_manager.py
File d'attente par utilisateur — création lazy des primitives asyncio
pour éviter le problème "no current event loop" au niveau module.
"""
import asyncio
import logging

logger = logging.getLogger(__name__)

MAX_PARALLEL = 3  # fichiers traités en parallèle sur tout le bot

_global_sem: asyncio.Semaphore | None = None
_user_locks: dict[int, asyncio.Lock]  = {}


def _sem() -> asyncio.Semaphore:
    """Crée le sémaphore global au premier appel (dans le bon event loop)."""
    global _global_sem
    if _global_sem is None:
        _global_sem = asyncio.Semaphore(MAX_PARALLEL)
    return _global_sem


def _lock(user_id: int) -> asyncio.Lock:
    """Crée le verrou utilisateur s'il n'existe pas encore."""
    if user_id not in _user_locks:
        _user_locks[user_id] = asyncio.Lock()
    return _user_locks[user_id]


async def acquire(user_id: int):
    """Acquiert le verrou utilisateur + le sémaphore global."""
    lock = _lock(user_id)
    if lock.locked():
        raise RuntimeError("already_busy")
    await lock.acquire()
    await _sem().acquire()
    logger.debug(f"[Queue] Slot acquis pour {user_id}")


def release(user_id: int):
    """Libère le verrou utilisateur + le sémaphore global."""
    lock = _lock(user_id)
    if lock.locked():
        lock.release()
    try:
        _sem().release()
    except ValueError:
        pass  # déjà libéré
    logger.debug(f"[Queue] Slot libéré pour {user_id}")
