from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
from app.core.logger import logger

# SQLite needs connect_args check_same_thread=False
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True
    )
    logger.info(f"Database engine initialized for URL: {settings.DATABASE_URL.split('@')[-1]}")
except Exception as e:
    logger.error(f"Error initializing DB engine: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def _ensure_schema_columns():
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            cols = [c[1] for c in conn.execute(text("PRAGMA table_info(recovery_plans)")).fetchall()]
            if cols:
                if "rejection_feedback" not in cols:
                    conn.execute(text("ALTER TABLE recovery_plans ADD COLUMN rejection_feedback JSON"))
                if "active_constraints" not in cols:
                    conn.execute(text("ALTER TABLE recovery_plans ADD COLUMN active_constraints JSON"))
                if "revision_count" not in cols:
                    conn.execute(text("ALTER TABLE recovery_plans ADD COLUMN revision_count INTEGER DEFAULT 0"))
                conn.commit()
    except Exception as err:
        logger.warning(f"Schema check error (safe to ignore if table does not exist yet): {err}")

_ensure_schema_columns()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
