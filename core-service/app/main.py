from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, tickets, webhooks, analytics, ws
import asyncio
from app.redis_listener import listen_for_ticket_events

# create tables on startup (fine for a portfolio project; use Alembic for real prod migrations)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Incident AI Platform - Core Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tickets.router)
app.include_router(webhooks.router)
app.include_router(analytics.router)
app.include_router(ws.router)
@app.on_event("startup")
async def start_redis_listener():
    app.state.redis_listener_task = asyncio.create_task(listen_for_ticket_events())


@app.get("/health")
def health():
    return {"status": "ok"}
