from fastapi import FastAPI
from fastapi.responses import JSONResponse
from routes.whatsapp import router as whatsapp_router

app = FastAPI()

@app.get("/", response_class=JSONResponse)
async def home():
    return {"message": "✅ Daily Manna backend is running."}

# Register WhatsApp webhook router
app.include_router(whatsapp_router)
