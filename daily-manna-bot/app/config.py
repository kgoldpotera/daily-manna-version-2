import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    # UltraMsg Configuration
    ULTRAMSG_INSTANCE_ID: str = os.getenv("ULTRAMSG_INSTANCE_ID", "")
    ULTRAMSG_TOKEN: str = os.getenv("ULTRAMSG_TOKEN", "")
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # Application Configuration
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    @property
    def ultramsg_api_url(self) -> str:
        return f"https://api.ultramsg.com/{self.ULTRAMSG_INSTANCE_ID}/messages/chat"
    
    def validate(self) -> bool:
        """Validate that all required environment variables are set"""
        required_vars = [
            self.ULTRAMSG_INSTANCE_ID,
            self.ULTRAMSG_TOKEN,
            self.SUPABASE_URL,
            self.SUPABASE_KEY
        ]
        return all(var for var in required_vars)

settings = Settings()

# Validate configuration on startup
if not settings.validate():
    print("⚠️ Warning: Missing required environment variables. Check your .env file.")