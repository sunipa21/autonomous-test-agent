import os
import asyncio
from browser_use.actor.page import Page

class SecretsManager:
    def __init__(self, username=None, password=None, login_url=None):
        self.username = username or os.getenv("APP_USERNAME")
        self.password = password or os.getenv("APP_PASSWORD")
        self.login_url = login_url or os.getenv("APP_LOGIN_URL")

    async def inject_login(self, page: Page):
        """
        Injects credentials directly into the browser DOM.
        """
        if not self.username or not self.password:
            print("⚠️ No credentials provided. Skipping login injection.")
            return

        print(f"🔐 SECURE: Navigating to {self.login_url}...")
        await page.goto(self.login_url)
        # Simple wait for load since wait_for_load_state is not available
        await asyncio.sleep(3)
        
        print("🔐 SECURE: Injecting credentials via Python (Bypassing AI)...")
        
        # Heuristic selectors for common login forms
        user_selectors = ["input[name='user-name']", "#user-name", "input[type='email']", "#username", "#email"]
        pass_selectors = ["input[name='password']", "#password", "input[type='password']"]
        btn_selectors = ["input[type='submit']", "#login-button", "button:has-text('Login')", "button[type='submit']", "[data-test='login-button']"]

        for s in user_selectors:
            elements = await page.get_elements_by_css_selector(s)
            if elements:
                await elements[0].fill(self.username)
                break
        
        for s in pass_selectors:
            elements = await page.get_elements_by_css_selector(s)
            if elements:
                await elements[0].fill(self.password)
                break

        for s in btn_selectors:
            elements = await page.get_elements_by_css_selector(s)
            if elements:
                await elements[0].click()
                break
        
        await asyncio.sleep(3)
        
        # Handle browser alerts/popups after login
        await self.handle_post_login_alerts(page)
        
        print("🔐 SECURE: Injection complete. Handing over to AI Agent.")

    async def handle_post_login_alerts(self, page: Page):
        """
        Handles common browser alerts that appear after login:
        1. "Change your password" alert (Google Password Manager)
        2. "Save password?" dialog (Chrome)
        
        Uses ESC key to dismiss alerts - much simpler than finding buttons!
        """
        print("🔐 SECURE: Checking for post-login alerts...")
        
        # Wait for alerts to potentially appear
        await asyncio.sleep(2)
        
        # 1. Handle "Change your password" alert by pressing ESC
        # This works for most dialogs/overlays
        try:
            print("  ⌨️  Pressing ESC to dismiss any alerts...")
            
            # Press ESC key multiple times to ensure dismissal
            await page.keyboard.press("Escape")
            await asyncio.sleep(0.5)
            
            # Press again in case first one didn't catch it
            await page.keyboard.press("Escape")
            await asyncio.sleep(0.5)
            
            print("  ✅ ESC pressed - alerts should be dismissed")
            
        except Exception as e:
            print(f"  ⚠️  ESC press failed: {e}")
        
        print("🔐 SECURE: Post-login alert handling complete.")
