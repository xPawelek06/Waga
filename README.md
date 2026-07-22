Codzienny dziennik wagi i kalorii — Paweł

Statyczny frontend (GitHub Pages) + backend FastAPI/Postgres (Neon), wzorem
`PlanTreningowy`. Jedna tabela na bieżący tydzień (Poniedziałek..Niedziela: data,
waga, kcal, średnia 7-dniowa licząca się automatycznie z tego, co wpisane) + zakładka
"Trend" z historią cotygodniowych podsumowań.

## Hosting backendu (2026-07-22: migracja z Render)

VM (GCP, `paw-projects`), Docker Compose — FastAPI + Caddy (reverse proxy,
HTTPS automatyczny przez Let's Encrypt/sslip.io), ten sam wzorzec co
`MeetingReminder`/`PlanTreningowy`. Jeden wspólny Caddy na tej VM obsługuje
wszystkie trzy appki (różne subdomeny sslip.io) — konfiguracja Caddyfile
mieszka w repo `MeetingReminder` (`~/MeetingReminder/Caddyfile` na serwerze).
Backend Waga podłącza się do tej samej sieci Dockera
(`meetingreminder_default`, external w `docker-compose.yml` tego repo).

Tymczasowy (trial GCP, do 21.09.2026), docelowo migracja na wspólny VPS
(Plan B, Hetzner). Baza (Neon) zostaje bez zmian — connection string
identyczny jak wcześniej na Renderze. `render.yaml` zostaje jako gotowy
fallback, nieużywany.

Konfiguracja: `docker-compose.yml` w katalogu głównym, `backend/Dockerfile`.
Sekrety (`DATABASE_URL`, `APP_SECRET`) w `backend/.env` na serwerze
(gitignore, chmod 600) — nie w tym repo.

Podsumowanie tygodnia (`POST /api/admin/weekly-summary`) liczy średnią wagi/kcal
automatycznie z bieżących wpisów, ale trend i rekomendację kaloryczną dostarcza
wywołujący — od 2026-07-09 robi to `trener-personalny` (subagent w repo mózgu) przy
niedzielnej analizie, oceniając z pełnym kontekstem (cel 80 kg, trend treningowy),
zamiast suchej formuły. Dawny mechaniczny cron (GitHub Actions, bez AI) został
wycofany.

Synchronizacja do `health/waga.md` w repo mózgu i czyszczenie tabeli na nowy tydzień są
RĘCZNE — robi je trener-personalny przy rozmowie z Pawłem, nie automatycznie.
