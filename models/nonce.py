from sqlalchemy import Column, Integer, String, DateTime
from models.base import Base, TimestampMixin

class Nonce(Base, TimestampMixin):
    __tablename__ = "nonces"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    wallet_address = Column(String(56), unique=True, nullable=False, index=True)
    nonce_message = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
