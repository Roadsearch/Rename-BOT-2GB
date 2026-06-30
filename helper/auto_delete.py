"""
helper/auto_delete.py
Auto-suppression des messages du bot après un délai configurable.
"""
import asyncio
import logging
from pyrogram.types import Message

logger = logging.getLogger(__name__)

# Délai par défaut : 5 minutes (modifiable)
DEFAULT_DELAY = 300


async def auto_delete(msg: Message, delay: int = DEFAULT_DELAY):
    """
    Supprime le message après `delay` secondes.
    À appeler avec asyncio.create_task() pour ne pas bloquer.
    """
    await asyncio.sleep(delay)
    try:
        await msg.delete()
        logger.debug(f"[AutoDelete] Message {msg.id} supprimé après {delay}s")
    except Exception as e:
        logger.debug(f"[AutoDelete] Impossible de supprimer {msg.id} : {e}")


def schedule_delete(msg: Message, delay: int = DEFAULT_DELAY):
    """Lance la suppression en arrière-plan sans bloquer."""
    asyncio.create_task(auto_delete(msg, delay))
