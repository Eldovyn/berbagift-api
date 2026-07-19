from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from schemas.response import APIResponse
from controllers.user import UserController
from databases.connection import get_db_session

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/{username}", response_model=APIResponse)
def get_user_by_username(username: str, db: Session = Depends(get_db_session)):
    user_controller = UserController(db)
    response_data, status_code = user_controller.get_user_by_username(username)
    return JSONResponse(status_code=status_code, content=response_data)
