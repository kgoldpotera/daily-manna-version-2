import itertools
import copy
from openai import AsyncOpenAI
from app.config import settings

class RoundRobinBalancer:
    def __init__(self):
        # Parse comma-separated config strings
        keys = [k.strip() for k in settings.GROQ_API_KEYS.split(",") if k.strip()]
        models = [m.strip() for m in settings.GROQ_MODELS.split(",") if m.strip()]
        
        if not keys:
            raise ValueError("No Groq API keys found in configuration.")
        if not models:
            # Fallback to defaults if empty
            models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"]
            
        # Create a pool of all (api_key, model) combinations
        self.pool = []
        for key in keys:
            for model in models:
                self.pool.append({
                    "api_key": key,
                    "model": model,
                    "client": AsyncOpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
                })
        
        # itertools.cycle creates an infinite round-robin iterator
        self._iterator = itertools.cycle(self.pool)
        self.pool_size = len(self.pool)

    def get_next(self):
        """Returns the next {api_key, model, client} dict in the round-robin sequence."""
        return next(self._iterator)

# Singleton instance of the load balancer
balancer = RoundRobinBalancer()

async def chat_completion_with_fallback(**kwargs):
    """
    Wraps the OpenAI chat completion call with a Round-Robin load balancer and automatic retries.
    It will try up to N times (where N is the total number of key/model combinations) before giving up.
    """
    # Remove 'model' from kwargs since the balancer injects it
    if "model" in kwargs:
        del kwargs["model"]
        
    last_exception = None
    
    # Try as many times as we have unique endpoints in the pool
    for attempt in range(balancer.pool_size):
        endpoint = balancer.get_next()
        client = endpoint["client"]
        model = endpoint["model"]
        
        # We must copy kwargs so we don't accidentally mutate it across loops
        call_kwargs = copy.deepcopy(kwargs)
        call_kwargs["model"] = model
        
        try:
            print(f"DEBUG: AI Request routing to model '{model}' (Attempt {attempt+1}/{balancer.pool_size})")
            response = await client.chat.completions.create(**call_kwargs)
            return response
        except Exception as e:
            last_exception = e
            print(f"WARNING: AI Request failed on model '{model}'. Error: {e}")
            print("Routing to next available endpoint in the pool...")
            
    # If we exhausted the pool, raise the final exception
    print("CRITICAL: All AI endpoints in the load balancer pool failed.")
    raise last_exception
