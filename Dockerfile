# Verwende das offizielle Python-Image als Basis
FROM python:3.9-slim

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# Installiere python-dotenv und psycopg2-binary
RUN pip install python-dotenv psycopg2-binary requests beautifulsoup4 schedule

# Kopiere das Python-Skript und die .env-Datei in den Container
COPY ./scraper.py ./

# Umgebungsvariablen, können später bei Bedarf überschrieben werden
ENV DB_HOST=localhost \
    DB_NAME=stiebelwp \
    DB_USER=stiebelwp \
    DB_PASSWORD=stiebelwp \
    DB_PORT=5432

# Befehl zum Ausführen des Scripts beim Starten des Containers
CMD ["python", "./scraper.py"]
