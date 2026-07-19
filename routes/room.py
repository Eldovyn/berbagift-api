from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from databases.connection import get_db_session
from schemas.response import APIResponse
from controllers.room import RoomController

router = APIRouter(prefix="/api/rooms", tags=["rooms"])

@router.get("/my-rooms", response_model=APIResponse)
def get_my_rooms(
    limit: int = 50, 
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db_session)
):
    room_controller = RoomController(db)
    response_data, status_code = room_controller.get_my_rooms(authorization, limit)
    return JSONResponse(status_code=status_code, content=response_data)

@router.get("/explore", response_model=APIResponse)
def explore_rooms(
    limit: int = 50, 
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db_session)
):
    room_controller = RoomController(db)
    response_data, status_code = room_controller.explore_rooms(authorization, limit)
    return JSONResponse(status_code=status_code, content=response_data)

@router.get("/{identifier}/check-winner", response_model=APIResponse)
def check_winner(
    identifier: str,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db_session)
):
    room_controller = RoomController(db)
    response_data, status_code = room_controller.check_winner(identifier, authorization)
    return JSONResponse(status_code=status_code, content=response_data)

@router.get("/{identifier}/check-claimed", response_model=APIResponse)
def check_claimed(
    identifier: str,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db_session)
):
    room_controller = RoomController(db)
    response_data, status_code = room_controller.check_claimed(identifier, authorization)
    return JSONResponse(status_code=status_code, content=response_data)

@router.get("/{identifier}", response_model=APIResponse)
def get_room_by_id(
    identifier: str,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db_session)
):
    room_controller = RoomController(db)
    response_data, status_code = room_controller.get_room_by_id(identifier, authorization)
    return JSONResponse(status_code=status_code, content=response_data)

@router.get("/{identifier}/participants", response_model=APIResponse)
def get_room_participants(
    identifier: str,
    db: Session = Depends(get_db_session)
):
    room_controller = RoomController(db)
    response_data, status_code = room_controller.get_room_participants(identifier)
    return JSONResponse(status_code=status_code, content=response_data)

@router.get("/{identifier}/activities", response_model=APIResponse)
def get_room_activities(
    identifier: str,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    room_controller = RoomController(db)
    response_data, status_code = room_controller.get_room_activities(identifier, limit)
    return JSONResponse(status_code=status_code, content=response_data)
