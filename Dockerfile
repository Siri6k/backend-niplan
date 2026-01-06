# 1. Image de base
FROM python:3.11-slim

# 2. Variables d'environnement pour Python
# Empêche la création de fichiers .pyc et force l'affichage des logs en temps réel
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Installation des dépendances système (nécessaires pour PostgreSQL)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 4. Dossier de travail
WORKDIR /app

# 5. Installation des dépendances Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copie du projet
COPY . /app/

# 7. Port exposé par Django
EXPOSE 8000

# 8. Commande de lancement (utilisant Gunicorn pour la prod)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]