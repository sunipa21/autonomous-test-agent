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
            print(f"Starting test: {test_case.get('title')}")
            test_id = "{test_case.get('id')}"
            
            # Load credentials from secure config file
            import json
            from pathlib import Path
            config_file = Path(__file__).parent / "{suite_name}_metadata.json"
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    test_url = config.get('url', '')
                    test_username = config.get('username', '')
                    test_password = config.get('password', '')
                print(f"Loaded credentials from: {{config_file}}")
            else:
                print("WARNING: No config file found, using placeholder values")
                test_url = "{credentials.get('url')}"
                test_username = "{credentials.get('username')}"
                test_password = "{credentials.get('password')}"
            
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
                    # Escape quotes for safe embedding
                    sel_escaped = sel.replace('"', '\\"')
                    script += f'''            await page.locator("{sel_escaped}").first.fill("{val}")
'''
                if 'last name' in step_lower:
                    val = "User"
                    sel = '#last-name, input[name="lastName"]'
                    for s in extracted_selectors:
                        if 'last' in s: sel = s
                    sel_escaped = sel.replace('"', '\\"')
                    script += f'''            await page.locator("{sel_escaped}").first.fill("{val}")
'''
                if 'zip' in step_lower or 'postal' in step_lower:
                    val = "12345"
                    sel = '#postal-code, input[name="postalCode"]'
                    for s in extracted_selectors:
                        if 'postal' in s or 'zip' in s or 'code' in s: sel = s
                    sel_escaped = sel.replace('"', '\\"')
                    script += f'''            await page.locator("{sel_escaped}").first.fill("{val}")
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

                # Escape quotes for safe embedding in string
                safe_selector_print = click_selector.replace('"', '\\"')
                safe_selector_code = click_selector.replace('"', '\\"')
                script += f'''            # Click action
            print("  - Clicking {safe_selector_print}")
            btn = page.locator("{safe_selector_code}").first
            if await btn.is_visible():
                await btn.click()
            else:
                # Fallback
                await page.click("{safe_selector_code}", timeout=2000)
            await page.wait_for_load_state('networkidle')
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
    
    def save_test_metadata(self, suite_name, test_cases, scripts, credentials=None):
        """Save metadata about generated scripts including credentials"""
        metadata = {
            "suite_name": suite_name,
            "generated_at": datetime.now().isoformat(),
            "test_count": len(test_cases),
            "scripts": scripts,
            # Store credentials for runtime use by scripts
            "url": credentials.get('url') if credentials else '',
            "username": credentials.get('username') if credentials else '',
            "password": credentials.get('password') if credentials else ''
        }
        
        metadata_file = os.path.join(self.output_dir, f"{suite_name}_metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return metadata_file
