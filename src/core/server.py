from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import json
import os
import asyncio
from typing import List, Dict

from src.agents.explorer_agent import explore_and_generate_tests
from src.agents.test_executor import execute_single_test
from src.generators.playwright_generator import PlaywrightGenerator
from src.core.secrets_manager import SecretsManager
from src.core.logger import setup_logger, log_crash

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

@app.post("/api/generate")
async def generate_tests(req: GenerateRequest):
    # ALWAYS initialize test_cases to avoid undefined errors
    test_cases = []
    
    try:
        logger.info(f"Received generation request for suite '{req.suite_name}' at URL: {req.url}")
        
        # Initialize Secrets Manager
        secrets = SecretsManager(
            username=os.getenv("APP_USERNAME"),
            password=os.getenv("APP_PASSWORD"),
            login_url=os.getenv("APP_LOGIN_URL")
        )
        
        # Run AI Agent
        raw_result = await explore_and_generate_tests(req.url, req.description, secrets)
        
        
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
        TEST_SUITES[req.suite_name] = {"config": req.dict(), "cases": test_cases}
        save_suites()  # Persist to file
        
        # Generate Playwright scripts for each test case
        from src.generators.playwright_generator import PlaywrightGenerator
        generator = PlaywrightGenerator(output_dir="data/generated_tests")
        
        generated_scripts = []
        credentials = {
            "url": os.getenv("APP_LOGIN_URL"),
            "username": os.getenv("APP_USERNAME"),
            "password": os.getenv("APP_PASSWORD")
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
        if generated_scripts:
            metadata_file = generator.save_test_metadata(req.suite_name, test_cases, generated_scripts)
            logger.info(f"Saved metadata to: {metadata_file}")
        
        # ALWAYS return success with test_cases array (never return error status)
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
    script_pattern = f"generated_tests/{req.suite_name}_{req.test_case_id}_*.py"
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
        logger.error(f"Error executing script {script_path}: {e}")
        return {"status": "success", "result": "ERROR"}

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
