from sqlalchemy.orm import Session
from databases.user import UserDatabase

class UserController:
    def __init__(self, db: Session):
        self.user_db = UserDatabase(db)

    def get_user_by_username(self, username: str):
        user = self.user_db.get_user_by_username(username)
        if not user:
            return {
                "message": "User tidak ditemukan",
                "data": None,
                "errors": None
            }, 404
        data = {
            "id": user.id,
            "username": user.username,
            "wallet_address": user.wallet_address
        }
        return {
            "message": "Berhasil mendapatkan data user",
            "data": data,
            "errors": None
        }, 200
