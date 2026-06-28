"""
helper/database.py
Couche d'accès Supabase (PostgreSQL) — remplace motor/MongoDB.

Schema SQL à créer dans Supabase (SQL Editor) :
───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id   BIGINT PRIMARY KEY,
    thumbnail TEXT,
    caption   TEXT,
    prefix    TEXT,
    suffix    TEXT,
    metadata  TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
───────────────────────────────────────────────
"""

from supabase import create_client, Client
from config import Config

# Client Supabase (initialisé une seule fois)
_sb: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)


# ── Utilitaire interne ───────────────────────────────────────────────────────

def _get(user_id: int) -> dict | None:
    """Retourne la ligne utilisateur ou None."""
    resp = _sb.table("users").select("*").eq("user_id", user_id).execute()
    return resp.data[0] if resp.data else None


def _upsert(user_id: int, **fields):
    """Crée ou met à jour un utilisateur."""
    _sb.table("users").upsert({"user_id": user_id, **fields}).execute()


# ── API publique ─────────────────────────────────────────────────────────────

async def add_user(user_id: int):
    """Enregistre un utilisateur (sans écraser ses données existantes)."""
    if not _get(user_id):
        _upsert(user_id)


async def is_user_exist(user_id: int) -> bool:
    return _get(user_id) is not None


async def total_users_count() -> int:
    resp = _sb.table("users").select("user_id", count="exact").execute()
    return resp.count or 0


async def get_all_users():
    """Retourne tous les user_id."""
    resp = _sb.table("users").select("user_id").execute()
    return [row["user_id"] for row in resp.data]


async def delete_user(user_id: int):
    _sb.table("users").delete().eq("user_id", user_id).execute()


# ── Thumbnail ────────────────────────────────────────────────────────────────

async def set_thumbnail(user_id: int, thumbnail: str):
    _upsert(user_id, thumbnail=thumbnail)


async def get_thumbnail(user_id: int) -> str | None:
    row = _get(user_id)
    return row["thumbnail"] if row else None


async def del_thumbnail(user_id: int):
    _sb.table("users").update({"thumbnail": None}).eq("user_id", user_id).execute()


# ── Caption ──────────────────────────────────────────────────────────────────

async def set_caption(user_id: int, caption: str):
    _upsert(user_id, caption=caption)


async def get_caption(user_id: int) -> str | None:
    row = _get(user_id)
    return row["caption"] if row else None


async def del_caption(user_id: int):
    _sb.table("users").update({"caption": None}).eq("user_id", user_id).execute()


# ── Prefix ───────────────────────────────────────────────────────────────────

async def set_prefix(user_id: int, prefix: str):
    _upsert(user_id, prefix=prefix)


async def get_prefix(user_id: int) -> str | None:
    row = _get(user_id)
    return row["prefix"] if row else None


async def del_prefix(user_id: int):
    _sb.table("users").update({"prefix": None}).eq("user_id", user_id).execute()


# ── Suffix ───────────────────────────────────────────────────────────────────

async def set_suffix(user_id: int, suffix: str):
    _upsert(user_id, suffix=suffix)


async def get_suffix(user_id: int) -> str | None:
    row = _get(user_id)
    return row["suffix"] if row else None


async def del_suffix(user_id: int):
    _sb.table("users").update({"suffix": None}).eq("user_id", user_id).execute()


# ── Metadata ─────────────────────────────────────────────────────────────────

async def set_metadata(user_id: int, metadata: str):
    _upsert(user_id, metadata=metadata)


async def get_metadata(user_id: int) -> str | None:
    row = _get(user_id)
    return row["metadata"] if row else None


async def del_metadata(user_id: int):
    _sb.table("users").update({"metadata": None}).eq("user_id", user_id).execute()
