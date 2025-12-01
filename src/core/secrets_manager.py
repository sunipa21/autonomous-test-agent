import os
import asyncio
import hashlib
from pathlib import Path
from browser_use.actor.page import Page

class SecretsManager:
    def __init__(self, username=None, password=None, login_url=None, cache_dir="data/auth_cache"):
        self.username = username or os.getenv("APP_USERNAME")
        self.password = password or os.getenv("APP_PASSWORD")
        self.login_url = login_url or os.getenv("APP_LOGIN_URL")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create cache file path using username hash for security
        if self.username:
            username_hash = hashlib.md5(self.username.encode()).hexdigest()[:8]
            self.cache_file = self.cache_dir / f"{username_hash}_session.json"
        else:
            self.cache_file = None

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
        
        # Save session cookies after successful login (OPTIMIZATION)
        if self.cache_file:
            try:
                import json
                # Get current cookies from page
                cookies = await page.context.cookies()
                # Save cookies to cache file
                with open(self.cache_file, 'w') as f:
                    json.dump(cookies, f)
                # Restrict file permissions (owner read/write only)
                os.chmod(self.cache_file, 0o600)
                print(f"💾 Saved session cookies to cache")
                print(f"   Future runs will skip login!")
            except Exception as e:
                print(f"⚠️ Failed to save session cache: {e}")
    
    async def try_load_cached_session(self, page: Page):
        """
        Attempts to load cached session cookies.
        Returns True if session loaded and valid, False otherwise.
        """
        if not self.cache_file or not self.cache_file.exists():
            return False
        
        try:
            import json
            print(f"🚀 OPTIMIZATION: Found cached session for {self.username}")
            
            # Load cookies from cache
            with open(self.cache_file, 'r') as f:
                cookies = json.load(f)
            
            # Add cookies to browser context
            await page.context.add_cookies(cookies)
            
            # Navigate to login URL to check if session is still valid
            await page.goto(self.login_url)
            await asyncio.sleep(2)
            
            # Check if login form is present (session expired) or not (logged in)
            login_elements = await page.get_elements_by_css_selector("input[name='user-name'], #user-name, input[type='email']")
            
            if not login_elements:
                print("   ✅ Cached session is VALID - skipping login")
                print(f"   ⚡ Saved ~5-10 seconds!")
                return True
            else:
                print("   ❌ Cached session EXPIRED")
                # Delete expired cache
                os.remove(self.cache_file)
                return False
                
        except Exception as e:
            print(f"   ⚠️ Cache load failed: {e}")
            # Delete corrupted cache
            if self.cache_file.exists():
                os.remove(self.cache_file)
            return False
    
    def clear_cache(self):
        """Manually clear cached session (for debugging/logout)"""
        if self.cache_file and self.cache_file.exists():
            os.remove(self.cache_file)
            print(f"🗑️ Cleared cached session: {self.cache_file}")
