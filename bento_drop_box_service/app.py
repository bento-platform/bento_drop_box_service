from bento_lib.responses.fastapi_errors import http_exception_handler_factory, validation_exception_handler
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import get_config
from .logger import get_logger
from .routes import drop_box_router


application = FastAPI()
application.include_router(drop_box_router)

config_for_setup = get_config()

application.add_middleware(
    CORSMiddleware,
    allow_origins=config_for_setup.cors_origins,
    allow_headers=["Authorization"],
    allow_credentials=True,
)

application.exception_handler(StarletteHTTPException)(http_exception_handler_factory(get_logger(config_for_setup)))
application.exception_handler(RequestValidationError)(validation_exception_handler)
