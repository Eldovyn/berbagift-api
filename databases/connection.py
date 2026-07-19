from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from configs.database import DatabaseConfig

class DatabaseConnection:
    def __init__(self):
        self.database_url = DatabaseConfig.get_database_url()
        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_db_session(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

db_connection = DatabaseConnection()
engine = db_connection.engine
get_db_session = db_connection.get_db_session
