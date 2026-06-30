"""
helper/database.py
Couche d'accès Supabase (PostgreSQL).
Développeur : LabZero (https://t.me/LabZero0)
Programmeur : Dev Suayki (https://t.me/Suayki)

Schema SQL à créer dans Supabase :
───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id       BIGINT PRIMARY KEY,
    thumbnail     TEXT,
    caption       TEXT,
    prefix        TEXT,
    suffix        TEXT,
    metadata      TEXT,
    rename_rule   TEXT,
    auto_delete   INTEGER DEFAULT 300,
    files_count   INTEGER DEFAULT 0,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_users_created ON users (created_at DESC);
───────────────────────────────────────────────
"""
import logging
from supabase import create_client, Client
from config import Config

logger = logging.getLogger(__name__)

try:
    _sb: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    logger.info("✅ Connexion Supabase établie")
except Exception as e:
    logger.critical(f"❌ Impossible de se connecter à Supabase : {e}")
    raise


def _get(user_id: int) -> dict | None:
    try:
        resp = _sb.table("users").select("*").eq("user_id", user_id).execute()
        return resp.data[0] if resp.data else None
    except Exception as e:
        logger.error(f"[DB] _get({user_id}) : {e}")
        return None


def _upsert(user_id: int, **fields):
    try:
        _sb.table("users").upsert({"user_id": user_id, **fields}).execute()
    except Exception as e:
        logger.error(f"[DB] _upsert({user_id}, {fields}) : {e}")


# ── Utilisateurs ─────────────────────────────────────────────────────────────

async def add_user(user_id: int):
    if not _get(user_id):
        _upsert(user_id)
        logger.info(f"[DB] Nouvel utilisateur : {user_id}")

async def is_user_exist(user_id: int) -> bool:
    return _get(user_id) is not None

async def total_users_count() -> int:
    try:
        resp = _sb.table("users").select("user_id", count="exact").execute()
        return resp.count or 0
    except Exception as e:
        logger.error(f"[DB] total_users_count : {e}")
        return 0

async def get_all_users() -> list:
    try:
        resp = _sb.table("users").select("user_id").execute()
        return [row["user_id"] for row in resp.data]
    except Exception as e:
        logger.error(f"[DB] get_all_users : {e}")
        return []

async def delete_user(user_id: int):
    try:
        _sb.table("users").delete().eq("user_id", user_id).execute()
    except Exception as e:
        logger.error(f"[DB] delete_user({user_id}) : {e}")


# ── Compteur fichiers ────────────────────────────────────────────────────────

async def increment_files_count(user_id: int):
    try:
        row = _get(user_id)
        current = row["files_count"] if row and row.get("files_count") else 0
        _upsert(user_id, files_count=current + 1)
    except Exception as e:
        logger.error(f"[DB] increment_files_count({user_id}) : {e}")

async def get_files_count(user_id: int) -> int:
    row = _get(user_id)
    return row["files_count"] if row and row.get("files_count") else 0


# ── Thumbnail ────────────────────────────────────────────────────────────────

async def set_thumbnail(user_id: int, thumbnail: str):
    _upsert(user_id, thumbnail=thumbnail)

async def get_thumbnail(user_id: int) -> str | None:
    row = _get(user_id)
    return row["thumbnail"] if row else None

async def del_thumbnail(user_id: int):
    try:
        _sb.table("users").update({"thumbnail": None}).eq("user_id", user_id).execute()
    except Exception as e:
        logger.error(f"[DB] del_thumbnail({user_id}) : {e}")


# ── Caption ──────────────────────────────────────────────────────────────────

async def set_caption(user_id: int, caption: str):
    _upsert(user_id, caption=caption)

async def get_caption(user_id: int) -> str | None:
    row = _get(user_id)
    return row["caption"] if row else None

async def del_caption(user_id: int):
    try:
        _sb.table("users").update({"caption": None}).eq("user_id", user_id).execute()
    except Exception as e:
        logger.error(f"[DB] del_caption({user_id}) : {e}")


# ── Prefix ───────────────────────────────────────────────────────────────────

async def set_prefix(user_id: int, prefix: str):
    _upsert(user_id, prefix=prefix)

async def get_prefix(user_id: int) -> str | None:
    row = _get(user_id)
    return row["prefix"] if row else None

async def del_prefix(user_id: int):
    try:
        _sb.table("users").update({"prefix": None}).eq("user_id", user_id).execute()
    except Exception as e:
        logger.error(f"[DB] del_prefix({user_id}) : {e}")


# ── Suffix ───────────────────────────────────────────────────────────────────

async def set_suffix(user_id: int, suffix: str):
    _upsert(user_id, suffix=suffix)

async def get_suffix(user_id: int) -> str | None:
    row = _get(user_id)
    return row["suffix"] if row else None

async def del_suffix(user_id: int):
    try:
        _sb.table("users").update({"suffix": None}).eq("user_id", user_id).execute()
    except Exception as e:
        logger.error(f"[DB] del_suffix({user_id}) : {e}")


# ── Metadata ─────────────────────────────────────────────────────────────────

async def set_metadata(user_id: int, metadata: str):
    _upsert(user_id, metadata=metadata)

async def get_metadata(user_id: int) -> str | None:
    row = _get(user_id)
    return row["metadata"] if row else None

async def del_metadata(user_id: int):
    try:
        _sb.table("users").update({"metadata": None}).eq("user_id", user_id).execute()
    except Exception as e:
        logger.error(f"[DB] del_metadata({user_id}) : {e}")


# ── Rename rule (Regex) ───────────────────────────────────────────────────────

async def set_rename_rule(user_id: int, rule: str):
    _upsert(user_id, rename_rule=rule)

async def get_rename_rule(user_id: int) -> str | None:
    row = _get(user_id)
    return row.get("rename_rule") if row else None

async def del_rename_rule(user_id: int):
    try:
        _sb.table("users").update({"rename_rule": None}).eq("user_id", user_id).execute()
    except Exception as e:
        logger.error(f"[DB] del_rename_rule({user_id}) : {e}")


# ── Auto-delete delay ────────────────────────────────────────────────────────

async def set_auto_delete(user_id: int, seconds: int):
    _upsert(user_id, auto_delete=seconds)

async def get_auto_delete(user_id: int) -> int:
    row = _get(user_id)
    return row.get("auto_delete", 300) if row else 300


# ── Paramètres globaux du bot (bot_settings) ─────────────────────────────────

async def set_bot_setting(key: str, value: str):
    try:
        _sb.table("bot_settings").upsert(
            {"key": key, "value": value, "updated_at": "now()"}
        ).execute()
        logger.info(f"[DB] bot_setting {key} mis à jour")
    except Exception as e:
        logger.error(f"[DB] set_bot_setting({key}) : {e}")


async def get_bot_setting(key: str) -> str | None:
    try:
        resp = _sb.table("bot_settings").select("value").eq("key", key).execute()
        return resp.data[0]["value"] if resp.data else None
    except Exception as e:
        logger.error(f"[DB] get_bot_setting({key}) : {e}")
        return None


async def del_bot_setting(key: str):
    try:
        _sb.table("bot_settings").delete().eq("key", key).execute()
        logger.info(f"[DB] bot_setting {key} supprimé")
    except Exception as e:
        logger.error(f"[DB] del_bot_setting({key}) : {e}")
