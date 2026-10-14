from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.logger import logger
from app.db.init_db import init_db
from app.api.v1.api import api_router
from app.api.v1.endpoints import suppliers as suppliers_endpoint
from app.api.v1.endpoints import events as events_endpoint
from app.api.v1.endpoints import news as news_endpoint
from app.api.v1.endpoints import policy_chat as policy_chat_endpoint
from app.modules.events.pipeline_consumers import event_pipeline

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    # Initialize DB tables & seed demo data
    init_db()
    # Register Kafka Event-Driven Consumer Groups
    event_pipeline.register_all_consumers()
    yield
    logger.info("Shutting down application...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Autonomous Disruption Recovery Agent - Travel Graph & AI Recovery Platform API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Set CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS if settings.BACKEND_CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)
# Expose /api/news and /api/chat for direct /api compatibility
app.include_router(news_endpoint.router, prefix="/api")
app.include_router(policy_chat_endpoint.router, prefix="/api")
# Also expose Mock Supplier endpoints at root (/flights/search, /trains/search, /bookings/rebook, etc.)
app.include_router(suppliers_endpoint.router)

@app.websocket("/ws/events")
async def root_ws_events(websocket: WebSocket):
    await events_endpoint.kafka_events_websocket(websocket)

@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
        "websocket": "/ws/events"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
