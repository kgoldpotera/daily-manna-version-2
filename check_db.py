import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

try:
    resp = supabase.table("users").select("*").execute()
    print("Users in DB:", resp.data)
except Exception as e:
    print("Error:", e)
