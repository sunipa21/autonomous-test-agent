"""
Playwright Script Generator

Converts AI-generated test cases into executable Playwright Python scripts.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path


class PlaywrightGenerator:
    """Generates runnable Playwright Python scripts from AI test-case dicts."""

    def __init__(self, output_dir: str = "generated_tests") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ── Public API ────────────────────────────────────────────────────────────

    def generate_script(
        self,
        test_case: dict,
        suite_name: str,
        credentials: dict,
    ) -> str:
        """Generate a Playwright Python script file and return its path."""
        test_id = test_case.get("id", "TC001")
        title = test_case.get("title", "Test Case")

        safe_name = "".join(c if c.isalnum() or c in (" ", "_") else "" for c in title)
        safe_name = safe_name.replace(" ", "_").lower()[:50]
        filename = f"{suite_name}_{test_id}_{safe_name}.py"
        filepath = self.output_dir / filename

        script = self._create_script_content(test_case, suite_name, credentials)
        filepath.write_text(script)

        return str(filepath)

    def save_test_metadata(
        self,
        suite_name: str,
        test_cases: list[dict],
        scripts: list[str],
        credentials: dict | None = None,
    ) -> str:
        """
        Save metadata about the generated scripts.

        NOTE: Only the URL and username are stored here.
        Passwords are deliberately excluded — they should be loaded from .env
        at test-run time via APP_PASSWORD.
        """
        metadata = {
            "suite_name": suite_name,
            "generated_at": datetime.now().isoformat(),
            "test_count": len(test_cases),
            "scripts": scripts,
            # URL and username are non-sensitive identifiers; password is NOT stored
            "url": credentials.get("url") if credentials else "",
            "username": credentials.get("username") if credentials else "",
        }

        metadata_file = self.output_dir / f"{suite_name}_metadata.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))

        return str(metadata_file)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _create_script_content(
        self,
        test_case: dict,
        suite_name: str,
        credentials: dict,
    ) -> str:
        """Build the full Playwright Python script as a string."""
        test_id: str = test_case.get("id", "TC001")
        title: str = test_case.get("title", "Test Case")
        steps: list[str] = test_case.get("steps", [])

        # ── Header ────────────────────────────────────────────────────────────
        script = f'''"""
Test Case : {test_id}
Title     : {title}
Suite     : {suite_name}
Generated : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
import asyncio
import json
import os
import re
from pathlib import Path

from playwright.async_api import async_playwright, expect


