"""
Playwright Recorder Agent
Records browser interactions using Playwright codegen and converts to test cases
"""
import asyncio
import subprocess
import os
import re
import json
import uuid
from datetime import datetime
from typing import Dict, Optional, List
from src.llm.llm_factory import get_llm
from src.agents.recorder_logger import RecorderLogger

# Session storage for active recording sessions
RECORDING_SESSIONS: Dict[str, Dict] = {}

class RecorderAgent:
    """
    Agent for recording browser interactions using Playwright codegen
    """
    
    def __init__(self):
        self.sessions = RECORDING_SESSIONS
    
    async def start_recording(self, config: Dict) -> Dict:
        """
        Start a recording session using Playwright codegen
        
        Args:
            config: {
                "suite_name": str,
                "test_title": str,
                "url": str,
                "username": str (optional),
                "password": str (optional),
                "headless": bool
            }
        
        Returns:
            {"session_id": str, "status": "recording", "pid": int}
        """
        session_id = str(uuid.uuid4())
        start_url = config.get("url", "")
        headless = config.get("headless", False)
        
        # Log session start
        RecorderLogger.log_session_start(session_id, config)
        
        # Build playwright codegen command
        cmd = ["playwright", "codegen"]
        
        # Create output file for capturing code
        # Use system temp directory to avoid triggering server reload
        import tempfile
        output_dir = os.path.join(tempfile.gettempdir(), "playwright_recordings")
        output_file = f"{output_dir}/recording_{session_id}.py"
        os.makedirs(output_dir, exist_ok=True)
        
        RecorderLogger.log_file_operation("Creating output file", output_file)
        
        # Add output file flag
        cmd.extend(["-o", output_file])
        
        # Set target language
        cmd.extend(["--target", "python-async"])
        
        if not headless:
            cmd.extend(["--viewport-size", "1280,720"])
        
        # Add start URL if provided
        if start_url:
            cmd.append(start_url)
        
        RecorderLogger.log_command(cmd)
        
        # Start the codegen process
        try:
            # Launch codegen with output capture
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            RecorderLogger.log_process_info(process.pid, "started")
            
            # Store session info
            self.sessions[session_id] = {
                "session_id": session_id,
                "config": config,
                "process": process,
                "pid": process.pid,
                "status": "recording",
                "started_at": datetime.now().isoformat(),
                "output_file": output_file,
                "stdout_lines": [],
                "stderr_lines": []
            }
            
            print(f"✅ Recording session started: {session_id} (PID: {process.pid})")
            print(f"   Command: {' '.join(cmd)}")
            
            return {
                "session_id": session_id,
                "status": "recording",
                "pid": process.pid,
                "message": "Recording started. Interact with the browser, then call /api/recorder/stop"
            }
            
        except Exception as e:
            RecorderLogger.log_error("start_recording", e)
            print(f"❌ Failed to start recording: {str(e)}")
            raise Exception(f"Failed to start Playwright codegen: {str(e)}")
    
    async def stop_recording(self, session_id: str) -> Dict:
        """
        Stop a recording session and capture the generated code
        
        Args:
            session_id: The session ID from start_recording
        
        Returns:
            {
                "playwright_code": str,
                "english_steps": [str],
                "test_case": {...}
            }
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        process = session["process"]
        
        try:
            # IMMEDIATE KILL - No graceful termination, it takes 2.5+ minutes!
            # Playwright codegen doesn't need graceful shutdown, file is already written
            print(f"⚡ Immediately killing Playwright process {process.pid}")
            process.kill()  # SIGKILL - instant death
            
            # Wait max 2 seconds for process cleanup
            try:
                stdout, stderr = process.communicate(timeout=2)
                session["stdout"] = stdout
                session["stderr"] = stderr
                print(f"✅ Process {process.pid} terminated successfully")
            except subprocess.TimeoutExpired:
                print(f"⚠️  Process {process.pid} didn't die after SIGKILL (rare system issue)")
                stdout, stderr = b"", b""
                session["stdout"] = stdout
                session["stderr"] = stderr
            
            session["status"] = "stopped"
            session["stopped_at"] = datetime.now().isoformat()
            
            RecorderLogger.log_process_info(process.pid, "stopped")
            print(f"✅ Recording stopped: {session_id}")
            
            # Get the output file path
            output_file = session.get("output_file", None)
            
            # Read the generated code from the file
            # Note: Playwright codegen writes to file continuously, so it should exist
            playwright_code = ""
            if output_file and os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    playwright_code = f.read()
                RecorderLogger.log_file_operation("Read code from file", output_file)
                print(f"   Read {len(playwright_code)} bytes of code from {output_file}")
            else:
                RecorderLogger.log_warning(f"Output file not found: {output_file}")
                print(f"⚠️  Warning: Output file not found: {output_file}")
            
            # Check if we captured any code
            if not playwright_code or len(playwright_code.strip()) == 0:
                RecorderLogger.log_warning("No code captured from recording")
                print("⚠️  Warning: No code captured. Did you perform any actions in the browser?")
                playwright_code = "# No actions recorded\n# Please ensure you perform actions in the browser before stopping"
                english_steps = ["No actions were recorded - browser was closed without interactions"]
            else:
                # SKIP LLM - Use fallback directly for reliability and speed
                # The LLM call often hangs/times out, but fallback works perfectly
                print("📋 Extracting steps using fallback method (fast & reliable)")
                english_steps = self._extract_steps_from_code(playwright_code)
                RecorderLogger.log_llm_conversion(len(playwright_code), len(english_steps))
            
            # Create test case structure
            test_case = {
                "id": self._generate_test_id(session["config"]["suite_name"]),
                "title": session["config"]["test_title"],
                "steps": english_steps,
                "playwright_code": playwright_code,
                "recorded_at": session["started_at"],
                "recording_session_id": session_id
            }
            
            RecorderLogger.log_session_stop(session_id, len(playwright_code), len(english_steps))
            
            return {
                "playwright_code": playwright_code,
                "english_steps": english_steps,
                "test_case": test_case,
                "output_file": output_file
            }
            
        except subprocess.TimeoutExpired:
            # This shouldn't happen since we handle timeout above, but just in case
            process.kill()
            raise Exception("Failed to stop recording process (timeout)")
        except ValueError as e:
            # Session not found
            print(f"❌ Session error: {str(e)}")
            raise
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Error stopping recording: {str(e)}")
            print(f"   Full traceback:\n{error_details}")
            raise Exception(f"Failed to stop recording: {str(e)}")
    
    def get_recording_status(self, session_id: str) -> Dict:
        """
        Get the status of a recording session
        
        Returns:
            {"status": "recording|stopped", "duration": int, "pid": int}
        """
        if session_id not in self.sessions:
            return {"status": "not_found", "message": f"Session {session_id} not found"}
        
        session = self.sessions[session_id]
        started_at = datetime.fromisoformat(session["started_at"])
        duration = (datetime.now() - started_at).seconds
        
        # Check if process is still running
        process = session.get("process")
        if process and process.poll() is None:
            status = "recording"
        else:
            status = "stopped"
        
        return {
            "status": status,
            "session_id": session_id,
            "duration": duration,
            "pid": session.get("pid"),
            "started_at": session["started_at"]
        }
    
    def _parse_codegen_output(self, raw_output: str) -> str:
        """
        Parse and clean the output from Playwright codegen
        
        Args:
            raw_output: Raw stdout from codegen
        
        Returns:
            Clean Playwright Python code
        """
        if not raw_output:
            return ""
        
        # Playwright codegen outputs Python code directly to stdout
        # Clean up any extra whitespace or prompts
        lines = raw_output.split('\n')
        
        # Find the start of actual code (usually starts with import or async def)
        code_lines = []
        in_code = False
        
        for line in lines:
            if line.strip().startswith('import') or line.strip().startswith('from') or line.strip().startswith('async def'):
                in_code = True
            
            if in_code:
                code_lines.append(line)
        
        return '\n'.join(code_lines)
    
    async def _convert_code_to_english_steps(self, playwright_code: str) -> List[str]:
        """
        Convert Playwright code to human-readable English steps using LLM
        
        Args:
            playwright_code: The generated Playwright code
        
        Returns:
            List of English step descriptions
        """
        try:
            # Get LLM instance
            llm = get_llm()
            
            # Create prompt for conversion
            prompt = f"""You are a QA test documentation expert. Convert the following Playwright test code into clear, human-readable test steps.

