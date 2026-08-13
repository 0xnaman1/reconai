from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from recon_ai_api.errors import add_exception_handlers
from recon_ai_api.routes import api_router


def create_app() -> FastAPI:
    app = FastAPI(title="Recon AI API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    add_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
