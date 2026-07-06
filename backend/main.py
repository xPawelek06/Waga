import os
from datetime import date, timedelta
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models
import schemas
from database import Base, SessionLocal, engine

Base.metadata.create_all(bind=engine)


def seed_week_days():
    """7 stale wiersze dni tygodnia - seedowane raz, jesli tabela jest pusta.
    W odroznieniu od Exercise w PlanTreningowy te nazwy sie nie zmieniaja, wiec
    nie ma tu potrzeby osobnego upsert-skryptu uruchamianego recznie."""
    db = SessionLocal()
    try:
        if db.query(models.WeekDay).count() > 0:
            return
        days = [
            "Poniedziałek",
            "Wtorek",
            "Środa",
            "Czwartek",
            "Piątek",
            "Sobota",
            "Niedziela",
        ]
        for order, name in enumerate(days):
            db.add(models.WeekDay(day=name, day_order=order))
        db.commit()
    finally:
        db.close()


seed_week_days()

# Sekret do zapisu (naglowek X-Auth-Secret) - w produkcji ustaw go jako zmienna
# srodowiskowa APP_SECRET w Renderze, zamiast polegac na tej wartosci domyslnej.
APP_SECRET = os.environ.get("APP_SECRET", "Waga")

ALLOWED_ORIGINS = [
    "https://xpawelek06.github.io",
    "http://localhost:8003",
    "http://127.0.0.1:8003",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

app = FastAPI(title="Waga API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_secret(x_auth_secret: str = Header(default="")):
    if x_auth_secret != APP_SECRET:
        raise HTTPException(status_code=401, detail="Zly sekret (naglowek X-Auth-Secret)")


def latest_entries_by_day(db: Session):
    """Zwraca liste (WeekDay, najnowszy DayEntry albo None) posortowana po day_order."""
    week_days = db.query(models.WeekDay).order_by(models.WeekDay.day_order).all()
    result = []
    for wd in week_days:
        latest = (
            db.query(models.DayEntry)
            .filter(models.DayEntry.week_day_id == wd.id)
            .order_by(models.DayEntry.created_at.desc())
            .first()
        )
        result.append((wd, latest))
    return result


def compute_week_averages(db: Session):
    """Srednia wagi/kcal z tego, co aktualnie wpisane w biezacym tygodniu
    (tabela day_entries jest czyszczona na start kazdego tygodnia, wiec wszystko
    co tam jest to dane "tego tygodnia" - nie trzeba filtrowac po dacie)."""
    pairs = latest_entries_by_day(db)
    weights = [e.weight_kg for _, e in pairs if e and e.weight_kg is not None]
    kcals = [e.kcal for _, e in pairs if e and e.kcal is not None]
    avg_weight = round(sum(weights) / len(weights), 2) if weights else None
    avg_kcal = round(sum(kcals) / len(kcals), 1) if kcals else None
    return avg_weight, avg_kcal


def current_week_bounds(today: Optional[date] = None):
    today = today or date.today()
    week_start = today - timedelta(days=today.weekday())  # poniedzialek
    week_end = week_start + timedelta(days=6)  # niedziela
    return week_start, week_end


def compute_trend(avg_weight_kg: Optional[float], previous: Optional[models.WeeklySummary]):
    """Reguly z health/CLAUDE.md w repo mozgu (lean bulk do 80 kg, tempo 0,25-0,4
    kg/tydzien): stoi/spada -> +150-200 kcal; rosnie >0,5 kg/tydz -> -150 kcal;
    w zdrowym tempie (0 < delta <= 0,5) -> kaloryka OK, bez zmian."""
    if avg_weight_kg is None:
        return None, "Brak wpisów wagi w tym tygodniu — nie można ocenić trendu."
    if previous is None or previous.avg_weight_kg is None:
        return None, "Za mało danych — wróć za tydzień."

    delta = round(avg_weight_kg - previous.avg_weight_kg, 2)
    if delta <= 0:
        return "stoi/spada", "Kaloryka za niska — dodaj +150 do +200 kcal/dzień."
    if delta > 0.5:
        return "rośnie za szybko", "Kaloryka za wysoka — odejmij 150 kcal/dzień."
    return "rośnie w zdrowym tempie", "Kaloryka OK — bez zmian."


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/week", response_model=schemas.WeekOut)
def get_week(db: Session = Depends(get_db)):
    pairs = latest_entries_by_day(db)
    days = [
        schemas.WeekDayOut(
            id=wd.id,
            day=wd.day,
            day_order=wd.day_order,
            entry_date=entry.entry_date if entry else None,
            weight_kg=entry.weight_kg if entry else None,
            kcal=entry.kcal if entry else None,
        )
        for wd, entry in pairs
    ]
    avg_weight, avg_kcal = compute_week_averages(db)
    return schemas.WeekOut(days=days, avg_weight_7d=avg_weight, avg_kcal_7d=avg_kcal)


@app.post(
    "/api/entries",
    response_model=schemas.DayEntryOut,
    dependencies=[Depends(require_secret)],
)
def create_entry(payload: schemas.DayEntryCreate, db: Session = Depends(get_db)):
    week_day = db.query(models.WeekDay).filter(models.WeekDay.id == payload.week_day_id).first()
    if not week_day:
        raise HTTPException(status_code=404, detail="Nie ma dnia o tym id")

    entry = models.DayEntry(
        week_day_id=payload.week_day_id,
        entry_date=payload.entry_date,
        weight_kg=payload.weight_kg,
        kcal=payload.kcal,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@app.get(
    "/api/entries",
    response_model=List[schemas.DayEntryOut],
    dependencies=[Depends(require_secret)],
)
def list_entries(since: Optional[date] = None, db: Session = Depends(get_db)):
    """Do recznej synchronizacji przez trenera-personalnego do health/waga.md."""
    q = db.query(models.DayEntry)
    if since:
        q = q.filter(models.DayEntry.entry_date >= since)
    return q.order_by(models.DayEntry.entry_date, models.DayEntry.id).all()


@app.delete("/api/admin/week", dependencies=[Depends(require_secret)])
def clear_week(db: Session = Depends(get_db)):
    """Kasuje wszystkie wpisy biezacego tygodnia (day_entries), zostawiajac
    tabele week_days (nazwy dni) nietknieta - uzywane przez trenera-personalnego
    przy recznej synchronizacji na start kolejnego tygodnia."""
    deleted = db.query(models.DayEntry).delete()
    db.commit()
    return {"status": "ok", "deleted": deleted}


@app.post(
    "/api/admin/weekly-summary",
    response_model=schemas.WeeklySummaryOut,
    dependencies=[Depends(require_secret)],
)
def run_weekly_summary(db: Session = Depends(get_db)):
    """Liczy srednia wagi/kcal biezacego tygodnia, porownuje z ostatnim zapisanym
    wierszem WeeklySummary i dopisuje/aktualizuje wiersz dla tego tygodnia.
    Wyzwalane co niedziele ~20:00 (Europe/Warsaw) przez GitHub Actions - patrz
    .github/workflows/weekly-summary.yml. Idempotentne: wywolanie drugi raz w tym
    samym tygodniu nadpisuje ten sam wiersz (upsert po week_start), a nie dubluje."""
    week_start, week_end = current_week_bounds()
    avg_weight, avg_kcal = compute_week_averages(db)

    previous = (
        db.query(models.WeeklySummary)
        .filter(models.WeeklySummary.week_start < week_start)
        .order_by(models.WeeklySummary.week_start.desc())
        .first()
    )
    trend, recommendation = compute_trend(avg_weight, previous)

    existing = (
        db.query(models.WeeklySummary)
        .filter(models.WeeklySummary.week_start == week_start)
        .first()
    )
    if existing:
        existing.week_end = week_end
        existing.avg_weight_kg = avg_weight
        existing.avg_kcal = avg_kcal
        existing.trend = trend
        existing.kcal_recommendation = recommendation
        row = existing
    else:
        row = models.WeeklySummary(
            week_start=week_start,
            week_end=week_end,
            avg_weight_kg=avg_weight,
            avg_kcal=avg_kcal,
            trend=trend,
            kcal_recommendation=recommendation,
        )
        db.add(row)

    db.commit()
    db.refresh(row)
    return row


@app.get("/api/weekly-summary", response_model=List[schemas.WeeklySummaryOut])
def list_weekly_summaries(db: Session = Depends(get_db)):
    return (
        db.query(models.WeeklySummary)
        .order_by(models.WeeklySummary.week_start.desc())
        .all()
    )
