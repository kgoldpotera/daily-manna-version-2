from supabase import create_client, Client
from app.config import settings

def get_supabase_client() -> Client:
    """Returns an authenticated Supabase client."""
    url: str = settings.SUPABASE_URL
    key: str = settings.SUPABASE_KEY
    
    if not url or not key:
        raise ValueError("Supabase URL and Key must be provided in environment variables.")
        
    return create_client(url, key)

supabase_client = get_supabase_client()
