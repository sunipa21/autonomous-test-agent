from browser_use import Agent, Browser
from src.llm.llm_factory import get_llm
import json
import asyncio

async def explore_and_generate_tests(start_url, user_description, secrets_manager):
    print(f"🕵️ Starting Explorer Agent...")
    
    llm = get_llm()
    
    # Headful browser to visualize the exploration
    # IMPORTANT: Configuration passed directly to Browser for visibility
    # Headful browser to visualize the exploration
    # IMPORTANT: Configuration passed directly to Browser for visibility
    # Reverting to using BrowserProfile for args as this was confirmed working previously
    # Headful browser to visualize the exploration
    # IMPORTANT: Configuration passed directly to Browser for visibility
    browser = Browser(
        args=[
            "--disable-save-password-bubble",
            "--disable-infobars",
            "--no-default-browser-check",
            "--disable-popup-blocking",
            "--disable-password-manager",
            "--disable-features=PasswordBreachDetection,PasswordProtectionWarningTrigger,PasswordManager,OptimizationGuideModelDownloading,OptimizationHintsFetching,SafeBrowsingProtectionLevelToRequests,AutofillServerCommunication",
            "--password-store=basic",
            "--no-service-autorun",
            "--strict-origin-isolation",
            "--disable-sync",
            "--disable-signin-promo",
            "--disable-domain-reliability",
            "--disable-client-side-phishing-detection",
            "--disable-component-update",
            "--no-first-run",
            "--disable-password-generation",
            "--disable-password-manager-reauthentication",
            "--use-mock-keychain",
            "--disable-blink-features=AutofillShowTypePredictions",
            "--start-maximized",  # Maximize window for better visibility
            "--force-device-scale-factor=1",  # Normal zoom level
        ],
        headless=False,  # CRITICAL: Show the browser window
        wait_between_actions=3.0,  # 3 SECONDS between EVERY action for visibility
        highlight_elements=True,  # Yellow highlights on elements
    )
    await browser.start()
    page = await browser.new_page()
    
    # Make browser window visible and bring to front
    print("🌐 Browser window opened - should be visible now")
    print("⏱️  SLOW MOTION MODE: 3-second delay between EVERY action!")
    
    # Add a small delay to ensure window is visible
    await asyncio.sleep(2)

    # Securely inject credentials first
    if secrets_manager:
        await secrets_manager.inject_login(page)
    else:
        # Fallback if secrets manager is not provided
        await page.goto(start_url)
    
    # Task for the Agent
    exploration_task = f"""
GOAL: {user_description}

INSTRUCTIONS:
1. I have ALREADY logged you in to the inventory page
2. PERFORM the goal by actually CLICKING buttons and FILLING forms:
   - Click "Add to cart"
   - Navigate to cart
   - Click checkout
   - Fill customer info form
   - Complete the checkout
3. Document each action you performed with its selector

CRITICAL - OUTPUT FORMAT:
You MUST return ONLY this JSON structure with NO other text:

{{"test_cases": [{{"id": "TC001", "title": "Shopping cart checkout", "steps": ["Click 'Add to cart' using selector: button[data-test='add-to-cart-sauce-labs-backpack']", "Click cart icon using selector: .shopping_cart_link", "Click 'Checkout' using selector: button[data-test='checkout']"]}}]}}

RULES:
- NO explanations
- NO markdown
- NO "Here is the JSON"
- ONLY the raw JSON object starting with {{
- Each step MUST include the selector you used
"""

    agent = Agent(
        task=exploration_task,
        llm=llm,
        browser=browser
    )
    
    print("🤖 Agent is now exploring the application...")
    print("👀 WATCH THE BROWSER - You should see clicks and navigation happening slowly!")

    try:
        history = await agent.run()
        
        # Keep browser open for 10 seconds so you can see the final state
        print("⏸️  Keeping browser open for 10 seconds to see final state...")
        await asyncio.sleep(10)
        
        final_result = history.final_result()
        
        if not final_result:
            print("❌ Agent finished but returned no result (likely failed internally)")
            # Return a structured error that the server can parse
            error_json = json.dumps({
                "test_cases": [{
                    "id": "ERR",
                    "title": "Agent Execution Failed",
                    "steps": [
                        "Agent stopped without producing a result.",
                        "This is likely due to an API Rate Limit (429) or repeated errors.",
                        "Please wait a minute and try again."
                    ]
                }]
            })
            await browser.stop()
            return error_json
            
    except Exception as e:
        print(f"❌ Agent run failed: {str(e)}")
        # Return a structured error that the server can parse
        error_json = json.dumps({
            "test_cases": [{
                "id": "ERR",
                "title": "Agent Execution Failed",
                "steps": [
                    f"Error: {str(e)}",
                    "If this is a Rate Limit error (429), please wait a minute and try again."
                ]
            }]
        })
        await browser.stop()
        return error_json
    
    await browser.stop()
    return final_result
