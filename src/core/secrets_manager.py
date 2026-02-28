"""
Secrets Manager — Zero-Trust credential injection for autonomous-test-agent.

Credentials are injected locally into Playwright and NEVER sent to any LLM.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from browser_use.actor.page import Page


class SecretsManager:
    """Handles secure, local-only injection of credentials into the browser."""

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        login_url: str | None = None,
        cache_dir: str = "data/auth_cache",
    ) -> None:
        self.username: str | None = username or os.getenv("APP_USERNAME")
        self.password: str | None = password or os.getenv("APP_PASSWORD")
        self.login_url: str | None = login_url or os.getenv("APP_LOGIN_URL")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Use SHA-256 (truncated) for the session-cache filename — avoids MD5
        if self.username:
            username_hash = hashlib.sha256(self.username.encode()).hexdigest()[:12]
            self.cache_file: Path | None = self.cache_dir / f"{username_hash}_session.json"
        else:
            self.cache_file = None

    # ── Public API ────────────────────────────────────────────────────────────

    async def inject_login(self, page: Page) -> None:
        """Fill the login form and submit — entirely local, AI never involved."""
        if not self.username or not self.password:
            print("⚠️  No credentials provided. Skipping login injection.")
            return

        import asyncio

        print(f"🔐 SECURE: Navigating to {self.login_url}…")
        await page.goto(self.login_url)
        await asyncio.sleep(3)

        print("🔐 SECURE: Injecting credentials via Python (AI excluded)…")

        user_selectors = [
            "input[name='user-name']",
            "#user-name",
            "input[type='email']",
            "#username",
            "#email",
        ]
        pass_selectors = [
            "input[name='password']",
            "#password",
            "input[type='password']",
        ]
        btn_selectors = [
            "input[type='submit']",
            "#login-button",
            "button:has-text('Login')",
            "button[type='submit']",
            "[data-test='login-button']",
        ]

        for selector in user_selectors:
            elements = await page.get_elements_by_css_selector(selector)
            if elements:
                await elements[0].fill(self.username)
                break

        for selector in pass_selectors:
            elements = await page.get_elements_by_css_selector(selector)
            if elements:
                await elements[0].fill(self.password)
                break

        for selector in btn_selectors:
            elements = await page.get_elements_by_css_selector(selector)
            if elements:
                await elements[0].click()
                break

        await asyncio.sleep(3)
        await self._handle_post_login_alerts(page)
        print("🔐 SECURE: Injection complete. Browser handed to AI Agent.")

    async def try_load_cached_session(self, page: Page) -> bool:
        """
        Load cached cookies and verify the session is still valid.

        Returns True if a valid cached session was loaded, False otherwise.
        """
        import asyncio

        if not self.cache_file or not self.cache_file.exists():
            return False

        try:
            print(f"🚀 OPTIMISATION: Found cached session for {self.username}…")
            cookies = json.loads(self.cache_file.read_text())
            await page.context.add_cookies(cookies)
            await page.goto(self.login_url)
            await asyncio.sleep(2)

            # If the login form is still visible the session has expired
            login_elements = await page.get_elements_by_css_selector(
                "input[name='user-name'], #user-name, input[type='email']"
            )
            if not login_elements:
                print("   ✅ Cached session VALID — skipping login (~5-10 sec saved)")
                return True

            print("   ❌ Cached session EXPIRED — removing cache")
            self.cache_file.unlink(missing_ok=True)
            return False

        except Exception as exc:
            print(f"   ⚠️  Cache load failed: {exc}")
            self.cache_file.unlink(missing_ok=True)
            return False

    def clear_cache(self) -> None:
        """Manually remove cached session (useful for testing / explicit logout)."""
        if self.cache_file and self.cache_file.exists():
            self.cache_file.unlink()
            print(f"🗑️  Cleared cached session: {self.cache_file}")

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _handle_post_login_alerts(self, page: Page) -> None:
        """Dismiss browser password-save / change-password popups via ESC."""
        import asyncio

        print("🔐 SECURE: Checking for post-login alerts…")
        await asyncio.sleep(2)

        try:
            await page.keyboard.press("Escape")
            await asyncio.sleep(0.5)
            await page.keyboard.press("Escape")
            await asyncio.sleep(0.5)
            print("   ✅ ESC pressed — alerts dismissed")
        except Exception as exc:
            print(f"   ⚠️  ESC press failed: {exc}")

        # Cache session cookies for future runs
        await self._save_session(page)

    async def _save_session(self, page: Page) -> None:
        """Persist browser cookies to disk for session reuse."""
        if not self.cache_file:
            return

        try:
            cookies = await page.context.cookies()
            self.cache_file.write_text(json.dumps(cookies))
            os.chmod(self.cache_file, 0o600)
            print("💾 Session cookies cached — future runs will skip login")
        except Exception as exc:
            print(f"⚠️  Failed to save session cache: {exc}")
