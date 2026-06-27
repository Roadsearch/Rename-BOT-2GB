# Utilisation d'une version récente et maintenue de Debian (Bookworm)
FROM python:3.10-slim-bookworm

# Installation de FFmpeg de manière stable et propre
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Création du dossier de travail
WORKDIR /app

# Copie et installation des bibliothèques Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du reste du code du bot
COPY . .

# Commande de démarrage du bot
CMD ["python", "bot.py"]
