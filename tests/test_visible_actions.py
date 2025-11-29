"""
Test browser with VISIBLE actions and longer delays
"""
import asyncio
from browser_use import Browser

async def test_visible_actions():
    print("=" * 60)
    print("🚀 STARTING VISIBILITY TEST WITH SLOW ACTIONS")
    print("=" * 60)
    
    browser = Browser(
        args=["--start-maximized"],
        headless=False,
        wait_between_actions=2.0,  # 2 SECONDS between actions
        highlight_elements=True,
    )
    
    await browser.start()
    page = await browser.new_page()
    
    print("\n✅ Browser opened - you should see a maximized Chrome window")
    await asyncio.sleep(3)
    
    print("\n🌐 Navigating to SauceDemo...")
    await page.goto("https://www.saucedemo.com")
    await asyncio.sleep(2)
    
    print("\n✏️  Typing username (WATCH THE SCREEN)...")
    username_field = page.locator('#user-name').first
    await username_field.fill("standard_user")
    await asyncio.sleep(2)
    
    print("\n✏️  Typing password (WATCH THE SCREEN)...")
    password_field = page.locator('#password').first
    await password_field.fill("secret_sauce")
    await asyncio.sleep(2)
    
    print("\n🖱️  Clicking login button (WATCH THE SCREEN)...")
    login_button = page.locator('#login-button').first
    await login_button.click()
    await asyncio.sleep(3)
    
    print("\n✅ Actions complete! Browser will stay open for 5 more seconds...")
    await asyncio.sleep(5)
    
    print("\n🔚 Closing browser...")
    await browser.stop()
    print("\n✅ Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_visible_actions())
