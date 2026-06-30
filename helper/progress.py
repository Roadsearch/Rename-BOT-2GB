"""
helper/progress.py
Barre de progression pro — utilisée partout dans le bot.

Rendu final dans Telegram :
╔══════════════════════════╗
║  ⬇️  Téléchargement...   ║
║                          ║
║  ████████████░░░░  68%   ║
║                          ║
║  📦  68.4 Mo / 100.2 Mo  ║
║  🚀  3.2 Mo/s            ║
║  ⏱️  Reste : 9s          ║
║  ⏳  Écoulé : 21s        ║
╚══════════════════════════╝
helper/progress.py
Barre de progression pro — utilisée partout dans le bot.
Correction : __call__ rendu synchrone pour la compatibilité absolue avec les callbacks de Pyrogram.
"""

import time
import logging
import asyncio
from pyrogram.types import Message

logger = logging.getLogger(__name__)

# ── Blocs Unicode pour la barre ───────────────────────────────────────────────
FULL  = "█"
EMPTY = "░"
BAR_LENGTH = 12   # nombre de blocs


def _human_size(num: float) -> str:
    for unit in ["o", "Ko", "Mo", "Go", "To"]:
        if abs(num) < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} To"


def _eta(seconds: float) -> str:
    seconds = int(seconds)
    if seconds <= 0:
        return "0s"
    if seconds < 60:
        return f"{seconds}s"
    m, s = divmod(seconds, 60)
    if m < 60:
        return f"{m}m {s:02d}s"
    h, m = divmod(m, 60)
    return f"{h}h {m:02d}m"


def _speed_label(bps: float) -> str:
    return _human_size(bps) + "/s"


def _build_bar(percent: float) -> str:
    filled = int(BAR_LENGTH * percent / 100)
    empty  = BAR_LENGTH - filled
    return FULL * filled + EMPTY * empty


# Emojis selon la phase
PHASE_EMOJI = {
    "download": "⬇️",
    "upload":   "⬆️",
    "extract":  "📂",
    "rename":   "✏️",
}

PHASE_LABEL = {
    "download": "Téléchargement",
    "upload":   "Upload",
    "extract":  "Extraction",
    "rename":   "Renommage",
}


def build_progress_text(
    current: int,
    total: int,
    elapsed: float,
    phase: str = "download",
    filename: str = "",
) -> str:
    """
    Construit le texte de progression formaté.
    """
    percent  = min(current * 100 / total, 100) if total else 0
    speed    = current / elapsed if elapsed > 0 else 0
    remaining = (total - current) / speed if speed > 0 else 0
    bar      = _build_bar(percent)
    emoji    = PHASE_EMOJI.get(phase, "⏳")
    label    = PHASE_LABEL.get(phase, phase.capitalize())

    # Ligne nom du fichier (tronquée à 35 chars)
    fname_line = ""
    if filename:
        name = filename if len(filename) <= 35 else "…" + filename[-33:]
        fname_line = f"📄 <code>{name}</code>\n\n"

    text = (
        f"{emoji} <b>{label}...</b>\n\n"
        f"{fname_line}"
        f"<code>[{bar}]</code> <b>{percent:.1f}%</b>\n\n"
        f"📦 <b>Taille :</b> {_human_size(current)} / {_human_size(total)}\n"
        f"🚀 <b>Vitesse :</b> {_speed_label(speed)}\n"
        f"⏱️ <b>Reste :</b> {_eta(remaining)}\n"
        f"⏳ <b>Écoulé :</b> {_eta(elapsed)}"
    )
    return text


class ProgressUpdater:
    """
    Classe réutilisable pour mettre à jour une barre de progression.
    Throttle : 1 mise à jour max toutes les UPDATE_INTERVAL secondes.
    """
    UPDATE_INTERVAL = 3.5  # Modifié à 3.5s pour respecter les limites de l'API Telegram

    def __init__(
        self,
        msg: Message,
        phase: str = "download",
        filename: str = "",
    ):
        self.msg       = msg
        self.phase     = phase
        self.filename  = filename
        self.start     = time.time()
        self._last_upd = 0.0

    def __call__(self, current: int, total: int):
        """
        Callback synchrone requis par Pyrogram pour progress=.
        Redirige l'affichage vers une tâche asynchrone en arrière-plan.
        """
        now = time.time()
        if now - self._last_upd < self.UPDATE_INTERVAL:
            return
        self._last_upd = now
        
        # Récupération de la boucle d'événements courante pour planifier l'édition du message
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.update_telegram(current, total, now))
        except Exception as e:
            logger.error(f"[Progress] Erreur lors de la planification : {e}")

    async def update_telegram(self, current: int, total: int, now: float):
        """Effectue la véritable modification asynchrone du message Telegram."""
        elapsed = now - self.start
        text = build_progress_text(
            current, total, elapsed,
            phase=self.phase,
            filename=self.filename,
        )
        try:
            await self.msg.edit_text(text, parse_mode="html")
        except Exception as e:
            logger.debug(f"[Progress] edit_text ignoré : {e}")

    async def done(self, total: int, phase_next: str = ""):
        """Affiche 100% avant de passer à la phase suivante."""
        elapsed = time.time() - self.start
        text = build_progress_text(
            total, total, elapsed,
            phase=self.phase,
            filename=self.filename,
        )
        try:
            await self.msg.edit_text(text, parse_mode="html")
        except Exception as e:
            logger.debug(f"[Progress] Échec de la mise à jour finale : {e}")

    async def set_phase(self, phase: str, filename: str = ""):
        """Change la phase (ex: download → upload) et réinitialise le timer."""
        self.phase    = phase
        self.filename = filename or self.filename
        self.start    = time.time()
        self._last_upd = 0.0
        emoji = PHASE_EMOJI.get(phase, "⏳")
        label = PHASE_LABEL.get(phase, phase.capitalize())
        try:
            await self.msg.edit_text(
                f"{emoji} <b>{label}...</b>",
                parse_mode="html"
            )
        except Exception as e:
            logger.debug(f"[Progress] Échec du changement de phase visuel : {e}")
