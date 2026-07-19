from sqlalchemy import Column, Integer, String, Enum
from models.base import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=True, index=True)
    email = Column(String(100), unique=True, nullable=True, index=True)
    wallet_address = Column(String(56), unique=True, nullable=False, index=True)
    role = Column(Enum('user', 'admin', name='user_roles'), nullable=False, default='user', server_default='user')
