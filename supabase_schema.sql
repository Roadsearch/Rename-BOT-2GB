-- ============================================================
-- SUPABASE SCHEMA — Rename-Bot-2GB
-- Colle ce SQL dans : Supabase → SQL Editor → New Query → Run
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    user_id    BIGINT PRIMARY KEY,
    thumbnail  TEXT,
    caption    TEXT,
    prefix     TEXT,
    suffix     TEXT,
    metadata   TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index optionnel pour les broadcasts (lecture de tous les user_id)
CREATE INDEX IF NOT EXISTS idx_users_created ON users (created_at DESC);
