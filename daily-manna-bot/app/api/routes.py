from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from app.services.whatsapp_service import whatsapp_service
from app.services.message_handler import message_handler
from app.services.bible_service import bible_service

router = APIRouter()

@router.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "Daily Manna API is running"}

@router.api_route("/webhook", methods=["POST", "OPTIONS"])
async def whatsapp_webhook(request: Request):
    """WhatsApp webhook endpoint"""
    if request.method == "OPTIONS":
        return JSONResponse(
            content={"status": "ok"}, 
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            }
        )
    
    try:
        payload = await request.json()
        print("📥 Webhook payload received:", payload)
        
        # Extract user data from payload
        user_data = whatsapp_service.extract_user_data(payload)
        if not user_data:
            print("📭 Skipping non-user message")
            return JSONResponse(content={"status": "ignored"}, status_code=200)
        
        # Handle the message
        success = await message_handler.handle_message(user_data)
        
        if success:
            return JSONResponse(content={"status": "processed"}, status_code=200)
        else:
            return JSONResponse(content={"status": "error"}, status_code=500)
            
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@router.get("/today-reading")
async def get_today_reading():
    """Get today's Bible reading"""
    try:
        reading_data = bible_service.get_today_reading()
        return reading_data
    except Exception as e:
        print(f"❌ Error getting today's reading: {e}")
        raise HTTPException(status_code=500, detail="Failed to get today's reading")

@router.get("/reading/{day}")
async def get_reading_by_day(day: int):
    """Get Bible reading for a specific day"""
    try:
        if day < 1 or day > 365:
            raise HTTPException(status_code=400, detail="Day must be between 1 and 365")
        
        reading_data = bible_service.get_reading_for_day(day)
        return reading_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting reading for day {day}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get reading")

@router.get("/join")
async def join_redirect():
    """Redirect to WhatsApp to join Daily Manna"""
    from fastapi.responses import RedirectResponse
    # Replace with your actual WhatsApp number
    whatsapp_number = "254721420119"  # Update this with your number
    return RedirectResponse(f"https://wa.me/{whatsapp_number}?text=START")