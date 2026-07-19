from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse

from schemas.response import APIResponse
from controllers.token import TokenController

router = APIRouter(prefix="/api/tokens", tags=["tokens"])

@router.get("/prices", response_model=APIResponse)
def get_token_prices(authorization: str | None = Header(default=None)):
    token_controller = TokenController()
    response_data, status_code = token_controller.get_prices(authorization)
    return JSONResponse(status_code=status_code, content=response_data)

@router.get("/market-stats", response_model=APIResponse)
def get_market_stats():
    token_controller = TokenController()
    response_data, status_code = token_controller.get_market_stats()
    return JSONResponse(status_code=status_code, content=response_data)

@router.get("/registry", response_model=APIResponse)
def get_registry_tokens():
    from databases.mongo_registry import RegistryDatabase
    try:
        tokens = RegistryDatabase.get_all_active_tokens()
        return JSONResponse(status_code=200, content={
            "message": "Successfully retrieved tokens",
            "data": tokens,
            "errors": None
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "message": "Internal server error",
            "data": None,
            "errors": {"Exception": str(e)}
        })
