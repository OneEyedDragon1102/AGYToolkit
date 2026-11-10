from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from {{PACKAGE_NAME}}.api.routes.health import router as health_router
from {{PACKAGE_NAME}}.api.routes.items import router as items_router


def create_app() -> FastAPI:
    application = FastAPI(
        title="{{PROJECT_NAME}}",
        version="0.1.0",
        description="Production FastAPI service bootstrapped with AGYToolkit",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health_router)
    application.include_router(items_router)

    return application


app = create_app()
