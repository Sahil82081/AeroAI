from fastapi import APIRouter
from app.api.v1.endpoints import auth, journeys, bookings, disruptions, recovery, notifications, health, ingestion, suppliers, events, news, policy_chat, predictions, weather, flights, agent

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(ingestion.router)
api_router.include_router(journeys.router)
api_router.include_router(bookings.router)
api_router.include_router(disruptions.router)
api_router.include_router(recovery.router)
api_router.include_router(notifications.router)
api_router.include_router(suppliers.router)
api_router.include_router(events.router)
api_router.include_router(news.router)
api_router.include_router(policy_chat.router)
api_router.include_router(predictions.router)
api_router.include_router(weather.router)
api_router.include_router(flights.router)
api_router.include_router(agent.router)


