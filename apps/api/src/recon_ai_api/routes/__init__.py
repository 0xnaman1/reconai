from fastapi import APIRouter

from recon_ai_api.routes.health import router as health_router
from recon_ai_api.routes.reconciliations import router as reconciliations_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(reconciliations_router)
