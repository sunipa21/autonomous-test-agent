from browser_use import Agent, Browser
from src.llm.llm_factory import get_llm
import json
import asyncio

async def explore_and_generate_tests(start_url: str, user_description: str, secrets_manager=None, headless: bool = False):
    """
    Launches a browser, explores the website, and generates test cases.
    
    Args:
        start_url: The application URL to explore
        user_description: User's description of what to test
        secrets_manager: Optional SecretsManager for login credentials
        headless: Whether to run browser in headless mode (default: False)
    
    Returns:
        str: JSON string containing test cases
    """
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
            "--start-maximized",
            "--disable-save-password-bubble",
            "--disable-infobars",
            "--no-default-browser-check",
            "--disable-popup-blocking",
            "--disable-password-manager",
            "--disable-features=PasswordBreachDetection,PasswordProtectionWarningTrigger,PasswordManager,OptimizationGuideModelDownloading,OptimizationHintsFetching,SafeBrowsingProtectionLevelToRequests,AutofillServerCommunication",
            "--password-store=basic",
            "--no-service-autorun",
            "--force-device-scale-factor=1",  # Normal zoom level
        ],
        headless=headless,  # Use user's preference from UI toggle
        wait_between_actions=1.0,  # 1 second delay (faster than 3s, still visible)
        highlight_elements=True,  # Yellow highlights on elements
    )
    await browser.start()
    
    # Make browser window visible and bring to front
    if headless:
        print("🌐 Browser started in HEADLESS mode (background, no window)")
    else:
        print("🌐 Browser window opened - should be visible now")
        print("⏱️  BALANCED MODE: 1-second delay between actions for speed + visibility!")

    
    # Add a small delay to ensure window is visible
    await asyncio.sleep(2)

    # ===== ZERO-TRUST SECURITY: LOGIN BEFORE AI =====
    # We handle authentication HERE, BEFORE the AI Agent runs
    # The AI NEVER sees credentials or login flow
    
    # Create a temporary page for login injection
    temp_page = await browser.new_page()
    
    if secrets_manager:
        # Try to load cached session first (optimization)
        session_loaded = await secrets_manager.try_load_cached_session(temp_page)
        
        if not session_loaded:
            # No cache - perform fresh login
            print("🔐 SECURE: No cached session. Performing fresh login (AI EXCLUDED)...")
            await secrets_manager.inject_login(temp_page)
        else:
            print("💾 SECURE: Loaded cached session. Skipping login (AI EXCLUDED)...")
    else:
        # No secrets manager - just navigate to start URL
        print("⚠️  No credentials provided. Navigating to URL without login...")
        await temp_page.goto(start_url)
        await asyncio.sleep(2)
    
    
    # Note: We don't close temp_page because browser-use Page objects don't have a close() method
    # The important part is that the browser CONTEXT is now authenticated
    # The Agent will create its own page but inherit the authenticated context
    print("✅ SECURE: Authentication complete. Browser context is ready for AI Agent.")
    
    # ===== AI AGENT TASK (NO CREDENTIALS) =====
    # The AI only sees: "You're logged in, now explore"
    # It does NOT know HOW we logged in or WHAT the credentials were
    exploration_task = f"""
IMPORTANT: You are starting on an AUTHENTICATED session. The login has ALREADY been completed for you.

GOAL: {user_description}

INSTRUCTIONS:


1. You are starting at the application's page
2. PERFORM the goal step-by-step by ACTUALLY interacting with the UI:
   - Click buttons and links
   - Fill in forms with realistic test data
   - Navigate through pages
   - Complete the entire flow described in the GOAL
3. Document EVERY action you take with the exact selector you used

CRITICAL - OUTPUT FORMAT:
You MUST return ONLY a JSON structure with NO other text before or after:

{{"test_cases": [{{"id": "TC001", "title": "Your test title", "steps": ["Step 1 description using selector: css-selector-here", "Step 2 description using selector: css-selector-here"]}}]}}

RULES:
- NO explanations before or after the JSON
- NO markdown code blocks (no ```json```)
- NO "Here is the JSON" or similar text
- ONLY the raw JSON object starting with {{
- Each step MUST include the exact CSS selector you used
- Use realistic test data for any forms (e.g., email: test@example.com, name: John Doe)
- If registration/login is needed, include those steps explicitly

EXAMPLE OUTPUT FORMAT:
{{"test_cases": [{{"id": "TC001", "title": "Complete registration and checkout", "steps": ["Click 'Register' using selector: a[href='/register']", "Fill email field using selector: #Email", "Click 'Register button' using selector: #register-button"]}}]}}
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
