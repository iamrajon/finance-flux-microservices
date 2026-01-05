from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from consumer import init_consumers
from email_utils import send_email
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Notification Service",
    description="Microservice for handling notifications",
    version="1.0.0"
)


class EmailNotification(BaseModel):
    """Schema for email notification"""
    to_email: EmailStr
    subject: str
    body: str
    html: bool = False


# Start RabbitMQ consumers
@app.on_event("startup")
async def startup_event():
    """Initialize consumers on startup"""
    logger.info("🚀 Notification Service starting up...")
    try:
        init_consumers()
        logger.info("✅ Notification Service startup complete")
    except Exception as e:
        logger.error(f"❌ Failed to initialize consumers: {e}", exc_info=True)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"service": "Notification Service", "status": "healthy"}


@app.post("/api/notifications/send")
async def send_notification(notification: EmailNotification):
    """Send email notification"""
    success = await send_email(
        to_email=notification.to_email,
        subject=notification.subject,
        body=notification.body,
        html=notification.html
    )
    
    if success:
        return {
            "message": "Notification sent successfully",
            "to": notification.to_email
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to send notification"
        )


@app.get("/api/notifications/history")
async def get_notification_history():
    """Get notification history (placeholder)"""
    # In a real application, you would store notification history in a database
    return {
        "message": "Notification history endpoint",
        "note": "Implement database storage for notification history"
    }


@app.put("/api/notifications/preferences")
async def update_notification_preferences():
    """Update notification preferences (placeholder)"""
    # In a real application, you would store user preferences in a database
    return {
        "message": "Notification preferences endpoint",
        "note": "Implement database storage for user notification preferences"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
