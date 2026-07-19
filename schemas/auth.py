from pydantic import BaseModel

class NonceRequest(BaseModel):
    wallet_address: str

class SignInRequest(BaseModel):
    wallet_address: str
    signature: str

class UpdateProfileRequest(BaseModel):
    username: str | None = None
    email: str | None = None
