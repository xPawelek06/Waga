Codzienny dziennik wagi i kalorii — Paweł

Statyczny frontend (GitHub Pages) + backend FastAPI/Postgres (Render + Neon), wzorem
`PlanTreningowy`. Jedna tabela na bieżący tydzień (Poniedziałek..Niedziela: data,
waga, kcal, średnia 7-dniowa licząca się automatycznie z tego, co wpisane) + zakładka
"Trend" z historią cotygodniowych podsumowań (licznik automatyczny, bez AI — patrz
`.github/workflows/weekly-summary.yml`).

Synchronizacja do `health/waga.md` w repo mózgu i czyszczenie tabeli na nowy tydzień są
RĘCZNE — robi je trener-personalny przy rozmowie z Pawłem, nie automatycznie.
