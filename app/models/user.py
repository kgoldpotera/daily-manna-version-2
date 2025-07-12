from datetime import datetime
from typing import Optional
from dataclasses import dataclass

@dataclass
class User:
    user_id: str
    name: str
    phone: str
    created_at: datetime
    reminder_time: str = "07:00"
    reminder_active: bool = True
    preferred_version: str = "ESV"
    timezone: str = "UTC"
    
    @classmethod
    def from_whatsapp_payload(cls, payload: dict) -> 'User':
        """Create User from WhatsApp webhook payload"""
        data = payload.get("data", {})
        raw_id = data.get("author") or data.get("from", "")
        user_id = raw_id if "@c.us" in raw_id else raw_id + "@c.us"
        phone = user_id.replace("@c.us", "")
        name = data.get("pushname", "Friend")
        
        return cls(
            user_id=user_id,
            name=name,
            phone=phone,
            created_at=datetime.utcnow()
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database operations"""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "phone": self.phone,
            "created_at": self.created_at.isoformat(),
            "reminder_time": self.reminder_time,
            "reminder_active": self.reminder_active,
            "preferred_version": self.preferred_version,
            "timezone": self.timezone
        }

@dataclass
class UserProgress:
    user_id: str
    days_completed: int = 0
    current_day: int = 1
    last_read_date: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "days_completed": self.days_completed,
            "current_day": self.current_day,
            "last_read_date": self.last_read_date.isoformat() if self.last_read_date else None
        }

@dataclass
class UserReflection:
    user_id: str
    reflection: str
    day: int
    created_at: datetime
    
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "reflection": self.reflection,
            "day": self.day,
            "created_at": self.created_at.isoformat()
        }