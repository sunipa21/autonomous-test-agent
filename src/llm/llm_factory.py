from browser_use.llm.google.chat import ChatGoogle
from browser_use.llm.openai.chat import ChatOpenAI
from browser_use.llm.anthropic.chat import ChatAnthropic
from src.core.config import Config

def get_llm(provider=None):
    provider = provider or Config.PROVIDER

    if provider == "gemini":
        api_key = Config.get_api_key("gemini")
        if not api_key:
            raise ValueError("Google API Key not found. Please set GOOGLE_API_KEY in .env")
        print(f"DEBUG: Using Gemini API Key: {api_key[:4]}...{api_key[-4:] if len(api_key)>8 else ''}")
        return ChatGoogle(
            model=Config.GEMINI_MODEL,
            api_key=api_key,
            temperature=0
        )
    elif provider == "openai":
        api_key = Config.get_api_key("openai")
        if not api_key:
            raise ValueError("OpenAI API Key not found. Please set OPENAI_API_KEY in .env")
        return ChatOpenAI(
            model=Config.OPENAI_MODEL,
            api_key=api_key,
            temperature=0
        )
    elif provider == "anthropic":
        api_key = Config.get_api_key("anthropic")
        if not api_key:
            raise ValueError("Anthropic API Key not found. Please set ANTHROPIC_API_KEY in .env")
        return ChatAnthropic(
            model=Config.ANTHROPIC_MODEL,
            api_key=api_key,
            temperature=0
        )
    elif provider == "custom":
        # Custom provider might need specific handling or fallback to OpenAI compatible wrapper
        return ChatOpenAI(
            base_url=Config.CUSTOM_BASE_URL,
            api_key=Config.CUSTOM_API_KEY,
            model=Config.CUSTOM_MODEL_NAME,
            temperature=0
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")
