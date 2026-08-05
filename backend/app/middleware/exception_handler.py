from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.schemas.common import APIResponse


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content=APIResponse.error(message=str(exc)).model_dump())


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        {"field": ".".join(str(l) for l in e["loc"]), "message": e["msg"]} for e in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=APIResponse(code=422, message="参数校验失败", data=errors).model_dump(),
    )
