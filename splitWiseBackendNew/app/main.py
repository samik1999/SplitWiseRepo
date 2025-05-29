# app/main.py
# Main application file: initializes FastAPI, sets up database, Redis, and includes API routes.

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.database import initialize_database_tables
from app.redis_utils import initialize_redis_connection_pool, close_down_redis_connection_pool
from app.routers import api_router 
from app.schemas import StandardApiResponse, ErrorApiResponse, ApiErrorDetail

app = FastAPI(
    title=settings.PROJECT_NAME, 
    version="0.0.1-debug",
    description="A very simplified Splitwise-like API.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc"
)

@app.on_event("startup")
async def application_startup_tasks():
    print(f"INFO:     Starting up: {app.title}...")
    initialize_database_tables()
    await initialize_redis_connection_pool()
    print("INFO:     Application startup tasks complete.")

@app.on_event("shutdown")
async def application_shutdown_tasks():
    print(f"INFO:     Shutting down: {app.title}...")
    await close_down_redis_connection_pool()
    print("INFO:     Application shutdown tasks complete.")

@app.exception_handler(HTTPException)
async def custom_fastapi_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorApiResponse(
            message=exc.detail,
            errors=[ApiErrorDetail(error_message=exc.detail)]
        ).model_dump(exclude_none=True)
    )

@app.exception_handler(RequestValidationError)
async def pydantic_request_validation_error_handler(request: Request, exc: RequestValidationError):
    list_of_error_details: List[ApiErrorDetail] = []
    for error_item_dict in exc.errors():
        field_location_path = " -> ".join(str(loc_part) for loc_part in error_item_dict.get("loc", []))
        list_of_error_details.append(ApiErrorDetail(
            field=field_location_path if field_location_path else "general_validation",
            error_message=error_item_dict.get("msg")
        ))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorApiResponse(
            message="Input validation failed. Please check the data you provided.",
            errors=list_of_error_details
        ).model_dump(exclude_none=True)
    )

@app.exception_handler(ValueError)
async def python_value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorApiResponse(
            message=str(exc) or "An invalid value was encountered or the operation is not allowed.",
            errors=[ApiErrorDetail(error_message=str(exc))]
        ).model_dump(exclude_none=True)
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Root"], response_model=StandardApiResponse[dict])
async def api_application_root():
    return StandardApiResponse[dict](
        message=f"Welcome to {app.title}! API is active.",
        data={
            "project_version": app.version,
            "api_documentation_swagger_ui": f"{settings.API_V1_STR}/docs",
        }
    )