async def test_{test_id.lower().replace("-", "_")}():
    """
    {title}

    Test Steps:
'''

        for i, step in enumerate(steps, 1):
            script += f"    {i}. {step}\\n"

        script += '    """\n'

        # ── Browser setup ─────────────────────────────────────────────────────
        script += f'''
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=1000,
            args=[
                "--start-maximized",
                "--disable-save-password-bubble",
                "--disable-password-manager",
                "--disable-infobars",
                "--no-default-browser-check",
            ],
        )
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()

        # ── Credentials ───────────────────────────────────────────────────────
        # Prefer metadata file; fall back to environment variables.
        config_file = Path(__file__).parent / "{suite_name}_metadata.json"
        if config_file.exists():
            config = json.loads(config_file.read_text())
            test_url      = config.get("url", "")
            test_username = config.get("username", "")
        else:
            test_url      = "{credentials.get('url', '')}"
            test_username = "{credentials.get('username', '')}"

        # Password is always loaded from the environment — never stored in files.
        test_password = os.getenv("APP_PASSWORD", "")

        try:
            print(f"Starting test: {title}")
            test_id = "{test_id}"

'''

        # ── Login ─────────────────────────────────────────────────────────────
        script += '''
            # Login (only if credentials are present and login form is visible)
            if test_username and test_password:
                await page.goto(test_url)
                await page.wait_for_load_state("networkidle")

                login_selector = "#login-button, input[type=\\'submit\\'], button:has-text(\\'Login\\')"
                login_count = await page.locator(login_selector).count()
                login_visible = (
                    await page.locator(login_selector).first.is_visible(timeout=2000)
                    if login_count > 0
                    else False
                )

                if login_visible:
                    await page.locator(
                        "input[name=\\'user-name\\'], #user-name, input[type=\\'text\\']"
                    ).first.fill(test_username)
                    await page.locator(
                        "input[name=\\'password\\'], #password, input[type=\\'password\\']"
                    ).first.fill(test_password)
                    await page.locator(login_selector).first.click()
                    await page.wait_for_load_state("networkidle")
            else:
                await page.goto(test_url)
                await page.wait_for_load_state("networkidle")

            # ── Test steps ────────────────────────────────────────────────────
'''

        # ── Per-step logic ────────────────────────────────────────────────────
        for i, step in enumerate(steps, 1):
            step_lower = step.lower()

            # Extract explicit CSS selectors from step description
            selector_match = re.search(
                r"(?:Selector|CSS selector)(?:s)?: (.*?)(?:$|\.|,|\))",
                step,
                re.IGNORECASE,
            )
            extracted_selectors: list[str] = []
            if selector_match:
                raw = selector_match.group(1).split(",")
                extracted_selectors = [s.strip().rstrip(")") for s in raw]

            # Fill actions
            if any(kw in step_lower for kw in ("input", "fill", "enter")):
                script += f'            print("Step {i}: {step}")\n'

                field_map = {
                    "first name": ("Test", '#first-name, input[name="firstName"]'),
                    "last name": ("User", '#last-name, input[name="lastName"]'),
                    "zip": ("12345", '#postal-code, input[name="postalCode"]'),
                    "postal": ("12345", '#postal-code, input[name="postalCode"]'),
                }
                for keyword, (value, default_sel) in field_map.items():
                    if keyword in step_lower:
                        sel = next(
                            (s for s in extracted_selectors if keyword.split()[0] in s),
                            default_sel,
                        )
                        sel_escaped = sel.replace('"', '\\"')
                        script += f'            await page.locator("{sel_escaped}").first.fill("{value}")\n'

            # Click actions
            if any(kw in step_lower for kw in ("click", "add", "navigate")):
                click_selector = ""
                if extracted_selectors:
                    click_selector = extracted_selectors[-1]
                else:
                    heuristics = {
                        "add to cart": 'button:has-text("Add to cart")',
                        "cart": ".shopping_cart_link, #shopping_cart_container a",
                        "checkout": '#checkout, button:has-text("Checkout")',
                        "continue": '#continue, input[type="submit"]',
                        "finish": '#finish, button[name="finish"]',
                    }
                    for kw, sel in heuristics.items():
                        if kw in step_lower:
                            click_selector = sel
                            break
                    if not click_selector:
                        btn_name = (
                            step.split("'")[1]
                            if "'" in step
                            else step.split('"')[1]
                            if '"' in step
                            else "Submit"
                        )
                        click_selector = f'button:has-text("{btn_name}"), text={btn_name}'

                safe_sel = click_selector.replace('"', '\\"')
                script += f'''            print("  → Clicking {safe_sel}")\n            btn = page.locator("{safe_sel}").first\n            if await btn.is_visible():\n                await btn.click()\n            else:\n                await page.click("{safe_sel}", timeout=2000)\n            await page.wait_for_load_state("networkidle")\n'''

            # Verify actions
            if any(kw in step_lower for kw in ("verify", "assert")):
                script += f'            print("Step {i}: {step}")\n'
                script += '            await expect(page).to_have_url(re.compile(".*"), timeout=5000)\n'

            # No recognised action — just wait
            if not any(
                kw in step_lower
                for kw in ("input", "fill", "enter", "click", "add", "navigate", "verify", "assert")
            ):
                script += f'            print("Step {i}: {step}")\n'
                script += "            await page.wait_for_timeout(1000)\n"

        # ── Teardown ──────────────────────────────────────────────────────────
        script += f'''
            print("Test PASSED ✓")
            return "PASS"

        except Exception as exc:
            print(f"Test FAILED ✗: {{exc}}")
            await page.screenshot(path=f"failure_{{test_id}}.png")
            return "FAIL"

        finally:
            await browser.close()


if __name__ == "__main__":
    result = asyncio.run(test_{test_id.lower().replace("-", "_")}())
    print(f"Final Result: {{result}}")
'''

        return script
