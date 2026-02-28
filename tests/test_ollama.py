"""
Quick test to verify Ollama + Fara-7B connection
"""
import asyncio
from src.llm.llm_factory import get_llm

async def test_ollama():
    print("🔍 Testing Ollama + Fara-7B connection...")
    print("-" * 50)
    
    try:
        # Get LLM (should use Ollama now)
        llm = get_llm()
        print(f"✓ LLM initialized: {type(llm).__name__}")
        print(f"✓ Model: {llm.model}")
        print(f"✓ Provider: {llm.provider}")
        
        # Test simple inference using browser-use message format
        print("\n🧪 Testing simple inference...")
        from browser_use.llm.openai.serializer import OpenAIMessage
        
        response = await llm.ainvoke([
            OpenAIMessage(role="user", content="Say 'Hello! I am Fara-7B running locally via Ollama.' in exactly one sentence.")
        ])
        
        print(f"✓ Response received: {response.content[:100]}...")
        print("\n✅ SUCCESS! Ollama + Fara-7B is working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_ollama())
    exit(0 if result else 1)
