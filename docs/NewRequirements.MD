# Secure QA Agent – Playwright Recorder & Test Management Specification

## Overview

This document defines the functional and technical requirements for enhancing the **Secure QA Agent** with:
- A **Playwright Recorder**
- **Human-readable English test steps**
- **Editable test cases**
- **Per-test and per-step execution**
- **Data-driven testing support**

The design aligns with the existing dashboard UI and focuses on **clarity, usability, and extensibility**.

---

## 1. Playwright Recorder Feature

### Objective
Allow users to **record browser interactions** and automatically convert them into:
- Executable Playwright tests
- Clear, readable English steps
- Reusable and editable test cases

---

## 2. Recorder Launch & Configuration

### UI Placement
- Add a **“Record New Test”** button on:
  - Main Dashboard
  - Test Suite View

### Pre-Recording Modal / Screen
User must provide:

| Field | Description |
|-----|------------|
| Test Suite Name | Existing or new suite |
| Test Case Title | Human-readable name |
| Application URL | Target application |
| Headed / Headless | Default: Headed |
| Credentials (Optional) | Username & password |
| Exploration Goal (Optional) | High-level intent |

---

## 3. Interactive Recording Session

### Browser Behavior
- Launch a **Playwright browser in headed mode**
- Browser must be **instrumented** to capture:
  - Clicks
  - Typing
  - Navigation
  - Form submissions
  - Page loads
  - Assertions (URL, text, element presence)

### Implementation Strategy
- **Primary approach**:
  - Use Playwright **codegen**
  - Capture output stream internally
- **Fallback approach**:
  - Inject custom DOM event listeners

---

## 4. Stop Recording & Processing

### Stop Action
- Provide a **“Stop Recording”** button in the UI

### Recorded Artifacts
- Raw Playwright code
- Event log
- DOM context (selectors, labels, roles)

---

## 5. Code Conversion Logic

### Path A – Native Codegen (Default)
- Generate standard Playwright test code (JS / Python)

### Path B – LLM-Enhanced Code (Optional)
Send to LLM:
- Raw codegen output
- DOM metadata
- Labels and accessibility roles

LLM improves:
- Selector quality
- Readability
- Comments
- Stability

**Example**

---

## 6. English Step Generation (Critical Requirement)

### Goal
Convert technical Playwright code into **clear, human-readable steps**, similar to what is shown in the current UI.

### Format (Mandatory)
Each step must:
- Start with an **action verb**
- Reference **business intent**, not selectors
- Be readable by non-technical users

### Example

| Playwright Code | English Step |
|---------------|--------------|
| `page.goto(url)` | Navigate to the application |
| `page.fill('#first-name','John')` | Enter "John" in First Name field |
| `page.click('#checkout')` | Click the Checkout button |
| `expect(page).toHaveURL(...)` | Verify order completion |

### Display
- English steps are shown:
  - Inside the **Test Results panel**
  - Expandable under each test case

---

## 7. Test Results & Execution UI

### Test Case View (Dashboard)

Each test case row shows:
- Test Case ID
- Test Case Title
- Status (Ready / Running / Passed / Failed)
- **Run Test** button
- **Edit** button

---

## 8. Step-Level Execution (New Requirement)

### Requirement
Each **individual English step** must support execution.

### UI Behavior
- Show a **Run ▶ icon** next to every step
- Clicking it:
  - Executes only that step
  - Opens browser (headed/headless based on config)
  - Highlights the executed step
  - Shows result (Passed / Failed)

### Use Cases
- Debugging flaky steps
- Selector validation
- Partial flow verification

---

## 9. Editable Test Cases

### Objective
Allow users to edit:
- English steps
- Playwright code
- Execution order

---

## 10. Edit Test Case View

### Split View Layout

#### Left Pane – English Steps
- Editable text
- Reorder via drag & drop
- Delete / disable steps
- Step-level Run option

#### Right Pane – Code Editor
- Monaco Editor
- Syntax highlighting
- Full Playwright test code

---

## 11. Synchronization Logic (LLM-Assisted)

### When Code Is Edited
- Trigger LLM:
  > “Convert this Playwright code into readable test steps”
- Update English steps automatically

### When English Steps Are Edited
- Trigger LLM:
  > “Generate Playwright code for this test step”
- Only affected code block is regenerated

> ⚠️ English and code are **loosely coupled**, not hard-mapped line by line.

---

## 12. Save & Versioning

### Save Action
Updates:
- `test_cases` table
- Fields:
  - English steps
  - Playwright code
  - Metadata

### Optional (Future)
- Version history
- Change diff view

---

## 13. Test Data Management (Data-Driven Testing)

### Objective
Separate **test logic** from **test data**.

---

## 14. Database Schema

### `test_data` Table

| Column | Description |
|------|------------|
| id | Primary key |
| variable_name | Logical placeholder |
| value | Data value |
| environment | Optional (QA, Staging, Prod) |
| encrypted | Boolean (for secrets) |

### Usage Example


---

## 15. Engineering & Quality Guidelines

### Architecture
- Modular components
- Clear API boundaries
- Stateless execution agents

### Validation
- Input validation
- Selector validation
- Step dependency checks
- Industry-standard error handling

### Non-Functional
- Secure credential handling
- Execution audit logs
- Scalable execution agents
- Clear error messaging

---

## Summary

This design ensures:
- Recorder-first UX
- Human-readable test steps
- Full editability
- Step-level execution
- Future-proof GenAI enhancements

This specification can be directly used by:
- Frontend engineers
- Backend engineers
- Automation engineers
- GenAI/LLM engineers
