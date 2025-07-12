from supabase import create_client, Client
from app.config import settings

class DatabaseClient:
    def __init__(self):
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            self._client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        else:
            self._client = None
            print("⚠️ Warning: Supabase credentials not configured")
    
    @property
    def client(self) -> Client:
        if self._client is None:
            raise ValueError("Database client not initialized. Check your Supabase credentials.")
        return self._client

# Global database instance
db = DatabaseClient()