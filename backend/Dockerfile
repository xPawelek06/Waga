# Obraz produkcyjny backendu Waga (FastAPI).
# Uzywany do wdrozenia na VM (docker compose) - baza (Neon) zostaje zewnetrzna,
# ten kontener trzyma wylacznie sam serwis API (bezstanowy). Wzorzec identyczny
# jak MeetingReminder (E:\HomeProjects\MeetingReminder\backend\Dockerfile).
FROM python:3.12.6-slim

WORKDIR /app

# Warstwa zaleznosci osobno od kodu - cache Dockera nie reinstaluje pakietow
# przy kazdej zmianie w main.py/itd.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Bez --reload (to produkcja) i bez czytania .env z volume - zmienne
# srodowiskowe (DATABASE_URL, APP_SECRET) przychodza z docker-compose
# (env_file), nie z pliku wewnatrz obrazu.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
