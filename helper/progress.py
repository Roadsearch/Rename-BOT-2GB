"""
helper/progress.py — Barre de progression pro.

CORRECTION BUG 3 : Pyrogram appelle progress= de façon SYNCHRONE.
La fonction doit être def (pas async def).
On utilise asyncio.create_task() pour lancer la mise à jour sans bloquer.
"""
import time
import asyncio
import logging
from pyrogram.types import Message

logger     = logging.getLogger(__name__)
FULL       = "█"
EMPTY      = "░"
BAR_LENGTH = 12


def _human_size(num: float) -> str:
    for unit in ["o", "Ko", "Mo", "Go", "To"]:
        if abs(num) < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} To"


def _eta(seconds: float) -> str:
    seconds = int(seconds)
    if seconds <= 0: return "0s"
    if seconds < 60: return f"{seconds}s"
    m, s = divmod(seconds, 60)
    if m < 60: return f"{m}m {s:02d}s"
    h, m = divmod(m, 60)
    return f"{h}h {m:02d}m"


def _build_bar(percent: float) -> str:
    filled = int(BAR_LENGTH * percent / 100)
    return FULL * filled + EMPTY * (BAR_LENGTH - filled)


PHASE_EMOJI = {"download": "⬇️", "upload": "⬆️", "extract": "📂", "rename": "✏️"}
PHASE_LABEL = {"download": "Téléchargement", "upload": "Upload", "extract": "Extraction", "rename": "Renommage"}


def build_progress_text(current, total, elapsed, phase="download", filename=""):
    percent   = min(current * 100 / total, 100) if total else 0
    speed     = current / elapsed if elapsed > 0 else 0
    remaining = (total - current) / speed if speed > 0 else 0
    bar       = _build_bar(percent)
    emoji     = PHASE_EMOJI.get(phase, "⏳")
    label     = PHASE_LABEL.get(phase, phase.capitalize())
    fname_line = ""
    if filename:
        name = filename if len(filename) <= 35 else "…" + filename[-33:]
        fname_line = f"📄 <code>{name}</code>\n\n"
    return (
        f"{emoji} <b>{label}...</b>\n\n"
        f"{fname_line}"
        f"<code>[{bar}]</code> <b>{percent:.1f}%</b>\n\n"
        f"📦 <b>Taille :</b> {_human_size(current)} / {_human_size(total)}\n"
        f"🚀 <b>Vitesse :</b> {_human_size(speed)}/s\n"
        f"⏱️ <b>Reste :</b> {_eta(remaining)}\n"
        f"⏳ <b>Écoulé :</b> {_eta(elapsed)}"
    )


class ProgressUpdater:
    """
    Callback de progression compatible Pyrogram.

    IMPORTANT : Pyrogram appelle progress= de manière SYNCHRONE
    (pas await). On doit donc définir __call__ comme def (synchrone)
    et lancer la mise à jour Telegram via asyncio.create_task().
    """
    UPDATE_INTERVAL = 4.0  # secondes entre deux mises à jour

    def __init__(self, msg: Message, phase: str = "download", filename: str = ""):
        self.msg       = msg
        self.phase     = phase
        self.filename  = filename
        self.start     = time.time()
        self._last_upd = 0.0
        self._task     = None

    # ── Appelé par Pyrogram (SYNCHRONE) ──────────────────────────────────────
    def __call__(self, current: int, total: int):
        now = time.time()
        if now - self._last_upd < self.UPDATE_INTERVAL:
            return
        self._last_upd = now
        elapsed = now - self.start
        text = build_progress_text(current, total, elapsed, self.phase, self.filename)
        # Lance la coroutine sans bloquer — crée une task dans l'event loop courant
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._edit(text))
        except Exception as e:
            logger.debug(f"[Progress] create_task ignoré : {e}")

    async def _edit(self, text: str):
        try:
            await self.msg.edit_text(text, parse_mode="html")
        except Exception as e:
            logger.debug(f"[Progress] edit_text ignoré : {e}")

    # ── Méthodes async pour usage manuel ─────────────────────────────────────
    async def set_phase(self, phase: str, filename: str = ""):
        self.phase    = phase
        self.filename = filename or self.filename
        self.start    = time.time()
        self._last_upd = 0.0
        emoji = PHASE_EMOJI.get(phase, "⏳")
        label = PHASE_LABEL.get(phase, phase.capitalize())
        try:
            await self.msg.edit_text(f"{emoji} <b>{label}...</b>", parse_mode="html")
        except:
            pass

    async def done(self, total: int):
        elapsed = time.time() - self.start
        text = build_progress_text(total, total, elapsed, self.phase, self.filename)
        try:
            await self.msg.edit_text(text, parse_mode="html")
        except:
            pass
