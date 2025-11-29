"""
Simple test to verify browser visibility
"""
import asyncio
from browser_use import Browser

async def test_visibility():
    print("🚀 Testing browser visibility...")
    print("Creating browser with headless=False...")
    
    browser = Browser(
        args=["--start-maximized"],
        headless=False,
        wait_between_actions=1.0,
        highlight_elements=True,
    )
    
    print("Starting browser...")
    await browser.start()
    
    print("Creating new page...")
    page = await browser.new_page()
    
    print("Navigating to Google...")
    await page.goto("https://www.google.com")
    
    print("⏸️  Browser should be VISIBLE now!")
    print("Waiting 10 seconds - CHECK IF YOU SEE THE BROWSER WINDOW...")
    await asyncio.sleep(10)
    
    print("Closing browser...")
    await browser.stop()
    print("✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(test_visibility())
