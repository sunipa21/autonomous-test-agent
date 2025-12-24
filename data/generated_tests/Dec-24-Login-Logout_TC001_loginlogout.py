"""
Test Case: TC001
Title: Login-Logout
Suite: Dec-24-Login-Logout
Recorded: 2025-12-24T20:08:16.533648
Recording Session: 07cd42d4-286a-4e49-b915-df8e1b42d1a8

English Steps:
  1. Navigate to "https://www.saucedemo.com/"
  2. Click username
  3. Enter "standard_user" in username field
  4. Click password
  5. Enter "secret_sauce" in password field
  6. Click login-button
  7. Click logout-sidebar-link
  8. Verify element

"""

import asyncio
import re
from playwright.async_api import Playwright, async_playwright, expect


async def run(playwright: Playwright) -> None:
    browser = await playwright.chromium.launch(headless=False, slow_mo=500)  # 500ms delay between actions for visibility
    context = await browser.new_context(viewport={"width":1280,"height":720})
    page = await context.new_page()
    await page.goto("https://www.saucedemo.com/")
    await page.locator("[data-test=\"username\"]").click()
    await page.locator("[data-test=\"username\"]").fill("standard_user")
    await page.locator("[data-test=\"password\"]").click()
    await page.locator("[data-test=\"password\"]").fill("secret_sauce")
    await page.locator("[data-test=\"login-button\"]").click()
    await page.get_by_role("button", name="Open Menu").click()
    await page.locator("[data-test=\"logout-sidebar-link\"]").click()
    await expect(page.locator("[data-test=\"login-button\"]")).to_be_visible()

    # ---------------------
    await context.close()
    await browser.close()


async def main() -> None:
    async with async_playwright() as playwright:
        await run(playwright)


asyncio.run(main())
