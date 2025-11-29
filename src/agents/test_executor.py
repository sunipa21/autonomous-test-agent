from browser_use import Agent, Browser
from src.llm.llm_factory import get_llm
import asyncio

async def execute_single_test(test_case_data, secrets_manager):
    llm = get_llm()
    
    print(f"\n🚀 STARTING TEST EXECUTION: {test_case_data.get('title')}")
    print("Opening browser window...")
    
    browser = Browser(
        browser_profile=BrowserProfile(
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
                "--start-maximized",  # Open browser maximized
                "--force-device-scale-factor=1",
            ]
        ),
        headless=False,
        wait_between_actions=1.0,  # 1 second delay
        highlight_elements=True,
    )
    await browser.start()
    page = await browser.new_page()
    
    # Securely re-inject credentials for this test run
    print("Injecting login credentials...")
    if secrets_manager:
        await secrets_manager.inject_login(page)
    
    print(f"Executing test steps...")
    
    steps_str = "\n".join(test_case_data.get('steps', []))
    
    execution_task = f"""
    You are a Test Executor.
    Execute these steps exactly:
    {steps_str}
    
    If the flow completes successfully, return exactly string "PASS".
    If it fails, return exactly string "FAIL".
    """
    
    agent = Agent(
        task=execution_task,
        llm=llm,
        browser=browser
    )
    
    history = await agent.run()
    result = history.final_result()
    
    print(f"Test execution completed with result: {result}")
    print("Keeping browser open for 3 seconds so you can see the final state...")
    
    # Give user time to see the final state
    await asyncio.sleep(3)
    
    await browser.stop()
    return result
