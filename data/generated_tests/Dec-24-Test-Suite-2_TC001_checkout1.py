"""
Test Case: TC001
Title: Checkout-1
Suite: Dec-24-Test-Suite-2
Recorded: 2025-12-24T14:51:23.969222
Recording Session: 944a3dd7-4cac-4b30-a148-96060d3f2235

English Steps:
  1. Navigate to "https://www.saucedemo.com/"
  2. Click username
  3. Enter "standard_user" in username field
  4. Click password
  5. Enter "secret_sauce" in password field
  6. Click login-button
  7. Click add-to-cart-sauce-labs-backpack
  8. Click shopping-cart-link
  9. Click checkout
  10. Click firstName
  11. Enter "Test" in firstName field
  12. Click lastName
  13. Enter "User" in lastName field
  14. Click postalCode
  15. Enter "12345" in postalCode field
  16. Click continue
  17. Click finish
  18. Verify element
  19. Verify element
  20. Click logout-sidebar-link

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
    await page.locator("[data-test=\"add-to-cart-sauce-labs-backpack\"]").click()
    await page.locator("[data-test=\"shopping-cart-link\"]").click()
    await page.locator("[data-test=\"checkout\"]").click()
    await page.locator("[data-test=\"firstName\"]").click()
    await page.locator("[data-test=\"firstName\"]").fill("Test")
    await page.locator("[data-test=\"lastName\"]").click()
    await page.locator("[data-test=\"lastName\"]").fill("User")
    await page.locator("[data-test=\"postalCode\"]").click()
    await page.locator("[data-test=\"postalCode\"]").fill("12345")
    await page.locator("[data-test=\"continue\"]").click()
    await page.locator("[data-test=\"finish\"]").click()
    await expect(page.locator("[data-test=\"pony-express\"]")).to_be_visible()
    await expect(page.locator("[data-test=\"complete-header\"]")).to_be_visible()
    await page.get_by_role("button", name="Open Menu").click()
    await page.locator("[data-test=\"logout-sidebar-link\"]").click()

    # ---------------------
    await context.close()
    await browser.close()


async def main() -> None:
    async with async_playwright() as playwright:
        await run(playwright)


asyncio.run(main())
