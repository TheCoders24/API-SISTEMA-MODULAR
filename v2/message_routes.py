from fastapi import APIRouter, Depends

router_v2_ = APIRouter(
    prefix="/test",
    tags=["Test v2"]
)


@router_v2_.get("/hello")
async def v2_messager():
    return {"message": "Pruebas de API v2"}