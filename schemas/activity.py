from pydantic import BaseModel

class UpdateInboxRequest(BaseModel):
    read: bool

class MarkAllReadRequest(BaseModel):
    category: str | None = None
