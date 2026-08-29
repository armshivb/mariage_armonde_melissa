import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base

_default_db = Path(__file__).parent / "mariage.db"
DB_PATH = Path(os.environ.get("DB_PATH", str(_default_db)))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        cols = [r[1] for r in conn.execute(text("PRAGMA table_info(guests)")).fetchall()]
        for field, definition in {
            "email": "TEXT DEFAULT ''",
            "table_number": "INTEGER DEFAULT 0",
            "seat_number": "TEXT DEFAULT ''",
            "affinity_group": "INTEGER DEFAULT 0",
            "affinity_score": "INTEGER DEFAULT 0",
            "relation_notes": "TEXT DEFAULT ''",
        }.items():
            if field not in cols:
                conn.execute(text(f"ALTER TABLE guests ADD COLUMN {field} {definition}"))
        conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


init_db()
