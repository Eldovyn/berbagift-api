from fastapi import APIRouter
from controllers.hello import HelloController
from schemas.response import APIResponse

router = APIRouter(prefix="/api/hello", tags=["hello"])
hello_controller = HelloController()

@router.get("", response_model=APIResponse, status_code=200)
def hello():
    return hello_controller.get_hello_world_data()
