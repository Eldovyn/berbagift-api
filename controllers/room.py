from sqlalchemy.orm import Session
import jwt
from utils.jwt import verify_access_token
from databases.mongo_room import RoomDatabase
from databases.user import UserDatabase

class RoomController:
    def __init__(self, db: Session):
        self.db = db
        self.user_db = UserDatabase(db)

    def _attach_creator_info(self, room_data: dict) -> dict:
        owner_address = room_data.get("owner")
        if owner_address:
            user = self.user_db.get_user_by_wallet(owner_address)
            if user and user.username:
                username = user.username
                initials = username[:2].upper()
            else:
                username = owner_address
                initials = "U"
            
            room_data["creator"] = {
                "username": username,
                "initials": initials,
                "role": "Room Creator"
            }
        return room_data

    def _attach_winners_info(self, room_data: dict) -> dict:
        winners = room_data.get("winners")
        if isinstance(winners, list) and len(winners) > 0:
            formatted_winners = []
            for wallet in winners:
                if isinstance(wallet, str):
                    user = self.user_db.get_user_by_wallet(wallet)
                    if user and user.username:
                        username = f"@{user.username}"
                    else:
                        username = f"@{wallet}"
                    formatted_winners.append({
                        "wallet_address": wallet,
                        "username": username
                    })
                else:
                    formatted_winners.append(wallet)
            room_data["winners"] = formatted_winners
        elif room_data.get("status") != "Completed":
            # Remove empty array so frontend falls back to total_winners count before draw
            if "winners" in room_data:
                del room_data["winners"]
        return room_data

    def _attach_reward_idr(self, room_data: dict) -> dict:
        try:
            from controllers.token import TokenController
            token_controller = TokenController()
            prices, _ = token_controller.get_prices_waterfall()
            
            reward_str = room_data.get("reward", "0 XLM")
            parts = reward_str.split(" ")
            
            num_str = parts[0].replace(',', '')
            try:
                amount = float(num_str)
            except ValueError:
                amount = 0.0
                
            symbol = parts[1] if len(parts) > 1 else "XLM"
            
            if symbol == "XLM":
                rate = prices.get("XLM", 1600)
            elif symbol == "RPK":
                rate = prices.get("RPK", 1)
            else:
                rate = 1
                
            idr_value = int(round(amount * rate))
            room_data["rewardPoolIdr"] = f"Rp {idr_value:,}".replace(',', '.')
        except Exception as e:
            print(f"[!] Warning: Failed to calculate reward in IDR. Error: {e}")
            room_data["rewardPoolIdr"] = "Rp 0"
        return room_data

    def _attach_participants_preview(self, room_data: dict) -> dict:
        """Attach up to 5 participant previews (username + initials) to room data."""
        room_id = room_data.get("room_id")
        if room_id is None:
            return room_data
        participants = RoomDatabase.get_participants(room_id)
        preview = []
        for p in participants[:5]:
            wallet = p.get("wallet_address")
            user = self.user_db.get_user_by_wallet(wallet)
            if user and user.username:
                username = f"@{user.username}"
                initials = user.username[:2].upper()
            else:
                username = f"@{wallet}"
                initials = "U"
            preview.append({
                "wallet_address": wallet,
                "username": username,
                "initials": initials
            })
        room_data["participants"] = preview
        return room_data

    def get_my_rooms(self, authorization: str | None, limit: int = 50):
        if not authorization or not authorization.startswith("Bearer "):
            return {
                "message": "Authentication failed: Missing or invalid Authorization header",
                "data": None,
                "errors": {"Auth": "IS_INVALID"}
            }, 401

        token = authorization.split(" ")[1]
        try:
            payload = verify_access_token(token)
            user_id = payload.get("sub")
        except jwt.ExpiredSignatureError:
            return {
                "message": "Token has expired",
                "data": None,
                "errors": {"Auth": "IS_INVALID"}
            }, 401
        except jwt.InvalidTokenError:
            return {
                "message": "Invalid token",
                "data": None,
                "errors": {"Auth": "IS_INVALID"}
            }, 401

        user = self.user_db.get_user_by_id(user_id)
        if not user:
            return {
                "message": "Authentication failed: User not found",
                "data": None,
                "errors": {"Auth": "IS_INVALID"}
            }, 404

        wallet_address = user.wallet_address
        if not wallet_address:
            return {
                "message": "Wallet not found",
                "data": None,
                "errors": {"Auth": "IS_INVALID"}
            }, 400

        try:
            rooms = RoomDatabase.get_rooms_by_owner(wallet_address, limit)
            
            # Format _id and mapping if necessary
            formatted_rooms = []
            for room in rooms:
                id_str = str(room.get("_id", ""))
                if isinstance(room.get("_id"), dict):
                    id_str = str(room["_id"].get("$oid", ""))

                room_data = room.copy()
                room_data["id"] = room_data.get("transaction_hash") or id_str
                if "_id" in room_data:
                    del room_data["_id"]
                room_data = self._attach_creator_info(room_data)
                room_data = self._attach_winners_info(room_data)
                room_data = self._attach_participants_preview(room_data)
                formatted_rooms.append(room_data)

            return {
                "message": "Successfully retrieved user rooms",
                "data": formatted_rooms,
                "errors": None
            }, 200
        except Exception as e:
            return {
                "message": "Internal server error",
                "data": None,
                "errors": {"Exception": str(e)}
            }, 500

    def explore_rooms(self, authorization: str | None, limit: int = 50):
        wallet_address = None
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            try:
                payload = verify_access_token(token)
                user_id = payload.get("sub")
                user = self.user_db.get_user_by_id(user_id)
                if user:
                    wallet_address = user.wallet_address
            except Exception:
                pass

        try:
            rooms = RoomDatabase.get_explore_rooms(wallet_address, limit)
            
            formatted_rooms = []
            for room in rooms:
                id_str = str(room.get("_id", ""))
                if isinstance(room.get("_id"), dict):
                    id_str = str(room["_id"].get("$oid", ""))

                room_data = room.copy()
                room_data["id"] = room_data.get("transaction_hash") or id_str
                if "_id" in room_data:
                    del room_data["_id"]
                room_data = self._attach_creator_info(room_data)
                room_data = self._attach_winners_info(room_data)
                room_data = self._attach_participants_preview(room_data)
                formatted_rooms.append(room_data)

            return {
                "message": "Successfully retrieved explore rooms",
                "data": formatted_rooms,
                "errors": None
            }, 200
        except Exception as e:
            return {
                "message": "Internal server error",
                "data": None,
                "errors": {"Exception": str(e)}
            }, 500

    def get_room_by_id(self, identifier: str, authorization: str | None = None):
        wallet_address = None
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            try:
                payload = verify_access_token(token)
                user_id = payload.get("sub")
                user = self.user_db.get_user_by_id(user_id)
                if user:
                    wallet_address = user.wallet_address
            except Exception:
                pass

        try:
            room = RoomDatabase.get_room_by_id(identifier)
            if not room:
                return {
                    "message": "Room not found",
                    "data": None,
                    "errors": {"Not Found": "Room does not exist"}
                }, 404

            is_owner = (room.get("owner") == wallet_address)
            is_participant = False

            if wallet_address:
                is_participant = RoomDatabase.is_participant(room.get("room_id"), wallet_address)

            id_str = str(room.get("_id", ""))
            if isinstance(room.get("_id"), dict):
                id_str = str(room["_id"].get("$oid", ""))

            room_data = room.copy()
            room_data["id"] = id_str
            if "_id" in room_data:
                del room_data["_id"]
            room_data = self._attach_creator_info(room_data)
            room_data = self._attach_winners_info(room_data)
            room_data = self._attach_reward_idr(room_data)
            
            # Add is_joined attribute
            room_data["is_joined"] = is_owner or is_participant
            room_data["is_owner"] = is_owner

            return {
                "message": "Successfully retrieved room",
                "data": room_data,
                "errors": None
            }, 200
        except Exception as e:
            return {
                "message": "Internal server error",
                "data": None,
                "errors": {"Exception": str(e)}
            }, 500

    def get_room_participants(self, identifier: str):
        try:
            room = RoomDatabase.get_room_by_id(identifier)
            if not room:
                return {
                    "message": "Room not found",
                    "data": None,
                    "errors": {"Not Found": "Room does not exist"}
                }, 404
                
            room_id = room.get("room_id")
            participants_data = RoomDatabase.get_participants(room_id)
            
            result = []
            for p in participants_data:
                wallet = p.get("wallet_address")
                user = self.user_db.get_user_by_wallet(wallet)
                
                if user and user.username:
                    username = f"@{user.username}"
                    initials = user.username[:2].upper()
                else:
                    username = f"@{wallet}"
                    initials = "U"
                    
                result.append({
                    "username": username,
                    "initials": initials,
                    "wallet_address": wallet,
                    "joined_at": p.get("created_at")
                })
                
            return {
                "message": "Successfully retrieved room participants",
                "data": result,
                "errors": None
            }, 200
        except Exception as e:
            return {
                "message": "Internal server error",
                "data": None,
                "errors": {"Exception": str(e)}
            }, 500

    def _format_activities(self, activities: list) -> list:
        """Format raw activity dicts into the standard API response shape."""
        result = []
        username_cache = {}

        def get_uname(addr):
            if not addr: return "Unknown"
            if addr not in username_cache:
                user = self.user_db.get_user_by_wallet(addr)
                if user and user.username:
                    username_cache[addr] = f"@{user.username}"
                else:
                    username_cache[addr] = f"@{addr}"
            return username_cache[addr]

        def extract_id(act):
            raw = act.get("_id")
            if isinstance(raw, dict):
                return raw.get("$oid", str(raw))
            return str(raw) if raw else ""

        for act in activities:
            wallet = act.get("wallet_address", "")
            username = get_uname(wallet)
            act_type = act.get("activity_type", "")

            message = ""
            if act_type == "Joined Room":
                message = f"{username} joined the room."
            elif act_type == "Left Room":
                message = f"{username} left the room."
            elif act_type == "Claimed Reward":
                message = f"{username} claimed their reward."
            elif act_type == "Completed Room":
                message = "The giveaway room has been completed and rewards drawn."
                username = "Berbagift System"
                wallet = "System"

            result.append({
                "id": extract_id(act),
                "username": username,
                "wallet_address": wallet,
                "activity_type": act_type,
                "message": message,
                "datetime": act.get("datetime")
            })
        return result

    def get_room_activities(self, identifier: str, limit: int = 100):
        try:
            room = RoomDatabase.get_room_by_id(identifier)
            if not room:
                return {
                    "message": "Room not found",
                    "data": None,
                    "errors": {"Not Found": "Room does not exist"}
                }, 404
                
            room_id = room.get("room_id")
            from databases.mongo_activity import ActivityDatabase
            
            activities = ActivityDatabase.get_room_activities(room_id, limit)
            result = self._format_activities(activities)
                
            return {
                "message": "Successfully retrieved room activities",
                "data": result,
                "errors": None
            }, 200
        except Exception as e:
            return {
                "message": "Internal server error",
                "data": None,
                "errors": {"Exception": str(e)}
            }, 500

    def check_winner(self, identifier: str, authorization: str | None):
        # ── Auth guard ──────────────────────────────────────────────────────────
        if not authorization or not authorization.startswith("Bearer "):
            return {
                "message": "Authentication required",
                "data": None,
                "errors": {"Auth": "IS_INVALID"}
            }, 401

        token = authorization.split(" ")[1]
        try:
            payload = verify_access_token(token)
            user_id = payload.get("sub")
        except jwt.ExpiredSignatureError:
            return {
                "message": "Token has expired",
                "data": None,
                "errors": {"Auth": "IS_INVALID"}
            }, 401
        except jwt.InvalidTokenError:
            return {
                "message": "Invalid token",
                "data": None,
                "errors": {"Auth": "IS_INVALID"}
            }, 401

        user = self.user_db.get_user_by_id(user_id)
        if not user:
            return {
                "message": "User not found",
                "data": None,
                "errors": {"Auth": "IS_INVALID"}
            }, 404

        wallet_address = user.wallet_address
        if not wallet_address:
            return {
                "message": "Wallet address not found on account",
                "data": None,
                "errors": {"wallet": "NOT_FOUND"}
            }, 400

        # ── Resolve room ────────────────────────────────────────────────────────
        try:
            room = RoomDatabase.get_room_by_id(identifier)
            if not room:
                return {
                    "message": "Room not found",
                    "data": None,
                    "errors": {"room": "NOT_FOUND"}
                }, 404

            room_id = room.get("room_id")
            result = RoomDatabase.check_winner(room_id, wallet_address)

            if not result["found"]:
                return {
                    "message": "Room not found",
                    "data": None,
                    "errors": {"room": "NOT_FOUND"}
                }, 404

            if result["reason"] == "draw_not_completed":
                return {
                    "message": "Draw has not been completed yet",
                    "data": {"is_winner": False, "wallet_address": wallet_address},
                    "errors": None
                }, 200

            return {
                "message": "Winner check successful",
                "data": {
                    "is_winner": result["is_winner"],
                    "wallet_address": wallet_address,
                    "room_id": room_id
                },
                "errors": None
            }, 200

        except Exception as e:
            return {
                "message": "Internal server error",
                "data": None,
                "errors": {"Exception": str(e)}
            }, 500

    def check_claimed(self, identifier: str, authorization: str | None):
        # ── Auth guard ──────────────────────────────────────────────────────────
        if not authorization or not authorization.startswith("Bearer "):
            return {
                "message": "Authentication required",
                "data": None,
                "errors": {"Auth": "IS_INVALID"}
            }, 401

        token = authorization.split(" ")[1]
        try:
            payload = verify_access_token(token)
            user_id = payload.get("sub")
        except jwt.ExpiredSignatureError:
            return {
                "message": "Token has expired",
                "data": None,
                "errors": {"Auth": "IS_INVALID"}
            }, 401
        except jwt.InvalidTokenError:
            return {
                "message": "Invalid token",
                "data": None,
                "errors": {"Auth": "IS_INVALID"}
            }, 401

        user = self.user_db.get_user_by_id(user_id)
        if not user:
            return {
                "message": "User not found",
                "data": None,
                "errors": {"Auth": "IS_INVALID"}
            }, 404

        wallet_address = user.wallet_address
        if not wallet_address:
            return {
                "message": "Wallet address not found on account",
                "data": None,
                "errors": {"wallet": "NOT_FOUND"}
            }, 400

        # ── Resolve room & check claimed ────────────────────────────────────────
        try:
            room = RoomDatabase.get_room_by_id(identifier)
            if not room:
                return {
                    "message": "Room not found",
                    "data": None,
                    "errors": {"room": "NOT_FOUND"}
                }, 404

            room_id = room.get("room_id")
            result = RoomDatabase.check_claimed(room_id, wallet_address)

            if not result["found"]:
                reason = result.get("reason", "unknown")
                msg = "Room not found" if reason == "room_not_found" else "You are not a participant in this room"
                return {
                    "message": msg,
                    "data": {"is_claimed": False, "wallet_address": wallet_address},
                    "errors": {"participant": reason.upper()}
                }, 200 if reason == "not_participant" else 404

            return {
                "message": "Claim status check successful",
                "data": {
                    "is_claimed": result["is_claimed"],
                    "wallet_address": wallet_address,
                    "room_id": room_id
                },
                "errors": None
            }, 200

        except Exception as e:
            return {
                "message": "Internal server error",
                "data": None,
                "errors": {"Exception": str(e)}
            }, 500
