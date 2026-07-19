import jwt
from datetime import datetime, timedelta
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS_DIR = os.path.join(BASE_DIR, "keys")

PRIVATE_KEY_PATH = os.path.join(KEYS_DIR, "private.pem")
PUBLIC_KEY_PATH = os.path.join(KEYS_DIR, "public.pem")

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def load_or_generate_keys():
    if not os.path.exists(KEYS_DIR):
        os.makedirs(KEYS_DIR)
    if os.path.exists(PRIVATE_KEY_PATH) and os.path.exists(PUBLIC_KEY_PATH):
        with open(PRIVATE_KEY_PATH, "r") as f:
            priv = f.read()
        with open(PUBLIC_KEY_PATH, "r") as f:
            pub = f.read()
        return priv, pub
    print("Generating new RSA keys...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(PRIVATE_KEY_PATH, "wb") as f:
        f.write(private_pem)
    with open(PUBLIC_KEY_PATH, "wb") as f:
        f.write(public_pem)
    return private_pem.decode("utf-8"), public_pem.decode("utf-8")

PRIVATE_KEY, PUBLIC_KEY = load_or_generate_keys()


def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=24)) -> str:
    if not PRIVATE_KEY:
        raise RuntimeError("Private key is not available for JWT signing.")
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, PRIVATE_KEY, algorithm="RS256")
    return encoded_jwt

def verify_access_token(token: str) -> dict:
    if not PUBLIC_KEY:
        raise RuntimeError("Public key is not available for JWT verification.")
    decoded_jwt = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
    return decoded_jwt
