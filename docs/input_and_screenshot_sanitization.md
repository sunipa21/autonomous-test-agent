# Input & Screenshot Sanitization Implementation Guide

**Version**: 1.0  
**Status**: Ready for Implementation  
**Objective**: Implement active sanitization for all data (text and visual) sent to LLM providers to prevent PII and credential leakage.

---

## 1. Overview & Importance

Currently, the system relies on "Security by Exclusion" (handling login outside AI). However, once logged in, the AI sees the entire screen. If the application displays sensitive user data (PII, API keys, financial data), this is sent raw to the LLM.

**Why this is critical:**
1.  **Data Privacy**: Prevents sending user PII (emails, phone numbers) to third-party LLMs.
2.  **Compliance**: Required for SOC2, GDPR, and HIPAA compliance.
3.  **Defense in Depth**: Acts as a safety net even if a user accidentally types a password in a non-password field.

---

## 2. Technical Implementation Specifications

### A. Input Sanitization (Text Redaction)

**Goal**: Actively replace sensitive patterns in text prompts with `[REDACTED]`.

**Target File**: `src/security/audit_logger.py`

#### Logic Change
Modify `AuditLogger` to perform **Active Redaction** instead of just passive detection.

1.  **Enhance `_check_for_leaks`**:
    *   Rename to `sanitize_text(self, text: str) -> Tuple[str, bool, List[str]]`.
    *   Return: `(sanitized_text, leak_detected, findings)`.
2.  **Redaction Logic**:
    *   **Credentials**: Replace known username/password substrings with `[CREDENTIAL_REDACTED]`.
    *   **Patterns**: Regex replace emails, phone numbers, and credit cards with `[PII_REDACTED]`.
    *   **Hash Check**: If exact hash match found, replace entire string.

#### Code Blueprint
```python
def sanitize_text(self, text: str) -> Tuple[str, bool, List[str]]:
    sanitized = text
    findings = []
    
    # 1. Redact Registered Credentials
    for sensitive_val in self.credential_substrings:
        if sensitive_val in sanitized.lower():
            sanitized = re.sub(re.escape(sensitive_val), "[CREDENTIAL_REDACTED]", sanitized, flags=re.IGNORECASE)
            findings.append("Redacted registered credential")

    # 2. Redact PII Patterns (Email, Phone, SSN)
    pii_patterns = {
        r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+': '[EMAIL_REDACTED]',
        r'\b\d{3}-\d{2}-\d{4}\b': '[SSN_REDACTED]',
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b': '[CARD_REDACTED]'
    }
    
    for pattern, replacement in pii_patterns.items():
        if re.search(pattern, sanitized):
            sanitized = re.sub(pattern, replacement, sanitized)
            findings.append(f"Redacted pattern: {replacement}")
            
    return sanitized, len(findings) > 0, findings
```

---

### B. Screenshot Sanitization (Vision Masking)

**Goal**: Visually mask sensitive DOM elements *before* the browser takes a screenshot for the LLM.

**Target Files**: 
- `src/core/vision_sanitizer.py` (New File)
- `src/agents/explorer_agent.py` (Integration)

#### Strategy: "Privacy Shield" CSS Injection
Inject a global CSS stylesheet into the browser context that forces sensitive elements to be blacked out or blurred. This is robust because it works even if the page reloads or navigates.

#### 1. Create `src/core/vision_sanitizer.py`

```python
class VisionSanitizer:
    """
    Injects privacy-preserving CSS into browser pages to mask sensitive data
    from AI vision capabilities.
    """
    
    # CSS to force redaction
    PRIVACY_CSS = """
        /* Mask Input Fields */
        input[type="password"],
        input[type="email"],
        input[type="tel"],
        input[name*="card"],
        input[name*="ssn"],
        input[name*="social"],
        .sensitive-input {
            color: transparent !important;
            text-shadow: 0 0 8px rgba(0,0,0,0.5) !important;
            background-color: #e0e0e0 !important;
            border: 1px solid #ccc !important;
        }

        /* Mask Sensitive Text Elements */
        .pii, .sensitive, .secret, 
        [data-sensitive="true"],
        [data-testid*="password"],
        [data-testid*="email"] {
            filter: blur(6px) !important;
            user-select: none !important;
        }
        
        /* Optional: Redaction Overlay */
        .redacted-overlay::after {
            content: "[REDACTED]";
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: black;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            z-index: 9999;
        }
    """

    @staticmethod
    async def apply_privacy_shield(page):
        """Injects the privacy CSS into the page"""
        await page.add_style_tag(content=VisionSanitizer.PRIVACY_CSS)
        print("🛡️ Vision Privacy Shield active: Sensitive elements masked")
```

#### 2. Integration in `explorer_agent.py`

Modify `explore_and_generate_tests` to apply the shield immediately after login.

```python
# In explore_and_generate_tests, after login:

from src.core.vision_sanitizer import VisionSanitizer

# ... authentication code ...

print("✅ SECURE: Authentication complete.")

# APPLY VISION SANITIZATION
# This ensures all future screenshots taken by the Agent have sensitive fields masked
context = browser.browser_context
await context.add_init_script(f"""
    const style = document.createElement('style');
    style.textContent = `{VisionSanitizer.PRIVACY_CSS}`;
    document.head.append(style);
""")
print("🛡️ Privacy Shield injected into browser context")
```

---

## 3. Implementation Checklist (Copy-Paste Ready)

To implement this feature "in one go", follow these exact steps:

1.  **Create `src/core/vision_sanitizer.py`**:
    *   Copy the class definition above.
    *   Include standard sensitive selectors (`password`, `email`, `credit-card`, `ssn`).

2.  **Update `src/security/audit_logger.py`**:
    *   Add `sanitize_text` method.
    *   Update `log_llm_request` to call `sanitize_text` first.
    *   Use the *sanitized* text for the `audit_entry` AND return it so the caller can use it (optional, but good for logging).
    *   **Crucial**: The `log_llm_request` usually logs *after* the request is formed. To actually protect the LLM, the sanitization should happen *before* sending. 
    *   *Correction*: The `AuditLogger` is currently passive. For full protection, we should use a helper `Sanitizer` class that is called *before* `llm.generate`.

3.  **Update `src/agents/explorer_agent.py`**:
    *   Import `VisionSanitizer`.
    *   Inject the CSS using `browser.new_context(service_workers="block")` or `context.add_init_script` to ensure it persists across navigations.

---

## 4. Verification Plan

1.  **Text Test**:
    *   Run a test with description: "Login with user admin and password secret_123".
    *   Check `data/security_audit/` logs.
    *   Expect prompt to contain: "Login with user admin and password [CREDENTIAL_REDACTED]".

2.  **Vision Test**:
    *   Run exploration on a page with a password field.
    *   Check the browser window (if headful).
    *   Expect password fields to be blurred or grayed out.
    *   (Note: The AI can still interact with them via selectors, but the *visual* screenshot sent to GPT-4V will be masked).

---

**End of Guide**
