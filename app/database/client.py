from supabase import create_client, Client
from app.config import settings

class DatabaseClient:
    def __init__(self):
        self._client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    @property
    def client(self) -> Client:
        return self._client

# Global database instance
db = DatabaseClient()