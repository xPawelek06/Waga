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

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
