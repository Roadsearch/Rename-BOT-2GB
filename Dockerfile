# Utilisation d'une version stable, récente et légère de Python sous Debian
FROM python:3.10-slim-bookworm

# Évite la génération de fichiers .pyc et force l'affichage immédiat des logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Installation de FFmpeg et des outils essentiels pour compiler TgCrypto et Psutil
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Définition du répertoire de travail dans le conteneur
WORKDIR /app

# Cache Docker : Copie et installation des dépendances en premier
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie du reste du code source (optimisé grâce au fichier .dockerignore)
COPY . .

# Commande de démarrage par défaut pour exécuter le bot
CMD ["python", "bot.py"]
