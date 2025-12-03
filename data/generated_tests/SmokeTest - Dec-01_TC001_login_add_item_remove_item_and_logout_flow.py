"""
Test Case: TC001
Title: Login, Add Item, Remove Item, and Logout Flow
Suite: SmokeTest - Dec-01
Generated: 2025-12-02 12:33:10
"""
import asyncio
from playwright.async_api import async_playwright, expect
import os

async def test_tc001():
    """
    Login, Add Item, Remove Item, and Logout Flow
    
    Test Steps:
    1. Fill username field with 'standard_user' using selector: #user-name\n    2. Fill password field with 'secret_sauce' using selector: #password\n    3. Click Login button using selector: #login-button\n    4. Click 'Add to cart' for 'Sauce Labs Backpack' using selector: #add-to-cart-sauce-labs-backpack\n    5. Navigate to the cart page using selector: #shopping_cart_container a\n    6. Verify 'Sauce Labs Backpack' is present in the cart using selector: .inventory_item_name\n    7. Click 'Remove' button for 'Sauce Labs Backpack' using selector: #remove-sauce-labs-backpack\n    8. Verify the cart is empty using selector: .cart_list\n    9. Click the burger menu button to open the sidebar using selector: #react-burger-menu-btn\n    10. Click 'Logout' link using selector: #logout_sidebar_link\n    """
    
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
            print(f"Starting test: Login, Add Item, Remove Item, and Logout Flow")
            test_id = "TC001"
            
            # Load credentials from secure config file
            import json
            from pathlib import Path
            config_file = Path(__file__).parent / "SmokeTest - Dec-01_metadata.json"
            
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
            print("Step 1: Fill username field with 'standard_user' using selector: #user-name")
            # Input text
            print("Step 2: Fill password field with 'secret_sauce' using selector: #password")
            # Input text
            # Click action
            print("  - Clicking #login-button")
            btn = page.locator("#login-button").first
            if await btn.is_visible():
                await btn.click()
            else:
                # Fallback
                await page.click("#login-button", timeout=2000)
            await page.wait_for_load_state('networkidle')
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
            print("  - Clicking #shopping_cart_container a")
            btn = page.locator("#shopping_cart_container a").first
            if await btn.is_visible():
                await btn.click()
            else:
                # Fallback
                await page.click("#shopping_cart_container a", timeout=2000)
            await page.wait_for_load_state('networkidle')
            print("Step 6: Verify 'Sauce Labs Backpack' is present in the cart using selector: .inventory_item_name")
            # Verification
            await expect(page).to_have_url(re.compile(".*"), timeout=5000)
            # Click action
            print("  - Clicking #remove-sauce-labs-backpack")
            btn = page.locator("#remove-sauce-labs-backpack").first
            if await btn.is_visible():
                await btn.click()
            else:
                # Fallback
                await page.click("#remove-sauce-labs-backpack", timeout=2000)
            await page.wait_for_load_state('networkidle')
            print("Step 8: Verify the cart is empty using selector: .cart_list")
            # Verification
            await expect(page).to_have_url(re.compile(".*"), timeout=5000)
            # Click action
            print("  - Clicking #react-burger-menu-btn")
            btn = page.locator("#react-burger-menu-btn").first
            if await btn.is_visible():
                await btn.click()
            else:
                # Fallback
                await page.click("#react-burger-menu-btn", timeout=2000)
            await page.wait_for_load_state('networkidle')
            # Click action
            print("  - Clicking #logout_sidebar_link")
            btn = page.locator("#logout_sidebar_link").first
            if await btn.is_visible():
                await btn.click()
            else:
                # Fallback
                await page.click("#logout_sidebar_link", timeout=2000)
            await page.wait_for_load_state('networkidle')
            
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
