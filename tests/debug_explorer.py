import asyncio
import os
from dotenv import load_dotenv
from src.agents.explorer_agent import explore_and_generate_tests
from src.core.secrets_manager import SecretsManager

# Load environment variables
load_dotenv()

async def run_debug():
    print("🚀 Starting Debug Explorer...")
    
    # Setup secrets
    secrets = SecretsManager(
        username=os.getenv("APP_USERNAME"),
        password=os.getenv("APP_PASSWORD"),
        login_url=os.getenv("APP_LOGIN_URL")
    )
    
    # Run the explorer directly
    print("Calling explore_and_generate_tests...")
    result = await explore_and_generate_tests(
        start_url="https://www.saucedemo.com/inventory.html",
        user_description="Verify the shopping cart flow: Add an item and proceed to checkout and finish till the end.",
        secrets_manager=secrets
    )
    
    print("\n✅ Exploration Complete!")
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(run_debug())
