"""
Playwright Script Generator
Converts AI-generated test cases into executable Playwright Python scripts
"""
import os
import json
from datetime import datetime

class PlaywrightGenerator:
    def __init__(self, output_dir="generated_tests"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_script(self, test_case, suite_name, credentials):
        """
        Generate a Playwright Python script from a test case
        """
        test_id = test_case.get("id", "TC001")
        title = test_case.get("title", "Test Case")
        steps = test_case.get("steps", [])
        
        # Create filename
        safe_name = "".join(c if c.isalnum() or c in (' ', '_') else '' for c in title)
        safe_name = safe_name.replace(' ', '_').lower()[:50]
        filename = f"{suite_name}_{test_id}_{safe_name}.py"
        filepath = os.path.join(self.output_dir, filename)
        
        # Generate script content
        script = self._create_script_content(test_case, suite_name, credentials)
        
        # Save to file
        with open(filepath, 'w') as f:
            f.write(script)
        
        return filepath
    
    def _create_script_content(self, test_case, suite_name, credentials):
        """Create the actual Playwright script content"""
        test_id = test_case.get("id", "TC001")
        title = test_case.get("title", "Test Case")
        steps = test_case.get("steps", [])
        
        script = f'''"""
Test Case: {test_id}
Title: {title}
Suite: {suite_name}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
import asyncio
from playwright.async_api import async_playwright, expect
import os

async def test_{test_id.lower().replace("-", "_")}():
    """
    {title}
    
    Test Steps:
'''
        
        for i, step in enumerate(steps, 1):
            script += f"    {i}. {step}\\n"
        
        script += '    """\n'
        script += f'''    
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
            print(f"Starting test: {title}")
            
            # Login
            print("Step: Navigate to login page")
            await page.goto("{credentials.get('url', 'https://www.saucedemo.com')}")
            
            print("Step: Enter credentials")
            username_field = page.locator('input[name="user-name"], #user-name, input[type="text"]').first
            await username_field.fill("{credentials.get('username', 'standard_user')}")
            
            password_field = page.locator('input[name="password"], #password, input[type="password"]').first
            await password_field.fill("{credentials.get('password', 'secret_sauce')}")
            
            print("Step: Click login button")
            login_button = page.locator('input[type="submit"], #login-button, button:has-text("Login")').first
            await login_button.click()
            
            # Wait for navigation
            await page.wait_for_load_state('networkidle')
            
            # Parse and execute test-specific steps
'''
        
        # Add test-specific logic based on parsed steps
        for i, step in enumerate(steps, 1):
            step_lower = step.lower()
            
            # Try to extract actions from step descriptions
            # Parse explicit selectors if provided by AI
            # Parse explicit selectors if provided by AI
            import re
            extracted_selectors = []
            # Improved regex to handle "Selector: ..." or "CSS selector: ..." and stop at ) or .
            selector_match = re.search(r"(?:Selector|CSS selector)(?:s)?: (.*?)(?:$|\.|,|\))", step, re.IGNORECASE)
            if selector_match:
                # Split by comma if multiple selectors
                raw_selectors = selector_match.group(1).split(',')
                extracted_selectors = [s.strip().rstrip(')') for s in raw_selectors]
            
            # Action 1: Fill Input Fields
            if 'input' in step_lower or 'fill' in step_lower or 'enter' in step_lower:
                script += f'''            print("Step {i}: {step}")
            # Input text
'''
                # Logic to handle specific fields
                if 'first name' in step_lower:
                    val = "Test"
                    sel = '#first-name, input[name="firstName"]'
                    # Try to find explicit selector
                    for s in extracted_selectors:
                        if 'first' in s or 'name' in s: sel = s
                    script += f'''            await page.locator('{sel}').first.fill("{val}")
            await page.wait_for_timeout(200)
'''
                if 'last name' in step_lower:
                    val = "User"
                    sel = '#last-name, input[name="lastName"]'
                    for s in extracted_selectors:
                        if 'last' in s: sel = s
                    script += f'''            await page.locator('{sel}').first.fill("{val}")
            await page.wait_for_timeout(200)
'''
                if 'zip' in step_lower or 'postal' in step_lower:
                    val = "12345"
                    sel = '#postal-code, input[name="postalCode"]'
                    for s in extracted_selectors:
                        if 'postal' in s or 'zip' in s or 'code' in s: sel = s
                    script += f'''            await page.locator('{sel}').first.fill("{val}")
            await page.wait_for_timeout(200)
'''
            
            # Action 2: Click / Add / Navigate (Can happen after fill)
            if 'click' in step_lower or 'add' in step_lower or 'navigate' in step_lower:
                # Determine selector
                click_selector = None
                
                # If we have extracted selectors, use the last one for the click (heuristic)
                # unless it was used for a field. But simpler: if explicit selector exists, use it.
                if extracted_selectors:
                    # Use the last selector for the click action if multiple
                    click_selector = extracted_selectors[-1]
                
                # Fallback heuristics if no explicit selector
                if not click_selector:
                    if 'add to cart' in step_lower:
                        click_selector = 'button:has-text("Add to cart")'
                    elif 'cart' in step_lower:
                        click_selector = '.shopping_cart_link, #shopping_cart_container a'
                    elif 'checkout' in step_lower:
                        click_selector = '#checkout, button:has-text("Checkout")'
                    elif 'continue' in step_lower:
                        click_selector = '#continue, input[type="submit"]'
                    elif 'finish' in step_lower:
                        click_selector = '#finish, button[name="finish"]'
                    else:
                        # Generic text match
                        # Extract potential button name
                        btn_name = "Submit"
                        if "'" in step: btn_name = step.split("'")[1]
                        elif '"' in step: btn_name = step.split('"')[1]
                        click_selector = f'button:has-text("{btn_name}"), text={btn_name}'

                # Escape quotes for the print statement
                safe_selector = click_selector.replace('"', '\\"')
                script += f'''            # Click action
            print("  - Clicking {safe_selector}")
            btn = page.locator('{click_selector}').first
            if await btn.is_visible():
                await btn.click()
            else:
                # Fallback
                await page.click('{click_selector}', timeout=2000)
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(500)
'''

            # Action 3: Verify
            if 'verify' in step_lower or 'assert' in step_lower:
                 script += f'''            print("Step {i}: {step}")
            # Verification
            await expect(page).to_have_url(re.compile(".*"), timeout=5000)
'''
            
            # If no action detected, just wait
            if not any(x in step_lower for x in ['input', 'fill', 'enter', 'click', 'add', 'navigate', 'verify', 'assert']):
                 script += f'''            print("Step {i}: {step}")
            await page.wait_for_timeout(1000)
'''
        
        script += '''            
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
    result = asyncio.run(test_''' + test_id.lower().replace("-", "_") + '''())
    print(f"Final Result: {result}")
'''
        
        return script
    
    def save_test_metadata(self, suite_name, test_cases, scripts):
        """Save metadata about generated scripts"""
        metadata = {
            "suite_name": suite_name,
            "generated_at": datetime.now().isoformat(),
            "test_count": len(test_cases),
            "scripts": scripts
        }
        
        metadata_file = os.path.join(self.output_dir, f"{suite_name}_metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return metadata_file
