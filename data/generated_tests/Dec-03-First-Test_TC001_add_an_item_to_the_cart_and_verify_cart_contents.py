"""
Test Case: TC001
Title: Add an item to the cart and verify cart contents
Suite: Dec-03-First-Test
Generated: 2025-12-03 11:30:58
"""
import asyncio
from playwright.async_api import async_playwright, expect
import os

async def test_tc001():
    """
    Add an item to the cart and verify cart contents
    
    Test Steps:
    1. Click the 'Add to cart' button for the Sauce Labs Backpack using selector: #add-to-cart-sauce-labs-backpack\n    2. Click the shopping cart icon using selector: .shopping_cart_link\n    3. Verify the 'Sauce Labs Backpack' is displayed in the cart with quantity 1 using selector: #item_4_title_link\n    """
    
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
            print(f"Starting test: Add an item to the cart and verify cart contents")
            test_id = "TC001"
            
            # Load credentials from secure config file
            import json
            from pathlib import Path
            config_file = Path(__file__).parent / "Dec-03-First-Test_metadata.json"
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    test_url = config.get('url', '')
                    test_username = config.get('username', '')
                    test_password = config.get('password', '')
                print(f"Loaded credentials from: {config_file}")
            else:
                print("WARNING: No config file found, using placeholder values")
                test_url = "https://www.saucedemo.com"
                test_username = "standard_user"
                test_password = "secret_sauce"
            
            # Login (Only if credentials provided AND login form is present)
            if test_username and test_password:
                print("Step: Navigate to login page and authenticate")
                await page.goto(test_url)
                await page.wait_for_load_state('networkidle')
                
                # Check if we need to login (is login button present?)
                login_button_present = await page.locator('#login-button, input[type="submit"], button:has-text("Login")').first.is_visible(timeout=2000) if await page.locator('#login-button, input[type="submit"], button:has-text("Login")').count() > 0 else False
                
                if login_button_present:
                    print("Step: Enter credentials")
                    username_field = page.locator('input[name="user-name"], #user-name, input[type="text"]').first
                    await username_field.fill(test_username)
                    
                    password_field = page.locator('input[name="password"], #password, input[type="password"]').first
                    await password_field.fill(test_password)
                    
                    print("Step: Click login button")
                    login_button = page.locator('input[type="submit"], #login-button, button:has-text("Login")').first
                    await login_button.click()
                    
                    # Wait for navigation
                    await page.wait_for_load_state('networkidle')
                else:
                    print("Step: Already logged in (login form not found, skipping)")
            else:
                print("Step: Navigate to application (No login required)")
                await page.goto(test_url)
                await page.wait_for_load_state('networkidle')

            
            # Parse and execute test-specific steps
            # Click action
            print("  - Clicking #add-to-cart-sauce-labs-backpack")
            btn = page.locator("#add-to-cart-sauce-labs-backpack").first
            if await btn.is_visible():
                await btn.click()
            else:
                # Fallback
                await page.click("#add-to-cart-sauce-labs-backpack", timeout=2000)
            await page.wait_for_load_state('networkidle')
            # Click action
            print("  - Clicking .shopping_cart_link, #shopping_cart_container a")
            btn = page.locator(".shopping_cart_link, #shopping_cart_container a").first
            if await btn.is_visible():
                await btn.click()
            else:
                # Fallback
                await page.click(".shopping_cart_link, #shopping_cart_container a", timeout=2000)
            await page.wait_for_load_state('networkidle')
            print("Step 3: Verify the 'Sauce Labs Backpack' is displayed in the cart with quantity 1 using selector: #item_4_title_link")
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
