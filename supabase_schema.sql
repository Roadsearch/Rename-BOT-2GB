-- ============================================================
-- SUPABASE SCHEMA — Rename-Bot-2GB (version 2)
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

-- RLS (Row Level Security) — sécurité Supabase
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Politique : seul le service_role (backend) peut tout faire
CREATE POLICY "service_role_only" ON users
    USING (true)
    WITH CHECK (true);

-- Ajout colonne start_pic dans la table users (si elle existe déjà)
-- Pour une nouvelle installation, la colonne est déjà dans le CREATE TABLE ci-dessus.
ALTER TABLE users ADD COLUMN IF NOT EXISTS start_pic TEXT;

-- Table dédiée pour les paramètres globaux du bot (admin)
CREATE TABLE IF NOT EXISTS bot_settings (
    key   TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
