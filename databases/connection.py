from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from configs.database import DatabaseConfig
import time


class DatabaseConnection:
    def __init__(self):
        self.database_url = DatabaseConfig.get_database_url()
        self._engine = None
        self._SessionLocal = None

    @property
    def engine(self):
        if self._engine is None:
            self._engine = create_engine(self.database_url, echo=False)
        return self._engine

    @property
    def SessionLocal(self):
        if self._SessionLocal is None:
            self._SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )
        return self._SessionLocal

    def wait_for_connection(self, max_retries: int = 60, delay: float = 3):
        """Block until a test query succeeds or max_retries exhausted."""
        eng = self.engine
        for attempt in range(1, max_retries + 1):
            try:
                with eng.connect() as conn:
                    conn.execute(text("SELECT 1"))
                print(f"[db] MySQL connection established (attempt {attempt})")
                return True
            except OperationalError as e:
                if attempt == max_retries:
                    raise RuntimeError(
                        f"Could not connect to MySQL after {max_retries} attempts "
                        f"(last error: {e.orig if e.orig else e})"
                    ) from e
                print(
                    f"[db] Waiting for MySQL... "
                    f"attempt {attempt}/{max_retries} ({e.orig if e.orig else e})"
                )
                time.sleep(delay)
        return False

    def get_db_session(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()


db_connection = DatabaseConnection()
engine = db_connection.engine          # lazy — no connection attempt yet
get_db_session = db_connection.get_db_session
