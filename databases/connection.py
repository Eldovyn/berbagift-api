from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from configs.database import DatabaseConfig


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

    def get_db_session(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()


db_connection = DatabaseConnection()
engine = db_connection.engine          # lazy — no connection attempt yet
get_db_session = db_connection.get_db_session
