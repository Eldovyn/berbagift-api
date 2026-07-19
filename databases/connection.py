from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from configs.database import DatabaseConfig
import time

class DatabaseConnection:
    def __init__(self):
        self.database_url = DatabaseConfig.get_database_url()
        self.engine = self._create_engine_with_retry()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def _create_engine_with_retry(self, max_retries=30, delay=2):
        engine = create_engine(self.database_url, echo=False)
        for attempt in range(1, max_retries + 1):
            try:
                with engine.connect() as conn:
                    conn.execute("SELECT 1")
                print(f"[db] MySQL connection established (attempt {attempt})")
                return engine
            except OperationalError as e:
                if attempt == max_retries:
                    raise RuntimeError(
                        f"Could not connect to MySQL after {max_retries} attempts"
                    ) from e
                print(
                    f"[db] Waiting for MySQL... "
                    f"attempt {attempt}/{max_retries} ({e.orig if e.orig else e})"
                )
                time.sleep(delay)

    def get_db_session(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

db_connection = DatabaseConnection()
engine = db_connection.engine
get_db_session = db_connection.get_db_session
