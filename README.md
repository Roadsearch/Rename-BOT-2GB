# Rename-Bot-2GB — Édition Supabase + Render

Bot Telegram de renommage de fichiers jusqu'à 2 Go.  
Fork adapté de [JishuDeveloper/Rename-Bot-2GB](https://github.com/JishuDeveloper/Rename-Bot-2GB) :  
**MongoDB/motor → Supabase (PostgreSQL)** · **Heroku → Render**

> **Développeur :** [LabZero](https://t.me/LabZero0)  
> **Programmeur :** [Dev Suayki](https://t.me/Suayki)

---

## Structure du projet

```
rename-bot-supabase/
├── bot.py                  # Point d'entrée Pyrogram
├── config.py               # Variables d'environnement
├── route.py                # Serveur aiohttp (keepalive Render)
├── requirements.txt        # Dépendances Python
├── render.yaml             # Config déploiement Render
├── Dockerfile              # Image Docker (inclut ffmpeg)
├── supabase_schema.sql     # SQL à exécuter dans Supabase
├── helper/
│   └── database.py         # Couche Supabase (remplace motor/MongoDB)
└── plugins/
    ├── start.py            # /start, force-sub, enregistrement
    ├── rename.py           # Logique principale de renommage
    ├── thumbnail.py        # /viewthumb /delthumb
    ├── caption.py          # /set_caption /see_caption /del_caption
    │                         /set_prefix /set_suffix (idem)
    ├── metadata.py         # /metadata
    ├── admin.py            # /broadcast /status /restart
    └── misc.py             # /ping /donate /help
```

---

## Déploiement étape par étape

### 1. Préparer Supabase

1. Crée un compte sur [supabase.com](https://supabase.com)
2. Nouveau projet → note le **mot de passe** de la base
3. **SQL Editor → New Query** → colle `supabase_schema.sql` → **Run**
4. **Project Settings → API** → copie :
   - `Project URL` → `SUPABASE_URL`
   - `service_role` key (secret) → `SUPABASE_KEY`

> ⚠️ Utilise la clé **service_role**, pas la clé `anon`.

---

### 2. Préparer Telegram

| Variable | Où l'obtenir |
|---|---|
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather) → /newbot |
| `API_ID` / `API_HASH` | [my.telegram.org](https://my.telegram.org) |
| `ADMIN` | Ton user ID (ex. `123456789`) |
| `LOG_CHANNEL` | ID de ton canal log (ex. `-1001234567890`) |

---

### 3. Déployer sur Render

1. Fork ce repo sur ton GitHub
2. [render.com](https://render.com) → **New → Background Worker**
3. Connecte ton repo GitHub
4. **Environment Variables** → renseigne toutes les variables :

```
BOT_TOKEN       = <ton token>
API_ID          = <ton api_id>
API_HASH        = <ton api_hash>
ADMIN           = <ton user_id>
LOG_CHANNEL     = <id canal log>
SUPABASE_URL    = https://xxxx.supabase.co
SUPABASE_KEY    = <service_role key>
FORCE_SUBS      = <username canal sans @>  (optionnel)
START_PIC       = <url image>              (optionnel)
WEBHOOK         = false
```

5. **Create Background Worker** → Render build et démarre le bot 🚀

---

## Commandes disponibles

| Commande | Description |
|---|---|
| `/start` | Démarre le bot |
| `/viewthumb` | Voir la miniature actuelle |
| `/delthumb` | Supprimer la miniature |
| `/set_caption` | Définir une caption personnalisée |
| `/see_caption` | Voir la caption |
| `/del_caption` | Supprimer la caption |
| `/set_prefix` | Définir un préfixe de nom |
| `/set_suffix` | Définir un suffixe de nom |
| `/metadata` | Définir les métadonnées |
| `/ping` | Latence du bot |
| `/donate` | Soutenir le développeur |
| `/broadcast` | *(admin)* Envoyer un message à tous |
| `/status` | *(admin)* Stats utilisateurs |
| `/restart` | *(admin)* Redémarrer le bot |

---

## Crédits

- **Développeur :** [LabZero](https://t.me/LabZero0)
- **Programmeur :** [Dev Suayki](https://t.me/Suayki)
- Bot original : [JishuDeveloper](https://github.com/JishuDeveloper)


---

## UptimeRobot — Garder le bot actif 24h/24

Render free tier met le Web Service en veille après **15 min d'inactivité**.  
Configure UptimeRobot pour pinger le bot toutes les 5 minutes :

1. Crée un compte sur [uptimerobot.com](https://uptimerobot.com)
2. **New Monitor** → type **HTTP(s)**
3. URL : `https://ton-app.onrender.com/health`
4. Intervalle : **5 minutes**
5. **Create Monitor** ✅

Le endpoint `/health` répond `200 OK` et maintient le service actif.

---

## Limites anti-flood

Par défaut : **5 fichiers maximum par minute** par utilisateur.  
Modifiable dans `helper/flood_control.py` :

```python
MAX_REQUESTS = 5   # nombre max de fichiers
WINDOW_SEC   = 60  # fenêtre de temps en secondes
```

## File d'attente

Maximum **3 fichiers traités simultanément** sur tout le bot,  
et **1 seul fichier à la fois** par utilisateur.  
Modifiable dans `helper/queue_manager.py` :

```python
_global_sem = asyncio.Semaphore(3)  # parallélisme global
```
