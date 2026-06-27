FROM python:3.10-slim-buster

# Installation des dépendances système indispensables (FFmpeg et outils de compression)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    xz-utils \
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
