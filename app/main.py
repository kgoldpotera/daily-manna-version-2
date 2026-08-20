from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.webhooks import router as webhook_router
from app.config import settings
from app.services.scheduler import start_scheduler

from contextlib import asynccontextmanager
import sys
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 API starting up...")
    print(f"🌍 Debug Mode: {settings.DEBUG}")
    start_scheduler()
    yield

# Create FastAPI app
app = FastAPI(
    title="Church Management Platform API",
    description="Multi-tenant WhatsApp-native church platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include webhook routes
app.include_router(webhook_router, prefix="/api/v1")

@app.get("/")
async def home():
    return {"message": "✅ Church Management Platform is running."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        reload_dirs=["app"]
    )