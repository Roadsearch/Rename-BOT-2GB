-- ============================================================
-- Schéma Supabase (PostgreSQL) pour Rename Bot 2GB
-- LabZero / Dev Suayki
-- ============================================================
-- ⚠️ Ce schéma est basé sur les fonctionnalités visibles du bot
-- (miniature, légende, préfixe, suffixe, métadonnées, admin).
-- À ajuster si le dossier plugins/database/ révèle d'autres champs.
-- ============================================================

create table if not exists users (
    user_id       bigint primary key,
    username      text,
    first_name    text,
    thumbnail     text,               -- file_id Telegram de la miniature
    caption       text,               -- légende personnalisée
    prefix        text,               -- préfixe de renommage
    suffix        text,               -- suffixe de renommage
    metadata_on   boolean default false,  -- métadonnées personnalisées activées ?
    metadata      text default 'Par :- @LabZero0',  -- texte des métadonnées
    banned        boolean default false,
    joined_at     timestamptz default now()
);

-- Index pour les recherches rapides par statut banni (utile pour le broadcast)
create index if not exists idx_users_banned on users (banned);

-- Table optionnelle : statistiques globales du bot (compteur de fichiers renommés, etc.)
create table if not exists bot_stats (
    id                bigint primary key default 1,
    total_files_renamed bigint default 0,
    updated_at        timestamptz default now(),
    constraint single_row check (id = 1)
);

insert into bot_stats (id) values (1)
on conflict (id) do nothing;

-- ============================================================
-- Row Level Security (RLS)
-- ============================================================
-- Le bot doit utiliser la clé "service_role" (pas "anon") pour
-- accéder à ces tables sans restriction RLS, car les requêtes
-- viennent du serveur, pas du navigateur d'un utilisateur final.
-- ============================================================
alter table users enable row level security;
alter table bot_stats enable row level security;

-- Politique : seul le service_role (backend) peut lire/écrire
create policy "Service role full access - users"
    on users for all
    using (auth.role() = 'service_role')
    with check (auth.role() = 'service_role');

create policy "Service role full access - bot_stats"
    on bot_stats for all
    using (auth.role() = 'service_role')
    with check (auth.role() = 'service_role');
