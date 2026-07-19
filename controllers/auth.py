import base64
import secrets
from datetime import datetime
from stellar_sdk import Keypair
from sqlalchemy.orm import Session
from schemas.auth import NonceRequest, SignInRequest, UpdateProfileRequest
from databases.user import UserDatabase
from databases.nonce import NonceDatabase
import os
from utils.jwt import create_access_token, verify_access_token
import jwt
from dotenv import load_dotenv

load_dotenv()

class AuthController:
    def __init__(self, db: Session):
        self.user_db = UserDatabase(db)
        self.nonce_db = NonceDatabase(db)

    def _fetch_stellar_balances(self, wallet_address: str):
        xlm_balance = 0.0
        rpk_balance = 0.0
        try:
            from stellar_sdk import Server
            from stellar_sdk.exceptions import NotFoundError
            server = Server("https://horizon-testnet.stellar.org")
            try:
                account = server.accounts().account_id(wallet_address).call()
                for b in account.get("balances", []):
                    if b.get("asset_type") == "native":
                        xlm_balance = float(b.get("balance", 0.0))
            except NotFoundError:
                pass
        except Exception:
            pass
        try:
            from stellar_sdk import SorobanServer, TransactionBuilder, Network, Account, scval
            from stellar_sdk.xdr import SCVal
            import os
            contract_id = os.getenv("RPK_CONTRACT", "CAXMJUKELFC7THVUKVH4NA5RYUDLORCKSZ5HTOPOMEXRMZJLFHKZJCQZ")
            contract_id = contract_id.strip('"').strip("'")
            rpc_server = SorobanServer("https://soroban-testnet.stellar.org")
            dummy = Account("GBBD47IF6LWK7P7MDEVSCWR7DPUWV3NY3DTQEVFL4NAT4AQH3ZLLFLA5", 1)
            tx = (
                TransactionBuilder(
                    source_account=dummy,
                    network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
                    base_fee=100,
                )
                .append_invoke_contract_function_op(
                    contract_id=contract_id,
                    function_name="balance",
                    parameters=[scval.to_address(wallet_address)],
                )
                .set_timeout(30)
                .build()
            )
            sim = rpc_server.simulate_transaction(tx)
            if sim and sim.results:
                xdr_str = sim.results[0].xdr
                sc_val = SCVal.from_xdr(xdr_str)
                if sc_val.i128 is not None:
                    hi = sc_val.i128.hi.int64
                    lo = sc_val.i128.lo.uint64
                    val = (hi << 64) | lo
                    rpk_balance = float(val) / 10000000.0
        except Exception as e:
            print(f"[!] Error fetching RPK via Soroban: {e}")
            pass
        return {"XLM": xlm_balance, "RPK": rpk_balance}


    def generate_nonce(self, request: NonceRequest):
        random_nonce = secrets.token_hex(16)
        message = f"Welcome to Berbagift!\n\nPlease sign this message to authenticate.\nNonce: {random_nonce}"
        self.nonce_db.upsert_nonce(wallet_address=request.wallet_address, nonce_message=message)
        return {
            "message": "Nonce generated successfully",
            "data": {
                "nonce": message
            },
            "errors": None
        }, 201

    def sign_in(self, request: SignInRequest):
        stored_nonce = self.nonce_db.get_nonce(request.wallet_address)
        if not stored_nonce:
            return {
                "message": "Authentication failed",
                "data": None,
                "errors": {
                    "wallet_address": "IS_INVALID"
                }
            }, 400
        if datetime.utcnow() > stored_nonce.expires_at:
            self.nonce_db.delete_nonce(request.wallet_address)
            return {
                "message": "Authentication failed",
                "data": None,
                "errors": {
                    "wallet_address": "IS_INVALID"
                }
            }, 400

        try:
            kp = Keypair.from_public_key(request.wallet_address)
            try:
                signature_bytes = base64.b64decode(request.signature)
            except Exception:
                signature_bytes = bytes.fromhex(request.signature)
            SIGN_MESSAGE_PREFIX = "Stellar Signed Message:\n"
            data_to_verify = (SIGN_MESSAGE_PREFIX + stored_nonce.nonce_message).encode('utf-8')
            import hashlib
            data_hash = hashlib.sha256(data_to_verify).digest()
            try:
                kp.verify(data_hash, signature_bytes)
            except Exception:
                kp.verify(data_to_verify, signature_bytes)
        except Exception as e:
            return {
                "message": "Signature verification failed",
                "data": None,
                "errors": {
                    "signature": "IS_INVALID"
                }
            }, 400

        self.nonce_db.delete_nonce(request.wallet_address)

        user = self.user_db.get_user_by_wallet(request.wallet_address)
        if not user:
            user = self.user_db.create_user(
                wallet_address=request.wallet_address,
                username=None
            )
            status_code = 201
            message = "User registered and logged in successfully"
        else:
            if user.username == user.wallet_address or user.username == user.wallet_address[:50]:
                user = self.user_db.update_user(user, clear_username=True)
            status_code = 201
            message = "Login successful"
        access_token = create_access_token(
            data={"sub": str(user.id), "wallet_address": user.wallet_address}
        )
        import urllib.parse
        avatar_name = urllib.parse.quote(user.username) if user.username else "USR"
        avatar_url = f"https://ui-avatars.com/api/?name={avatar_name}&background=D1FAE5&color=047857&rounded=true"
        return {
            "message": message,
            "data": {
                "user_id": user.id,
                "username": user.username,
                "wallet_address": user.wallet_address,
                "role": user.role,
                "avatar_url": avatar_url,
                "access_token": access_token
            },
            "errors": None
        }, status_code

    def get_me(self, authorization: str | None):
        if not authorization or not authorization.startswith("Bearer "):
            return {
                "message": "Authentication failed: Missing or invalid Authorization header",
                "data": None,
                "errors": None
            }, 401
        token = authorization.split(" ")[1]
        try:
            payload = verify_access_token(token)
        except jwt.ExpiredSignatureError:
            return {
                "message": "Token has expired",
                "data": None,
                "errors": None
            }, 401
        except jwt.InvalidTokenError:
            return {
                "message": "Invalid token",
                "data": None,
                "errors": None
            }, 401
        user_id = payload.get("sub")
        if not user_id:
            return {
                "message": "Invalid token payload",
                "data": None,
                "errors": None
            }, 401
        user = self.user_db.get_user_by_id(int(user_id))
        if not user:
            return {
                "message": "User not found",
                "data": None,
                "errors": None
            }, 404
        if user.username == user.wallet_address or user.username == user.wallet_address[:50]:
            user = self.user_db.update_user(user, clear_username=True)
        balances = self._fetch_stellar_balances(user.wallet_address)
        balances_idr = {"XLM": 0, "RPK": 0}
        try:
            from controllers.token import TokenController
            token_controller = TokenController()
            prices, _ = token_controller.get_prices_waterfall()
            xlm_price = prices.get("XLM", 0)
            usdc_price = prices.get("USDC", 0)
            
            xlm_idr = int(round(balances.get("XLM", 0.0) * xlm_price))
            rpk_idr = int(round(balances.get("RPK", 0.0)))
            
            balances_idr["XLM"] = xlm_idr
            balances_idr["RPK"] = rpk_idr
            balances_idr["total"] = xlm_idr + rpk_idr
            
            if xlm_price > 0:
                balances["total_xlm"] = balances.get("XLM", 0.0) + (rpk_idr / xlm_price)
            else:
                balances["total_xlm"] = balances.get("XLM", 0.0)
                
        except Exception as e:
            print(f"[!] Warning: Failed to calculate balance in IDR. Error: {e}")
        import urllib.parse
        avatar_name = urllib.parse.quote(user.username) if user.username else "USR"
        avatar_url = f"https://ui-avatars.com/api/?name={avatar_name}&background=D1FAE5&color=047857&rounded=true"
        return {
            "message": "Successfully retrieved user data",
            "data": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "wallet_address": user.wallet_address,
                "role": user.role,
                "avatar_url": avatar_url,
                "balances": balances,
                "balances_idr": balances_idr
            },
            "errors": None
        }, 200

    def update_me(self, authorization: str | None, request: UpdateProfileRequest):
        if not authorization or not authorization.startswith("Bearer "):
            return {
                "message": "Authentication failed: Missing or invalid Authorization header",
                "data": None,
                "errors": None
            }, 401
        token = authorization.split(" ")[1]
        try:
            payload = verify_access_token(token)
        except jwt.ExpiredSignatureError:
            return {
                "message": "Token has expired",
                "data": None,
                "errors": None
            }, 401
        except jwt.InvalidTokenError:
            return {
                "message": "Invalid token",
                "data": None,
                "errors": None
            }, 401
        user_id_str = payload.get("sub")
        if not user_id_str:
            return {
                "message": "Invalid token payload",
                "data": None,
                "errors": None
            }, 401
        user_id = int(user_id_str)
        user = self.user_db.get_user_by_id(user_id)
        if not user:
            return {
                "message": "User not found",
                "data": None,
                "errors": None
            }, 404

        new_username = request.username
        new_email = request.email

        errors = {}

        if new_username is not None:
            if len(new_username) > 50:
                errors["username"] = "TOO_LONG"
            elif self.user_db.check_username_exists(new_username, user_id):
                return {
                    "message": "Username already taken",
                    "data": None,
                    "errors": None
                }, 409

        if new_email is not None:
            if len(new_email) > 100:
                errors["email"] = "TOO_LONG"
            elif self.user_db.check_email_exists(new_email, user_id):
                return {
                    "message": "Email already taken",
                    "data": None,
                    "errors": None
                }, 409

        if errors:
            return {
                "message": "Validation failed",
                "data": None,
                "errors": errors
            }, 400

        updated_user = self.user_db.update_user(
            user=user,
            username=new_username,
            email=new_email
        )

        import urllib.parse
        avatar_name = urllib.parse.quote(updated_user.username) if updated_user.username else "USR"
        avatar_url = f"https://ui-avatars.com/api/?name={avatar_name}&background=D1FAE5&color=047857&rounded=true"

        return {
            "message": "Profile updated successfully",
            "data": {
                "id": updated_user.id,
                "username": updated_user.username,
                "email": updated_user.email,
                "wallet_address": updated_user.wallet_address,
                "role": updated_user.role,
                "avatar_url": avatar_url
            },
            "errors": None
        }, 201
