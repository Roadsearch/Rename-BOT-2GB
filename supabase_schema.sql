-- ============================================================
-- SUPABASE SCHEMA — Rename-Bot-2GB (version 3)
-- Colle ce SQL dans : Supabase → SQL Editor → New Query → Run
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    user_id      BIGINT PRIMARY KEY,
    thumbnail    TEXT,
    caption      TEXT,
    prefix       TEXT,
    suffix       TEXT,
    metadata     TEXT,
    rename_rule  TEXT,
    auto_delete  INTEGER DEFAULT 300,
    files_count  INTEGER DEFAULT 0,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_created ON users (created_at DESC);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_role_only" ON users USING (true) WITH CHECK (true);

CREATE TABLE IF NOT EXISTS bot_settings (
    key        TEXT PRIMARY KEY,
    value      TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Colonne cookies_file pour stocker le chemin local du fichier cookies
-- (la valeur est écrite dans bot_settings avec la clé "yt_cookies")
