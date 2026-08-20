import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    # OpenWA Configuration
    OPENWA_URL: str = os.getenv("OPENWA_URL", "http://localhost:8001")
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # Groq AI Configuration
    # Fallback lists support comma-separated values
    GROQ_API_KEYS: str = os.getenv("GROQ_API_KEYS", os.getenv("GROQ_API_KEY", ""))
    GROQ_MODELS: str = os.getenv("GROQ_MODELS", "openai/gpt-oss-120b,openai/gpt-oss-20b,qwen/qwen3.6-27b")
    
    # Application Configuration
    APP_SECRET: str = os.getenv("APP_SECRET", "default_secret_key")
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "daily_manna_secret_token_123")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    def validate(self) -> bool:
        """Validate that all required environment variables are set"""
        required_vars = [
            self.SUPABASE_URL,
            self.SUPABASE_KEY
        ]
        return all(required_vars)

settings = Settings()

# Validate configuration on startup
if not settings.validate():
    raise ValueError("❌ Missing required environment variables (SUPABASE_URL or SUPABASE_KEY). Check your .env file.")