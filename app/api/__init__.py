from app.api.routes import router
from app.api.websocket import ws_router
from app.api.auth_routes import auth_router

__all__ = ["router", "ws_router", "auth_router"]
