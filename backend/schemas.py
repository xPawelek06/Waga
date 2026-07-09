from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class DayEntryCreate(BaseModel):
    week_day_id: int
    entry_date: Optional[date] = None
    weight_kg: Optional[float] = None
    kcal: Optional[int] = None


class DayEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    week_day_id: int
    entry_date: Optional[date]
    weight_kg: Optional[float]
    kcal: Optional[int]
    created_at: datetime


class WeekDayOut(BaseModel):
    id: int
    day: str
    day_order: int
    entry_date: Optional[date] = None
    weight_kg: Optional[float] = None
    kcal: Optional[int] = None


class WeekOut(BaseModel):
    days: List[WeekDayOut]
    avg_weight_7d: Optional[float] = None
    avg_kcal_7d: Optional[float] = None


class WeeklySummaryCreate(BaseModel):
    """Trend i rekomendacja sa oceniane przez wywolujacego (trener-personalny, z
    pelnym kontekstem: cel 80 kg, trend treningowy) - backend juz ich NIE liczy
    mechanicznie. Srednia wagi/kcal wciaz jest liczona tutaj automatycznie z
    day_entries (patrz main.py: run_weekly_summary), bo to fakt, nie ocena."""

    trend: str
    kcal_recommendation: str


class WeeklySummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    week_start: date
    week_end: date
    avg_weight_kg: Optional[float]
    avg_kcal: Optional[float]
    trend: Optional[str]
    kcal_recommendation: Optional[str]
    created_at: datetime
