from contextlib import contextmanager

from app.db.session import SessionLocal


@contextmanager
def worker_db_session():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()