Requirements:
- Each step should start with an action verb (Navigate, Click, Enter, Verify, etc.)
- Reference business intent, not technical selectors
- Be concise but descriptive
- Make it readable by non-technical users
- Generate ONE step for EACH line of action code

Playwright Code:
```python
{playwright_code}
```

Return ONLY a JSON array of step descriptions, like:
["Navigate to the application", "Enter username in login field", "Click submit button"]

Do NOT include explanations or any text outside the JSON array.
"""
            
            RecorderLogger.log_llm_conversion(len(playwright_code), 0)
            print(f"📤 Sending {len(playwright_code)} bytes to LLM for conversion")
            
            # Call LLM
            response = await llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            print(f"📥 LLM Response ({len(content)} chars): {content[:300]}...")
            
            # Try multiple extraction methods
            steps = None
            
            # Method 1: Direct JSON parse
            try:
                steps = json.loads(content.strip())
                if isinstance(steps, list):
                    print(f"✅ Method 1: Direct parse successful, {len(steps)} steps")
                else:
                    steps = None
            except:
                pass
            
            # Method 2: Extract from markdown code block
            if not steps and "```json" in content:
                try:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                    steps = json.loads(json_str)
                    print(f"✅ Method 2: Markdown extraction successful, {len(steps)} steps")
                except:
                    pass
            
            # Method 3: Regex extraction
            if not steps:
                try:
                    json_match = re.search(r'\[.*?\]', content, re.DOTALL)
                    if json_match:
                        steps = json.loads(json_match.group(0))
                        print(f"✅ Method 3: Regex extraction successful, {len(steps)} steps")
                except:
                    pass
            
            if steps and len(steps) > 0:
                RecorderLogger.log_llm_conversion(len(playwright_code), len(steps))
                return steps
            else:
                print("⚠️ All extraction methods failed, using fallback")
                return self._extract_steps_from_code(playwright_code)
                
        except Exception as e:
            import traceback
            print(f"❌ LLM conversion error: {str(e)}")
            print(f"   Traceback: {traceback.format_exc()}")
            RecorderLogger.log_error("_convert_code_to_english_steps", e)
            return self._extract_steps_from_code(playwright_code)
    
    def _extract_steps_from_code(self, code: str) -> List[str]:
        """
        Fallback: Extract basic steps from Playwright code without LLM
        Handles both old (page.click) and new (locator().click) Playwright syntax
        
        Args:
            code: Playwright Python code
        
        Returns:
            List of basic step descriptions
        """
        print("📋 Extracting steps from code using fallback method")
        steps = []
        lines = code.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines, imports, function defs, context managers
            if not line or line.startswith('import') or line.startswith('from'):
                continue
            if line.startswith('async def') or line.startswith('async with'):
                continue
            if 'await context.close()' in line or 'await browser.close()' in line:
                continue
            if line.startswith('#') or line.startswith('"""'):
                continue
            
            # Extract actions
            step = None
            
            # Navigation
            if '.goto(' in line:
                url_match = re.search(r'goto\(["\']([^"\' ]+)["\']\)', line)
                if url_match:
                    step = f'Navigate to "{url_match.group(1)}"'
            
            # Fill/Type (new syntax: locator().fill())
            elif '.fill(' in line:
                # Extract value being filled
                value_match = re.search(r'fill\(["\']([^"\' ]+)["\']\)', line)
                if value_match:
                    value = value_match.group(1)
                    # Try to identify the field from data-test attribute
                    if 'data-test=' in line:
                        field_match = re.search(r'data-test=["\\]*([^"\\]+)["\\]*', line)
                        if field_match:
                            field = field_match.group(1)
                            step = f'Enter "{value}" in {field} field'
                        else:
                            step = f'Enter "{value}" in field'
                    else:
                        step = f'Enter "{value}" in field'
            
            # Click (new syntax: locator().click() or get_by_role().click())
            elif '.click()' in line:
                # get_by_role with name
                if 'get_by_role' in line:
                    role_match = re.search(r'get_by_role\(["\']([^"\' ]+)["\'], name=["\']([^"\' ]+)["\']\)', line)
                    if role_match:
                        role = role_match.group(1)
                        name = role_match.group(2)
                        step = f'Click "{name}" {role}'
                
                # locator with data-test
                elif 'data-test=' in line:
                    field_match = re.search(r'data-test=["\\]*([^"\\]+)["\\]*', line)
                    if field_match:
                        field = field_match.group(1)
                        step = f'Click {field}'
                    else:
                        step = 'Click element'
                
                else:
                    step = 'Click element'
            
            # Old syntax patterns (for compatibility)
            elif 'page.click(' in line:
                step = 'Click element'
            elif 'page.fill(' in line:
                step = 'Fill field'
            elif 'page.type(' in line:
                step = 'Type in field'
            elif 'expect(' in line:
                step = 'Verify element'
            elif 'page.press(' in line:
                step = 'Press key'
            elif 'page.close()' in line:
                step = 'Close page'
            
            if step:
                steps.append(step)
                print(f"   • {step}")
        
        if not steps:
            print("   ⚠️ No steps extracted, using default")
            steps = ["Manual test steps - code recorded successfully"]
        else:
            print(f"   ✅ Extracted {len(steps)} steps from code")
        
        return steps
    
    def _generate_test_id(self, suite_name: str) -> str:
        """Generate a unique test case ID"""
        # Count existing tests in this suite
        count = sum(1 for s in self.sessions.values() 
                   if s.get("config", {}).get("suite_name") == suite_name)
        return f"TC{str(count + 1).zfill(3)}"


# Global recorder instance
recorder = RecorderAgent()
