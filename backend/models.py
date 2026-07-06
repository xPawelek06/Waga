from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class WeekDay(Base):
    """Statyczna struktura tabeli: 7 stalych wierszy, Poniedzialek..Niedziela.

    Seedowane raz przy starcie backendu (patrz seed_week_days() w main.py) - te
    nazwy dni sie nie zmieniaja, wiec w odroznieniu od PlanTreningowy nie ma tu
    osobnego skryptu seed_data.py do reczengo uruchamiania.
    """

    __tablename__ = "week_days"

    id = Column(Integer, primary_key=True, index=True)
    day = Column(String, nullable=False, unique=True)  # np. "Poniedziałek"
    day_order = Column(Integer, nullable=False)  # 0 = poniedzialek ... 6 = niedziela

    entries = relationship("DayEntry", back_populates="week_day")


class DayEntry(Base):
    """Wpis Pawla z telefonu: data + waga + kcal dla danego dnia tygodnia.

    Kazdy zapis to NOWY wiersz (historia zachowana, jak Entry w PlanTreningowy) -
    do wyswietlania biezacego tygodnia bierzemy najnowszy wpis per dzien.
    Czyszczenie tygodnia (DELETE /api/admin/week) kasuje te wiersze, ale NIE
    rusza tabeli week_days (nazwy dni zostaja) - to jest "wyczyszczenie tabeli
    na start kolejnego tygodnia" z zadania Pawla.
    """

    __tablename__ = "day_entries"

    id = Column(Integer, primary_key=True, index=True)
    week_day_id = Column(Integer, ForeignKey("week_days.id"), nullable=False)
    entry_date = Column(Date, nullable=True)
    weight_kg = Column(Float, nullable=True)
    kcal = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    week_day = relationship("WeekDay", back_populates="entries")


class WeeklySummary(Base):
    """Historia cotygodniowych podsumowan - NIGDY nie czyszczona (w odroznieniu
    od day_entries). Jeden wiersz na tydzien (unikalny po week_start), dopisywany
    przez POST /api/admin/weekly-summary (wyzwalane co niedziele przez GitHub
    Actions - patrz .github/workflows/weekly-summary.yml).
    """

    __tablename__ = "weekly_summaries"

    id = Column(Integer, primary_key=True, index=True)
    week_start = Column(Date, nullable=False, unique=True)  # poniedzialek
    week_end = Column(Date, nullable=False)  # niedziela
    avg_weight_kg = Column(Float, nullable=True)
    avg_kcal = Column(Float, nullable=True)
    trend = Column(String, nullable=True)
    kcal_recommendation = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
