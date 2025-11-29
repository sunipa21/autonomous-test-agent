import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    # Model Configurations
    GEMINI_MODEL = "gemini-flash-latest"
    OPENAI_MODEL = "gpt-4o"
    ANTHROPIC_MODEL = "claude-3-5-sonnet-20240620"
    
    # Custom Model (e.g., Local Fara-7B)
    CUSTOM_BASE_URL = os.getenv("CUSTOM_BASE_URL", "http://localhost:8000/v1")
    CUSTOM_API_KEY = os.getenv("CUSTOM_API_KEY", "sk-dummy")
    CUSTOM_MODEL_NAME = os.getenv("CUSTOM_MODEL_NAME", "microsoft/Fara-7B")

    @staticmethod
    def get_api_key(provider):
        if provider == "gemini": return os.getenv("GOOGLE_API_KEY")
        if provider == "openai": return os.getenv("OPENAI_API_KEY")
        if provider == "anthropic": return os.getenv("ANTHROPIC_API_KEY")
        return None
