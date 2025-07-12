from datetime import datetime
from typing import Optional, Dict, Any
from app.database.client import db
from app.models.user import User, UserProgress, UserReflection

class UserService:
    def __init__(self):
        self.db = db.client
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by user_id"""
        try:
            result = self.db.table("users").select("*").eq("user_id", user_id).execute()
            if result.data:
                user_data = result.data[0]
                return User(
                    user_id=user_data["user_id"],
                    name=user_data["name"],
                    phone=user_data["phone"],
                    created_at=datetime.fromisoformat(user_data["created_at"]),
                    reminder_time=user_data.get("reminder_time", "07:00"),
                    reminder_active=user_data.get("reminder_active", True),
                    preferred_version=user_data.get("preferred_version", "ESV"),
                    timezone=user_data.get("timezone", "UTC")
                )
            return None
        except Exception as e:
            print(f"❌ Error getting user {user_id}: {e}")
            return None
    
    async def register_user(self, user: User) -> Dict[str, Any]:
        """Register a new user or return existing user"""
        try:
            existing_user = await self.get_user(user.user_id)
            if existing_user:
                return {"success": True, "message": f"👋 Welcome back, {existing_user.name}!", "user": existing_user}
            
            # Insert new user
            result = self.db.table("users").insert(user.to_dict()).execute()
            if result.data:
                # Initialize user progress
                progress = UserProgress(user_id=user.user_id)
                self.db.table("progress").insert(progress.to_dict()).execute()
                
                return {"success": True, "message": f"✅ Welcome to Daily Manna, {user.name}!", "user": user}
            
            return {"success": False, "message": "❌ Failed to register user"}
        except Exception as e:
            print(f"❌ Error registering user: {e}")
            return {"success": False, "message": "❌ Registration failed"}
    
    async def update_user_settings(self, user_id: str, **kwargs) -> bool:
        """Update user settings"""
        try:
            result = self.db.table("users").update(kwargs).eq("user_id", user_id).execute()
            return bool(result.data)
        except Exception as e:
            print(f"❌ Error updating user settings: {e}")
            return False
    
    async def get_user_progress(self, user_id: str) -> Optional[UserProgress]:
        """Get user's reading progress"""
        try:
            result = self.db.table("progress").select("*").eq("user_id", user_id).execute()
            if result.data:
                data = result.data[0]
                return UserProgress(
                    user_id=data["user_id"],
                    days_completed=data.get("days_completed", 0),
                    current_day=data.get("current_day", 1),
                    last_read_date=datetime.fromisoformat(data["last_read_date"]) if data.get("last_read_date") else None
                )
            return None
        except Exception as e:
            print(f"❌ Error getting user progress: {e}")
            return None
    
    async def update_reading_progress(self, user_id: str) -> bool:
        """Update user's reading progress"""
        try:
            progress = await self.get_user_progress(user_id)
            if progress:
                # Check if already read today
                today = datetime.utcnow().date()
                if progress.last_read_date and progress.last_read_date.date() == today:
                    return True  # Already read today
                
                # Update progress
                new_progress = UserProgress(
                    user_id=user_id,
                    days_completed=progress.days_completed + 1,
                    current_day=progress.current_day + 1,
                    last_read_date=datetime.utcnow()
                )
            else:
                # First time reading
                new_progress = UserProgress(
                    user_id=user_id,
                    days_completed=1,
                    current_day=1,
                    last_read_date=datetime.utcnow()
                )
            
            result = self.db.table("progress").upsert(new_progress.to_dict()).execute()
            return bool(result.data)
        except Exception as e:
            print(f"❌ Error updating reading progress: {e}")
            return False
    
    async def save_reflection(self, user_id: str, reflection_text: str, day: int) -> bool:
        """Save user's reflection"""
        try:
            reflection = UserReflection(
                user_id=user_id,
                reflection=reflection_text,
                day=day,
                created_at=datetime.utcnow()
            )
            result = self.db.table("reflections").insert(reflection.to_dict()).execute()
            return bool(result.data)
        except Exception as e:
            print(f"❌ Error saving reflection: {e}")
            return False
    
    async def get_users_for_reminder(self, time: str) -> list:
        """Get users who should receive reminders at the given time"""
        try:
            result = self.db.table("users").select("*").eq("reminder_time", time).eq("reminder_active", True).execute()
            return result.data or []
        except Exception as e:
            print(f"❌ Error getting users for reminder: {e}")
            return []

# Global service instance
user_service = UserService()