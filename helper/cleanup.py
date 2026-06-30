"""
helper/cleanup.py
Nettoyage garanti du dossier downloads/ même en cas de crash.
"""
import os
import glob
import logging

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads/"


def cleanup_files(*paths: str):
    """Supprime les fichiers passés en argument, silencieusement."""
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
                logger.debug(f"[Cleanup] Supprimé : {path}")
            except Exception as e:
                logger.warning(f"[Cleanup] Impossible de supprimer {path} : {e}")


def cleanup_user_files(user_id: int):
    """Supprime tous les fichiers temporaires d'un utilisateur."""
    pattern = os.path.join(DOWNLOAD_DIR, f"{user_id}_*")
    for f in glob.glob(pattern):
        cleanup_files(f)


def cleanup_all():
    """Vide entièrement le dossier downloads/ au démarrage."""
    for f in glob.glob(os.path.join(DOWNLOAD_DIR, "*")):
        cleanup_files(f)
    logger.info("[Cleanup] Dossier downloads/ nettoyé au démarrage")
