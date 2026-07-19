from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models.nonce import Nonce

class NonceDatabase:
    def __init__(self, db: Session):
        self.db = db

    def get_nonce(self, wallet_address: str):
        return self.db.query(Nonce).filter(
            Nonce.wallet_address == wallet_address,
            Nonce.deleted_at.is_(None)
        ).first()

    def upsert_nonce(self, wallet_address: str, nonce_message: str, expires_in_minutes: int = 5):
        existing = self.db.query(Nonce).filter(Nonce.wallet_address == wallet_address).first()
        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        if existing:
            existing.nonce_message = nonce_message
            existing.expires_at = expires_at
            existing.deleted_at = None                                  
            nonce_obj = existing
        else:
            nonce_obj = Nonce(
                wallet_address=wallet_address,
                nonce_message=nonce_message,
                expires_at=expires_at
            )
            self.db.add(nonce_obj)
        self.db.commit()
        self.db.refresh(nonce_obj)
        return nonce_obj
    def delete_nonce(self, wallet_address: str):
        existing = self.get_nonce(wallet_address)
        if existing:
            existing.deleted_at = datetime.utcnow()
            self.db.commit()
