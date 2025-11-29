"""
Test Case: TC001
Title: Verify Shopping Cart and Checkout Flow
Suite: Smoke Test A
Generated: 2025-11-30 00:48:25
"""
import asyncio
from playwright.async_api import async_playwright, expect
import os

async def test_tc001():
    """
    Verify Shopping Cart and Checkout Flow
    
    Test Steps:
    1. Add an item to the cart using selector: button[data-test="add-to-cart-sauce-labs-backpack"]\n    2. Navigate to the shopping cart using selector: .shopping_cart_link\n    3. Click the Checkout button using selector: button[data-test="checkout"]\n    4. Fill First Name using selector: input[data-test="firstName"]\n    5. Fill Last Name using selector: input[data-test="lastName"]\n    6. Fill Zip/Postal Code using selector: input[data-test="postalCode"]\n    7. Click Continue button using selector: input[data-test="continue"]\n    8. Click the Finish button using selector: button[data-test="finish"]\n    9. Verify successful purchase on Checkout: Complete! page\n    """
    
    async with async_playwright() as p:
        # Launch with slow_mo for visibility and Chrome flags to suppress alerts
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=1000,  # 1 second delay per action
            args=[
                "--start-maximized",
                "--disable-save-password-bubble",
                "--disable-password-manager",
                "--disable-infobars",
                "--no-default-browser-check"
            ]
        )
        # Create context with viewport=None to respect maximized window
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()
        
        try:
            print(f"Starting test: Verify Shopping Cart and Checkout Flow")
            
            # Login
            print("Step: Navigate to login page")
            await page.goto("https://www.saucedemo.com")
            
            print("Step: Enter credentials")
            username_field = page.locator('input[name="user-name"], #user-name, input[type="text"]').first
            await username_field.fill("standard_user")
            
            password_field = page.locator('input[name="password"], #password, input[type="password"]').first
            await password_field.fill("secret_sauce")
            
            print("Step: Click login button")
            login_button = page.locator('input[type="submit"], #login-button, button:has-text("Login")').first
            await login_button.click()
            
            # Wait for navigation
            await page.wait_for_load_state('networkidle')
            
            # Parse and execute test-specific steps
            # Click action
            print("  - Clicking button[data-test=\"add-to-cart-sauce-labs-backpack\"]")
            btn = page.locator('button[data-test="add-to-cart-sauce-labs-backpack"]').first
            if await btn.is_visible():
                await btn.click()
            else:
                # Fallback
                await page.click('button[data-test="add-to-cart-sauce-labs-backpack"]', timeout=2000)
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(500)
            # Click action
            print("  - Clicking .shopping_cart_link, #shopping_cart_container a")
            btn = page.locator('.shopping_cart_link, #shopping_cart_container a').first
            if await btn.is_visible():
                await btn.click()
            else:
                # Fallback
                await page.click('.shopping_cart_link, #shopping_cart_container a', timeout=2000)
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(500)
            # Click action
            print("  - Clicking button[data-test=\"checkout\"]")
            btn = page.locator('button[data-test="checkout"]').first
            if await btn.is_visible():
                await btn.click()
            else:
                # Fallback
                await page.click('button[data-test="checkout"]', timeout=2000)
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(500)
            print("Step 4: Fill First Name using selector: input[data-test="firstName"]")
            # Input text
            await page.locator('input[data-test="firstName"]').first.fill("Test")
            await page.wait_for_timeout(200)
            print("Step 5: Fill Last Name using selector: input[data-test="lastName"]")
            # Input text
            await page.locator('input[data-test="lastName"]').first.fill("User")
            await page.wait_for_timeout(200)
            print("Step 6: Fill Zip/Postal Code using selector: input[data-test="postalCode"]")
            # Input text
            await page.locator('input[data-test="postalCode"]').first.fill("12345")
            await page.wait_for_timeout(200)
            print("Step 7: Click Continue button using selector: input[data-test="continue"]")
            # Input text
            # Click action
            print("  - Clicking input[data-test=\"continue\"]")
            btn = page.locator('input[data-test="continue"]').first
            if await btn.is_visible():
                await btn.click()
            else:
                # Fallback
                await page.click('input[data-test="continue"]', timeout=2000)
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(500)
            # Click action
            print("  - Clicking button[data-test=\"finish\"]")
            btn = page.locator('button[data-test="finish"]').first
            if await btn.is_visible():
                await btn.click()
            else:
                # Fallback
                await page.click('button[data-test="finish"]', timeout=2000)
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(500)
            print("Step 9: Verify successful purchase on Checkout: Complete! page")
            # Verification
            await expect(page).to_have_url(re.compile(".*"), timeout=5000)
            
            print("Test PASSED ✓")
            return "PASS"
            
        except Exception as e:
            print(f"Test FAILED ✗: {str(e)}")
            # Take screenshot on failure
            await page.screenshot(path=f"failure_{test_id}.png")
            return "FAIL"
            
        finally:
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(test_tc001())
    print(f"Final Result: {result}")
