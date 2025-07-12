from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.config import settings

# Create FastAPI app
app = FastAPI(
    title="Daily Manna API",
    description="WhatsApp bot for daily Bible reading",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)

@app.on_event("startup")
async def startup_event():
    """Application startup"""
    print("🚀 Daily Manna API starting up...")
    print(f"📊 Debug mode: {settings.DEBUG}")
    print("✅ Daily Manna API is ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    print("👋 Daily Manna API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )