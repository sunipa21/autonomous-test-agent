from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import json
import os
import asyncio
import re
from typing import List, Dict
from pathlib import Path

from src.agents.explorer_agent import explore_and_generate_tests
from src.agents.test_executor import execute_single_test
from src.generators.playwright_generator import PlaywrightGenerator
from src.core.secrets_manager import SecretsManager
from src.core.logger import setup_logger, log_crash
from src.core.lifecycle_logger import LifecycleLogger, EventPhase, EventComponent

# Setup Logger
logger = setup_logger("server")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# In-memory storage for demo (Use DB for production)
TEST_SUITES = {}
# File paths
TEST_SUITES_FILE = "data/test_suites.json"

# Load existing suites from file
def load_suites():
    global TEST_SUITES
    if os.path.exists(TEST_SUITES_FILE):
        try:
            with open(TEST_SUITES_FILE, 'r') as f:
                TEST_SUITES = json.load(f)
            logger.info(f"Loaded {len(TEST_SUITES)} test suites from {TEST_SUITES_FILE}")
        except Exception as e:
            logger.error(f"Failed to load suites: {e}")
            TEST_SUITES = {}

# Save suites to file
def save_suites():
    try:
        with open(TEST_SUITES_FILE, 'w') as f:
            json.dump(TEST_SUITES, f, indent=2)
        logger.info(f"Saved {len(TEST_SUITES)} test suites to {TEST_SUITES_FILE}")
    except Exception as e:
        logger.error(f"Failed to save suites: {e}")

# Load on startup
load_suites() 

class GenerateRequest(BaseModel):
    suite_name: str
    url: str
    description: str
    username: str = ""
    password: str = ""
    headless: bool = False  # Headless mode toggle

class ExecuteRequest(BaseModel):
    suite_name: str
    test_case_id: str

@app.get("/")
def read_root(request: Request):
    response = templates.TemplateResponse("index.html", {"request": request})
    # Force browser to never cache this page
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/api/test")
async def test_response():
    """Test endpoint to verify response format"""
    return {"status": "success", "test_cases": [{"id": "TEST", "title": "Test Case", "steps": ["Step 1", "Step 2"]}]}

@app.get("/api/suites")
async def get_all_suites():
    """Get all existing test suites from storage"""
    logger.info(f"Fetching all test suites. Total suites: {len(TEST_SUITES)}")
    # Convert dictionary to list format for frontend
    suites_list = []
    for suite_name, suite_data in TEST_SUITES.items():
        suites_list.append({
            "suite_name": suite_name,
            "test_cases": suite_data.get('cases', []),
            "config": suite_data.get('config', {})
        })
    logger.info(f"Returning {len(suites_list)} suites to frontend")
    return {"status": "success", "suites": suites_list}

@app.post("/api/generate")
async def generate_tests(req: GenerateRequest):
    # ALWAYS initialize test_cases to avoid undefined errors
    test_cases = []
    
    try:
        logger.info(f"Received generation request for suite '{req.suite_name}' at URL: {req.url}")
        
        # LOG: Start new session and log user action
        session_id = LifecycleLogger.start_session()
        LifecycleLogger.log_event(
            event_type="user_action",
            phase=EventPhase.EXPLORATION,
            component=EventComponent.FRONTEND,
            action="launch_explorer",
            description=f"User initiated test generation for '{req.suite_name}'",
            metadata={"suite_name": req.suite_name, "url": req.url, "headless": req.headless}
        )
        
        # Initialize Secrets Manager with USER-PROVIDED credentials from request
        # This allows testing different applications without changing .env
        secrets = SecretsManager(
            username=req.username if req.username else os.getenv("APP_USERNAME"),
            password=req.password if req.password else os.getenv("APP_PASSWORD"),
            login_url=req.url  # USE USER-PROVIDED URL, not .env
        )
        
        # LOG: Secrets manager initialized
        LifecycleLogger.log_event(
            event_type="system_bootstrap",
            phase=EventPhase.EXPLORATION,
            component=EventComponent.SECRETS,
            action="secrets_manager_init",
            description="Secrets manager initialized from environment",
            metadata={"has_username": bool(req.username or os.getenv("APP_USERNAME"))}
        )
        
        # Run AI Agent with USER-PROVIDED URL and description
        raw_result = await explore_and_generate_tests(
            start_url=req.url,  # Pass user URL
            user_description=req.description,  # Pass user description
            secrets_manager=secrets,
            headless=req.headless  # Pass headless mode setting
        )

        
        
        if not raw_result:
            logger.error("Agent returned None for generation request.")
            test_cases = [{"id": "ERR", "title": "Agent Failed", "steps": ["Agent returned no output. Check API key and network connection."]}]
        else:
            logger.info(f"Raw agent output length: {len(raw_result)} characters")
            
            # Try multiple JSON extraction methods
            parsed_json = None
            
            # Method 1: Try direct JSON parse (if output is pure JSON)
            try:
                parsed_json = json.loads(raw_result)
                logger.info("Method 1: Direct JSON parse successful")
            except json.JSONDecodeError:
                pass
            
            # Method 2: Extract JSON from markdown code blocks
            if not parsed_json:
                json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_result, re.DOTALL)
                if json_block_match:
                    try:
                        parsed_json = json.loads(json_block_match.group(1))
                        logger.info("Method 2: Extracted JSON from markdown code block")
                    except json.JSONDecodeError:
                        pass
            
            # Method 3: Find JSON object using regex (improved)
            if not parsed_json:
                # Find the start of the JSON object
                json_start_match = re.search(r'\{[^\{]*"test_cases"', raw_result, re.DOTALL)
                if json_start_match:
                    start_index = json_start_match.start()
                    json_str = raw_result[start_index:]
                    
                    # Try to fix common JSON issues
                    json_str = json_str.replace('\n', ' ').replace('\r', '')
                    
                    try:
                        parsed_json = json.loads(json_str)
                        logger.info("Method 3: Extracted JSON via regex")
                    except json.JSONDecodeError:
                        # Attempt to repair truncated JSON
                        logger.warning("JSON appears truncated, attempting repair...")
                        try:
                            # Simple repair: close open brackets/braces
                            # Count open/close braces/brackets
                            open_braces = json_str.count('{')
                            close_braces = json_str.count('}')
                            open_brackets = json_str.count('[')
                            close_brackets = json_str.count(']')
                            
                            # Append missing closing characters
                            repaired_str = json_str
                            repaired_str += '"]' * (open_brackets - close_brackets)
                            repaired_str += '}' * (open_braces - close_braces)
                            
                            # Clean up potential trailing commas before closing
                            repaired_str = re.sub(r',\s*([\]\}])', r'\1', repaired_str)
                            
                            parsed_json = json.loads(repaired_str)
                            logger.info("Method 3 (Repair): Successfully repaired and parsed truncated JSON")
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to repair JSON: {e}")
                            logger.error(f"Original string snippet: {json_str[:200]}")
            
            # Process parsed JSON
            if parsed_json:
                test_cases = parsed_json.get("test_cases", [])
                
                # Validate that test_cases is a list
                if not isinstance(test_cases, list):
                    logger.warning(f"test_cases is not a list, got: {type(test_cases)}")
                    test_cases = []
                
                # Ensure each test case has required fields
                validated_cases = []
                for tc in test_cases:
                    if isinstance(tc, dict) and "id" in tc and "title" in tc and "steps" in tc:
                        validated_cases.append(tc)
                    else:
                        logger.warning(f"Skipping invalid test case: {tc}")
                
                test_cases = validated_cases
                
                if len(test_cases) > 0:
                    logger.info(f"Successfully generated {len(test_cases)} test cases for suite '{req.suite_name}'.")
                else:
                    logger.warning("No valid test cases found in parsed JSON")
                    test_cases = [{"id": "TC001", "title": "Manual Review Required", "steps": ["Agent completed task but returned no valid test cases. Please review the application manually."]}]
            else:
                # All parsing methods failed
                logger.error(f"Failed to parse JSON from agent output. Raw result (first 500 chars): {raw_result[:500]}")
                test_cases = [{
                    "id": "ERR",
                    "title": "JSON Parse Error",
                    "steps": [
                        "Failed to extract valid JSON from agent response.",
                        f"Error details: Could not find valid JSON structure",
                        f"Raw output snippet: {raw_result[:200]}"
                    ]
                }]

        # Save to memory
        # Save to in-memory storage and persist to file
        TEST_SUITES[req.suite_name] = {
            "config": {
                "suite_name": req.suite_name,
                "url": req.url,  # Use actual request URL
                "description": req.description,
                "username": req.username if req.username else os.getenv("APP_USERNAME"),
                "password": req.password if req.password else os.getenv("APP_PASSWORD")
            },
            "cases": test_cases
        }
        save_suites()
        
        # Generate Playwright scripts for each test case
        from src.generators.playwright_generator import PlaywrightGenerator
        generator = PlaywrightGenerator(output_dir="data/generated_tests")
        
        generated_scripts = []
        # Use actual request credentials, not .env defaults
        credentials = {
            "url": req.url,
            "username": req.username if req.username else os.getenv("APP_USERNAME"),
            "password": req.password if req.password else os.getenv("APP_PASSWORD")
        }
        
        logger.info(f"Generating Playwright scripts for {len(test_cases)} test cases...")
        for test_case in test_cases:
            try:
                script_path = generator.generate_script(test_case, req.suite_name, credentials)
                generated_scripts.append(script_path)
                logger.info(f"Generated script: {script_path}")
            except Exception as e:
                logger.error(f"Failed to generate script for {test_case.get('id')}: {e}")
        
        # Save metadata
        
        # Save metadata with credentials for runtime loading
        metadata_file = generator.save_test_metadata(
            suite_name=req.suite_name,
            test_cases=test_cases,
            scripts=generated_scripts,
            credentials=credentials  # Pass credentials for storage
        )
        logger.info(f"Saved test metadata to: {metadata_file}")

        
        # ALWAYS return success with test_cases array (never return error status)
        
        # LOG: Generation complete
        LifecycleLogger.log_event(
            event_type="test_generation",
            phase=EventPhase.GENERATION,
            component=EventComponent.SERVER,
            action="generation_complete",
            description=f"Generated {len(test_cases)} test cases successfully",
            metadata={"test_count": len(test_cases), "scripts_count": len(generated_scripts), "suite_name": req.suite_name}
        )
        
        return {"status": "success", "test_cases": test_cases, "scripts_generated": len(generated_scripts)}

    except Exception as e:
        crash_file = log_crash(e, context=f"generate_tests for suite '{req.suite_name}' at URL: {req.url}")
        logger.error(f"Crash occurred in generate_tests: {e}. Report saved to {crash_file}")
        # Return success with error test case instead of error status
        return {"status": "success", "test_cases": [{"id": "CRASH", "title": "Server Error", "steps": [f"Internal error occurred: {str(e)}", f"Crash report: {crash_file}"]}]}


@app.post("/api/execute")
async def execute_test(req: ExecuteRequest):
    import subprocess
    import glob
    
    logger.info(f"Received execution request for test case: {req.test_case_id} in suite: {req.suite_name}")
    
    suite = TEST_SUITES.get(req.suite_name)
    if not suite: 
        logger.error(f"Suite not found: {req.suite_name}")
        return {"status": "error", "message": "Suite not found"}
    
    target_case = next((tc for tc in suite['cases'] if tc['id'] == req.test_case_id), None)
    if not target_case: 
        logger.error(f"Test case not found: {req.test_case_id}")
        return {"status": "error", "message": "Test case not found"}

    # Find the generated Playwright script
    script_pattern = f"data/generated_tests/{req.suite_name}_{req.test_case_id}_*.py"
    matching_scripts = glob.glob(script_pattern)

    
    if not matching_scripts:
        logger.warning(f"No Playwright script found for {req.test_case_id}, falling back to AI execution")
        # Fallback to AI execution if script not found
        config = suite['config']
        secrets = SecretsManager(config.get('username', ''), config.get('password', ''), config.get('url', ''))
        result = await execute_single_test(target_case, secrets)
        return {"status": "success", "result": result if result else "FAIL"}
    
    # Execute the Playwright script
    script_path = matching_scripts[0]
    logger.info(f"Executing generated Playwright script: {script_path}")
    
    try:
        # Run the script and capture output
        process = subprocess.run(
            ['python', script_path],
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )
        
        output = process.stdout + process.stderr
        logger.info(f"Script execution output: {output[-500:]}")  # Log last 500 chars
        
        # Check if test passed based on output
        if "PASS" in output or process.returncode == 0:
            result = "PASS"
        else:
            result = "FAIL"
        
        logger.info(f"Test execution result: {result}")
        return {"status": "success", "result": result, "output": output[-200:]}
        
    except subprocess.TimeoutExpired:
        logger.error(f"Test execution timed out for {script_path}")
        return {"status": "success", "result": "TIMEOUT"}
    except Exception as e:
        logger.error(f"Failed to execute test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# AUDIT DASHBOARD ENDPOINTS
# ========================================

AUDIT_CONFIG_FILE = "data/audit_config.json"

def load_audit_config():
    """Load audit configuration from file"""
    if os.path.exists(AUDIT_CONFIG_FILE):
        try:
            with open(AUDIT_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"enabled": False}

def save_audit_config(config):
    """Save audit configuration to file"""
    os.makedirs("data", exist_ok=True)
    with open(AUDIT_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Also update environment variable for current session
    os.environ['ENABLE_AUDIT_LOG'] = 'true' if config.get('enabled') else 'false'

# === AUDIT DASHBOARD ROUTES ===

@app.get("/audit")
async def audit_dashboard(request: Request):
    """
    Standard audit dashboard with log viewing and compliance reports
    """
    response = templates.TemplateResponse("audit_dashboard.html", {"request": request})
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    return response

@app.get("/audit/lifecycle")
async def audit_lifecycle_dashboard(request: Request):
    """
    Enhanced lifecycle audit dashboard with end-to-end trace visualization
    Shows complete lifecycle from user action through AI exploration to test execution
    """
    return templates.TemplateResponse("audit_dashboard_enhanced.html", {"request": request})

# ==================== LIFECYCLE EVENT API ENDPOINTS ====================

@app.get("/api/audit/lifecycle/events")
async def get_lifecycle_events(session_id: str = None, limit: int = None):
    """
    Get lifecycle events for debugging and audit trail
    
    Args:
        session_id: Optional session ID to filter events
        limit: Optional limit on number of events to return
    
    Returns:
        JSON with events array and metadata
    """
    try:
        events = LifecycleLogger.get_events(session_id=session_id, limit=limit)
        return {
            "success": True,
            "events": [event.dict() for event in events],
            "total": len(events),
            "session_id": session_id or LifecycleLogger.get_current_session()
        }
    except Exception as e:
        logger.error(f"Failed to get lifecycle events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/audit/lifecycle/clear")
async def clear_lifecycle_events(session_id: str = None):
    """
    Clear lifecycle events
    
    Args:
        session_id: Optional session ID to clear specific session events
    
    Returns:
        Success status
    """
    try:
        LifecycleLogger.clear_events(session_id=session_id)
        return {
            "success": True,
            "message": f"Cleared events for session: {session_id}" if session_id else "Cleared all events"
        }
    except Exception as e:
        logger.error(f"Failed to clear lifecycle events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audit/lifecycle/sessions")
async def get_lifecycle_sessions():
    """
    Get all lifecycle session IDs
    
    Returns:
        List of session IDs with event counts
    """
    try:
        sessions = LifecycleLogger.get_sessions()
        session_data = []
        for session_id in sessions:
            count = LifecycleLogger.get_event_count(session_id)
            session_data.append({
                "session_id": session_id,
                "event_count": count
            })
        
        return {
            "success": True,
            "sessions": session_data,
            "current_session": LifecycleLogger.get_current_session()
        }
    except Exception as e:
        logger.error(f"Failed to get lifecycle sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audit/status")
async def get_audit_status():
    """Get current audit logging status"""
    config = load_audit_config()
    
    # Check if any audit logs exist
    audit_dir = Path("data/security_audit")
    log_files = list(audit_dir.glob("llm_audit_*.jsonl")) if audit_dir.exists() else []
    report_files = list(audit_dir.glob("compliance_report_*.md")) if audit_dir.exists() else []
    
    return {
        "enabled": config.get("enabled", False),
        "env_var": os.getenv('ENABLE_AUDIT_LOG',  'false'),
        "log_count": len(log_files),
        "report_count": len(report_files),
        "latest_log": str(log_files[-1]) if log_files else None,
        "latest_report": str(report_files[-1]) if report_files else None
    }

@app.post("/api/audit/toggle")
async def toggle_audit_logging(enabled: dict):
    """Toggle audit logging on/off"""
    is_enabled = enabled.get("enabled", False)
    
    config = {"enabled": is_enabled}
    save_audit_config(config)
    
    logger.info(f"Audit logging {'ENABLED' if is_enabled else 'DISABLED'} via web interface")
    
    return {
        "status": "success",
        "enabled": is_enabled,
        "message": f"Audit logging {'enabled' if is_enabled else 'disabled'}"
    }

@app.get("/api/audit/logs")
async def get_audit_logs(limit: int = 50):
    """Fetch recent audit log entries"""
    audit_dir = Path("data/security_audit")
    
    if not audit_dir.exists():
        return {
            "status": "success",
            "logs": [],
            "message": "No audit logs found. Enable audit logging and run tests to generate logs."
        }
    
    # Find most recent audit log file
    log_files = sorted(audit_dir.glob("llm_audit_*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not log_files:
        return {
            "status": "success",
            "logs": [],
            "message": "No audit log files found yet."
        }
    
    # Read the most recent log file
    logs = []
    try:
        with open(log_files[0], 'r') as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
        
        # Return most recent entries (limited)
        return {
            "status": "success",
            "logs": logs[-limit:] if len(logs) > limit else logs,
            "total": len(logs),
            "file": str(log_files[0])
        }
    except Exception as e:
        logger.error(f"Failed to read audit logs: {e}")
        return {
            "status": "error",
            "logs": [],
            "error": str(e)
        }

@app.get("/api/audit/report")
async def get_compliance_report():
    """Get the latest compliance report"""
    audit_dir = Path("data/security_audit")
    
    if not audit_dir.exists():
        return {
            "status": "error",
            "message": "No audit reports found."
        }
    
    # Find most recent report
    report_files = sorted(audit_dir.glob("compliance_report_*.md"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not report_files:
        return {
            "status": "error",
            "message": "No compliance reports generated yet."
        }
    
    # Read the report
    try:
        with open(report_files[0], 'r') as f:
            report_content = f.read()
        
        return {
            "status": "success",
            "report": report_content,
            "file": str(report_files[0])
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.delete("/api/audit/clear")
async def clear_audit_logs():
    """Clear all audit logs (for testing)"""
    audit_dir = Path("data/security_audit")
    
    if not audit_dir.exists():
        return {"status": "success", "message": "No logs to clear"}
    
    deleted_count = 0
    try:
        for file in audit_dir.glob("*"):
            file.unlink()
            deleted_count += 1
        
        return {
            "status": "success",
            "deleted": deleted_count,
            "message": f"Cleared {deleted_count} audit files"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
