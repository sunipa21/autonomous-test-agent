# Browser Alert Handling Guide

## Problem
After login, Chrome shows two alerts that can interfere with test execution:

1. **"Change your password" alert** (Google Password Manager)  
   ![Change Password Alert](uploaded_image_0_1764433897400.png)
   - Warning about password found in data breach
   - Has an "OK" button to dismiss

2. **"Save password?" dialog** (Chrome Password Manager)  
   ![Save Password Dialog](uploaded_image_1_1764433897400.png)
   - Chrome's native password save prompt
   - Has "Never" and "Save" buttons

## Solution Implemented

### Updated File: `secrets_manager.py`

Added `handle_post_login_alerts()` method that:
- ✅ Runs automatically after login
- ✅ Checks if alerts exist
- ✅ Only acts if alerts are visible
- ✅ Gracefully continues if alerts aren't present
- ✅ No errors if alerts don't appear

### How It Works

```python
async def handle_post_login_alerts(self, page: Page):
    # 1. Wait for alerts to potentially appear
    await asyncio.sleep(1)
    
    # 2. Try to find "OK" button (Change password alert)
    try:
        for selector in ["button:has-text('OK')", ...]:
            elements = await page.get_elements_by_css_selector(selector)
            if elements and await elements[0].is_visible():
                await elements[0].click()  # Click OK
                break
    except:
        pass  # Silently continue if not found
    
    # 3. Try to find "Never" button (Save password dialog)
    try:
        for selector in ["button:has-text('Never')", ...]:
            elements = await page.get_elements_by_css_selector(selector)
            if elements and await elements[0].is_visible():
                await elements[0].click()  # Click Never
                break
    except:
        pass  # Silently continue if not found
```

## Three Patterns for Conditional Alert Handling

### Pattern 1: Try-Except with Multiple Selectors (Used in secrets_manager.py)
```python
try:
    selectors = ["button:has-text('OK')", "[aria-label='OK']"]
    for selector in selectors:
        elements = await page.get_elements_by_css_selector(selector)
        if elements and await elements[0].is_visible():
            await elements[0].click()
            break
except Exception:
    pass  # Alert not found, continue
```

**Pros:** Robust, tries multiple selectors, continues on any error  
**Cons:** Catches all exceptions

---

### Pattern 2: wait_for_selector with Timeout (Recommended for pure Playwright)
```python
try:
    button = await page.wait_for_selector(
        "button:has-text('OK')",
        timeout=2000,  # Wait max 2 seconds
        state='visible'
    )
    if button:
        await button.click()
except TimeoutError:
    print("Alert not found within timeout")
```

**Pros:** Built-in visibility check, timeout control  
**Cons:** Adds delay if element doesn't exist

---

### Pattern 3: Locator with count() and is_visible()
```python
ok_button = page.locator("button:has-text('OK')")

if await ok_button.count() > 0:
    if await ok_button.is_visible():
        await ok_button.click()
```

**Pros:** Clean, explicit checks  
**Cons:** Requires two async calls

---

## When Alerts Appear

| Alert Type | When | Why |
|-----------|------|-----|
| **Change Password** | After login if password is weak/compromised | Google Password Manager security feature |
| **Save Password** | After successful login | Chrome's built-in password manager |

---

## How to Test

### Quick Test:
```bash
python example_alert_handling.py
```

### Full Integration Test:
1. Go to `http://127.0.0.1:8000`
2. Click "Launch Explorer Agent"
3. Watch console logs:
   - `🔐 SECURE: Checking for post-login alerts...`
   - `✓ Dismissing 'Change your password' alert...` (if present)
   - `✓ Clicking 'Never' on password save prompt...` (if present)
   - `🔐 SECURE: Post-login alert handling complete.`

---

## Additional Defense Layer

You already have Chrome flags in `explorer_agent.py` and `test_executor.py`:
```python
args=[
    "--disable-save-password-bubble",
    "--disable-password-manager",
    "--disable-features=PasswordBreachDetection,PasswordProtectionWarningTrigger",
    # ... more flags
]
```

**This provides two layers of protection:**
1. **Chrome flags** - Prevent alerts from appearing
2. **Alert handlers** - Dismiss alerts if they do appear anyway

---

## Troubleshooting

### If alerts still appear:
1. Check console logs for alert detection messages
2. Inspect the alert HTML to find correct selectors:
   ```javascript
   // In browser DevTools Console
   document.querySelector("button:has-text('OK')")
   ```
3. Add new selectors to `ok_button_selectors` or `never_button_selectors`

### If alerts are being missed:
- Increase wait time: `await asyncio.sleep(2)` instead of `1`
- Add more specific selectors based on actual HTML
- Check if alert is in an iframe

---

## Example: Adding Custom Alert Handler

```python
# In secrets_manager.py, add to handle_post_login_alerts():

# 3. Handle custom alert
try:
    custom_selectors = ["button:has-text('Dismiss')", "#custom-alert-ok"]
    for selector in custom_selectors:
        elements = await page.get_elements_by_css_selector(selector)
        if elements and await elements[0].is_visible():
            print("  ✓ Dismissing custom alert...")
            await elements[0].click()
            await asyncio.sleep(0.5)
            break
except Exception as e:
    print(f"  ℹ️  No custom alert found: {e}")
```

---

**Status:** ✅ Implemented and ready to test  
**Files Modified:** `secrets_manager.py`  
**Example Created:** `example_alert_handling.py`
