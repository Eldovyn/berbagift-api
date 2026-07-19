from pydantic import BaseModel
from typing import Optional

class IndodaxCallbackPayload(BaseModel):
    request_id: str
    withdraw_currency: str
    withdraw_address: str
    withdraw_amount: str
    withdraw_memo: Optional[str] = None
    requester_ip: str
    request_date: str