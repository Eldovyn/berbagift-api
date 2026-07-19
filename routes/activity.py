from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from databases.connection import get_db_session
from schemas.response import APIResponse
from controllers.activity import ActivityController

router = APIRouter(prefix="/api/activities", tags=["activities"])

@router.get("", response_model=APIResponse)
def get_activities(
    limit: int = 50, 
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db_session)
):
    activity_controller = ActivityController(db)
    response_data, status_code = activity_controller.get_activities(authorization, limit)
    return JSONResponse(status_code=status_code, content=response_data)

@router.get("/inbox", response_model=APIResponse)
def get_inbox(
    limit: int = 50, 
    category: str | None = None,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db_session)
):
    activity_controller = ActivityController(db)
    response_data, status_code = activity_controller.get_inbox(authorization, limit, category)
    return JSONResponse(status_code=status_code, content=response_data)


from schemas.activity import UpdateInboxRequest, MarkAllReadRequest

@router.patch("/inbox/{activity_id}", response_model=APIResponse)
def update_inbox_item(
    activity_id: str,
    payload: UpdateInboxRequest,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db_session)
):
    activity_controller = ActivityController(db)
    response_data, status_code = activity_controller.update_inbox_item(authorization, activity_id, {"read": payload.read})
    return JSONResponse(status_code=status_code, content=response_data)

@router.post("/inbox/mark-all-read", response_model=APIResponse)
def mark_all_read(
    payload: MarkAllReadRequest,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db_session)
):
    activity_controller = ActivityController(db)
    response_data, status_code = activity_controller.mark_all_read(authorization, payload.category)
    return JSONResponse(status_code=status_code, content=response_data)
