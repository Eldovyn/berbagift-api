import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from routes.hello import router as hello_router
from routes.auth import router as auth_router
from routes.token import router as token_router
from routes.user import router as user_router
from schemas.response import APIResponse
from databases.connection import engine, db_connection
from models.base import Base
import models.user
import models.nonce
from schemas.indodax import IndodaxCallbackPayload
from services.indodax import validate_withdrawal_request
from services.socket_manager import create_socket_app
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import PlainTextResponse
import logging
from fastapi.middleware.cors import CORSMiddleware
import threading
from contextlib import asynccontextmanager
from configs.mongo_db import connect_db as connect_mongo_db
from controllers.indexer import IndexerController
from routes.activity import router as activity_router
import models.mongo_activity_read  # ensure ActivityRead collection/indexes are created
import models.mongo_listing

logger = logging.getLogger(__name__)       # ensure Listing collection/indexes are created

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Wait for MySQL to be ready before creating tables
    db_connection.wait_for_connection(max_retries=60, delay=3)
    # Create all SQLAlchemy tables (MySQL)
    Base.metadata.create_all(bind=engine)
    # Connect to MongoDB for indexer
    connect_mongo_db()
    indexer = IndexerController()
    thread = threading.Thread(target=indexer.run_loop, daemon=True)
    thread.start()
    yield

app = FastAPI(
    title="BagiTHR API",
    description="Backend API using FastAPI",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.exceptions import RequestValidationError
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = {}
    for error in exc.errors():
        field = str(error["loc"][-1])
        if error["type"] == "missing":
            errors[field] = "IS_REQUIRED"
        else:
            errors[field] = error["msg"]

    return JSONResponse(
        status_code=400,
        content={
            "message": "gagal memproses permintaan",
            "data": None,
            "errors": errors
        }
    )

app.include_router(hello_router)
app.include_router(auth_router)
app.include_router(token_router)
app.include_router(user_router)
app.include_router(activity_router)

from routes.nft import router as nft_router
from routes.room import router as room_router

app.include_router(nft_router)
app.include_router(room_router)

@app.get("/", response_model=APIResponse, status_code=200)
def root():
    return {
        "message": "Welcome to Berbagift API",
        "data": None,
        "errors": None
    }

@app.post("/indodax-callback", response_class=PlainTextResponse)
async def indodax_withdraw_callback(
    request_id: str = Form(...),
    withdraw_currency: str = Form(...),
    withdraw_address: str = Form(...),
    withdraw_amount: str = Form(...),
    withdraw_memo: str = Form(None),
    requester_ip: str = Form(...),
    request_date: str = Form(...)
):
    logger.info(f"Menerima Callback Indodax! ID: {request_id} | Amount: {withdraw_amount} {withdraw_currency}")
    is_valid = True
    if is_valid:
        return "ok"
    raise HTTPException(status_code=400, detail="Validasi data withdrawal gagal")

# Wrap FastAPI app with Socket.IO support
# Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000
app = create_socket_app(app)
