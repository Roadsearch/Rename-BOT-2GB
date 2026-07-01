import asyncio
from supabase import create_client, Client as SupabaseClient
from config import Config
from .utils import send_log


class Database:
    """
    Couche d'accès Supabase (PostgreSQL) remplaçant l'ancien module
    MongoDB (motor). Le client supabase-py étant synchrone, chaque
    appel est exécuté dans un thread séparé via asyncio.to_thread
    pour ne pas bloquer la boucle asyncio de Pyrogram.
    """

    def __init__(self, url: str, key: str):
        self.supabase: SupabaseClient = create_client(url, key)
        self.table = "users"

    async def _run(self, func, *args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    # ------------------------------------------------------------------
    # Gestion des utilisateurs
    # ------------------------------------------------------------------
    async def is_user_exist(self, user_id: int) -> bool:
        def _get():
            return self.supabase.table(self.table).select("user_id").eq("user_id", user_id).execute()
        res = await self._run(_get)
        return len(res.data) > 0

    async def add_user(self, client, message):
        user = message.from_user
        if await self.is_user_exist(user.id):
            return

        def _insert():
            return self.supabase.table(self.table).insert({
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
            }).execute()
        await self._run(_insert)
        await send_log(client, user)

    async def total_users_count(self) -> int:
        def _count():
            return self.supabase.table(self.table).select("user_id", count="exact").execute()
        res = await self._run(_count)
        return res.count or 0

    async def get_all_users(self):
        def _get():
            return self.supabase.table(self.table).select("user_id").execute()
        res = await self._run(_get)
        for row in res.data:
            # "_id" est conservé pour rester compatible avec le code
            # existant (admin_panel.py) qui lit user['_id']
            yield {"_id": row["user_id"]}

    async def delete_user(self, user_id: int):
        def _del():
            return self.supabase.table(self.table).delete().eq("user_id", int(user_id)).execute()
        await self._run(_del)

    # ------------------------------------------------------------------
    # Champs génériques (lecture / écriture)
    # ------------------------------------------------------------------
    async def _get_field(self, user_id: int, field: str):
        def _get():
            return self.supabase.table(self.table).select(field).eq("user_id", user_id).execute()
        res = await self._run(_get)
        if res.data:
            return res.data[0].get(field)
        return None

    async def _set_field(self, user_id: int, field: str, value):
        def _upsert():
            return self.supabase.table(self.table).upsert({"user_id": user_id, field: value}).execute()
        await self._run(_upsert)

    # ------------------------------------------------------------------
    # Légende personnalisée
    # ------------------------------------------------------------------
    async def set_caption(self, user_id: int, caption):
        await self._set_field(user_id, "caption", caption)

    async def get_caption(self, user_id: int):
        return await self._get_field(user_id, "caption")

    # ------------------------------------------------------------------
    # Préfixe / Suffixe
    # ------------------------------------------------------------------
    async def set_prefix(self, user_id: int, prefix):
        await self._set_field(user_id, "prefix", prefix)

    async def get_prefix(self, user_id: int):
        return await self._get_field(user_id, "prefix")

    async def set_suffix(self, user_id: int, suffix):
        await self._set_field(user_id, "suffix", suffix)

    async def get_suffix(self, user_id: int):
        return await self._get_field(user_id, "suffix")

    # ------------------------------------------------------------------
    # Miniature
    # ------------------------------------------------------------------
    async def set_thumbnail(self, user_id: int, file_id):
        await self._set_field(user_id, "thumbnail", file_id)

    async def get_thumbnail(self, user_id: int):
        return await self._get_field(user_id, "thumbnail")

    # ------------------------------------------------------------------
    # Métadonnées
    # ------------------------------------------------------------------
    async def set_metadata(self, user_id: int, bool_meta: bool):
        await self._set_field(user_id, "metadata_on", bool_meta)

    async def get_metadata(self, user_id: int) -> bool:
        val = await self._get_field(user_id, "metadata_on")
        return bool(val)

    async def set_metadata_code(self, user_id: int, metadata_code):
        await self._set_field(user_id, "metadata", metadata_code)

    async def get_metadata_code(self, user_id: int):
        return await self._get_field(user_id, "metadata")


# Instance unique utilisée par tous les plugins : `from helper.database import db`
db = Database(Config.SUPABASE_URL, Config.SUPABASE_KEY)


# Channel dev : LabZero (https://t.me/LabZero0)
# Developer : Dev Suayki (https://t.me/Suayki)
