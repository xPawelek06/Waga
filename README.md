Codzienny dziennik wagi i kalorii — Paweł

Statyczny frontend (GitHub Pages) + backend FastAPI/Postgres (Render + Neon), wzorem
`PlanTreningowy`. Jedna tabela na bieżący tydzień (Poniedziałek..Niedziela: data,
waga, kcal, średnia 7-dniowa licząca się automatycznie z tego, co wpisane) + zakładka
"Trend" z historią cotygodniowych podsumowań.

Podsumowanie tygodnia (`POST /api/admin/weekly-summary`) liczy średnią wagi/kcal
automatycznie z bieżących wpisów, ale trend i rekomendację kaloryczną dostarcza
wywołujący — od 2026-07-09 robi to `trener-personalny` (subagent w repo mózgu) przy
niedzielnej analizie, oceniając z pełnym kontekstem (cel 80 kg, trend treningowy),
zamiast suchej formuły. Dawny mechaniczny cron (GitHub Actions, bez AI) został
wycofany.

Synchronizacja do `health/waga.md` w repo mózgu i czyszczenie tabeli na nowy tydzień są
RĘCZNE — robi je trener-personalny przy rozmowie z Pawłem, nie automatycznie.
