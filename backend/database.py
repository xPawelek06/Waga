import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Lokalnie (dev) czyta backend/.env, jesli istnieje - w produkcji (Render) i tak
# uzywane sa prawdziwe zmienne srodowiskowe z dashboardu, wiec to nieszkodliwe.
load_dotenv()

# Baza produkcyjna to Neon (neon.tech, darmowy Postgres bez limitu czasowego -
# patrz render.yaml). Osobny projekt Neon niz PlanTreningowy - te dwie appki nie
# dziela bazy. Niektorzy dostawcy podaja DATABASE_URL w formie "postgres://...",
# a SQLAlchemy 1.4+ / psycopg2 wymaga prefiksu "postgresql://" - konwersja ponizej.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./local.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# pool_pre_ping/pool_recycle (2026-07-23): Neon zamyka niewykorzystywane
# polaczenia (idle/suspend), a domyslny pool SQLAlchemy tego nie wykrywa - proba
# ponownego uzycia martwego polaczenia z puli konczyla sie
# "psycopg2.OperationalError: SSL connection has been closed unexpectedly" (500
# na GET/POST /api/entries), zwlaszcza po dluzszej przerwie bez ruchu (np.
# wieczorem). pool_pre_ping robi tanie "SELECT 1" przed kazdym uzyciem
# polaczenia z puli i po cichu je odtwarza, jesli jest martwe; pool_recycle
# dodatkowo wymusza odswiezenie polaczen starszych niz 5 min, zanim Neon zdazy
# je samo zamknac.
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=300,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
