🚀 Project: Secure AI QA Agent (Text-to-Test Platform)📖 OverviewThis is a full-stack application that uses Generative AI to autonomously explore web applications and generate test cases. It features a Zero-Trust Security Architecture where user credentials are injected locally and never shared with the AI model.Stack:Frontend: HTML5, Tailwind CSS, JavaScript (Vanilla)Backend: Python FastAPIAI/Automation: LangChain, Browser-Use, PlaywrightSupported Models: Gemini 2.0, GPT-4o, Claude 3.5, Local Fara-7B

## 🎥 Demo Videos

### Exploratory Steps
Watch the AI agent autonomously exploring the web application and generating test cases:

![Exploratory Steps Demo](Exploratory%20Steps.mp4)

### Execution of Generated Test Steps
See the AI agent executing the generated test cases:

![Execution of Test Steps Demo](Execution%20of%20Generated%20Test%20Steps.mp4)

📂 File StructureThe AI should generate the following directory structure:ai-test-agent/
├── .env                   # Secrets & Config
├── requirements.txt       # Dependencies
├── config.py              # Config Loader
├── llm_factory.py         # AI Model Logic
├── secrets_manager.py     # Security Logic
├── explorer_agent.py      # Exploration Logic
├── test_executor.py       # Execution Logic
├── server.py              # FastAPI Backend
└── templates/
    └── index.html         # Web UI
💻 Source Code1. requirements.txtfastapi
uvicorn
jinja2
python-multipart
langchain-google-genai
langchain-openai
langchain-anthropic
browser-use
playwright
python-dotenv
pydantic
colorama
2. .env# --- PROVIDER CONFIG ---
# Options: 'gemini', 'openai', 'anthropic', 'custom'
LLM_PROVIDER=gemini

# --- API KEYS (Fill yours) ---
GOOGLE_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# --- APP DEFAULTS (Optional fallback) ---
APP_LOGIN_URL=[https://www.saucedemo.com](https://www.saucedemo.com)
APP_USERNAME=standard_user
APP_PASSWORD=secret_sauce
3. config.pyimport os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    # Model Configurations
    GEMINI_MODEL = "gemini-2.0-flash-exp"
    OPENAI_MODEL = "gpt-4o"
    ANTHROPIC_MODEL = "claude-3-5-sonnet-20240620"
    
    # Custom Model (e.g., Local Fara-7B)
    CUSTOM_BASE_URL = os.getenv("CUSTOM_BASE_URL", "http://localhost:8000/v1")
    CUSTOM_API_KEY = os.getenv("CUSTOM_API_KEY", "sk-dummy")
    CUSTOM_MODEL_NAME = os.getenv("CUSTOM_MODEL_NAME", "microsoft/Fara-7B")

    @staticmethod
    def get_api_key(provider):
        if provider == "gemini": return os.getenv("GOOGLE_API_KEY")
        if provider == "openai": return os.getenv("OPENAI_API_KEY")
        if provider == "anthropic": return os.getenv("ANTHROPIC_API_KEY")
        return None
4. llm_factory.pyfrom langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from config import Config

def get_llm(provider=None):
    provider = provider or Config.PROVIDER

    if provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=Config.GEMINI_MODEL,
            api_key=Config.get_api_key("gemini"),
            temperature=0
        )
    elif provider == "openai":
        return ChatOpenAI(
            model=Config.OPENAI_MODEL,
            api_key=Config.get_api_key("openai"),
            temperature=0
        )
    elif provider == "anthropic":
        return ChatAnthropic(
            model=Config.ANTHROPIC_MODEL,
            api_key=Config.get_api_key("anthropic"),
            temperature=0
        )
    elif provider == "custom":
        return ChatOpenAI(
            base_url=Config.CUSTOM_BASE_URL,
            api_key=Config.CUSTOM_API_KEY,
            model=Config.CUSTOM_MODEL_NAME,
            temperature=0
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")
5. secrets_manager.py (Security Core)import os
from playwright.async_api import Page

class SecretsManager:
    def __init__(self, username=None, password=None, login_url=None):
        self.username = username or os.getenv("APP_USERNAME")
        self.password = password or os.getenv("APP_PASSWORD")
        self.login_url = login_url or os.getenv("APP_LOGIN_URL")

    async def inject_login(self, page: Page):
        """
        Injects credentials directly into the browser DOM.
        """
        if not self.username or not self.password:
            print("⚠️ No credentials provided. Skipping login injection.")
            return

        print(f"🔐 SECURE: Navigating to {self.login_url}...")
        await page.goto(self.login_url)
        await page.wait_for_load_state("networkidle")
        
        print("🔐 SECURE: Injecting credentials via Python (Bypassing AI)...")
        
        # Heuristic selectors for common login forms
        user_selectors = ["input[name='user-name']", "#user-name", "input[type='email']", "#username", "#email"]
        pass_selectors = ["input[name='password']", "#password", "input[type='password']"]
        btn_selectors = ["input[type='submit']", "#login-button", "button:has-text('Login')", "button[type='submit']", "[data-test='login-button']"]

        for s in user_selectors:
            if await page.is_visible(s):
                await page.fill(s, self.username)
                break
        
        for s in pass_selectors:
            if await page.is_visible(s):
                await page.fill(s, self.password)
                break

        for s in btn_selectors:
            if await page.is_visible(s):
                await page.click(s)
                break
        
        await page.wait_for_load_state("networkidle")
        print("🔐 SECURE: Injection complete. Handing over to AI Agent.")
6. explorer_agent.py (The Planner)from browser_use import Agent, Browser, BrowserConfig
from llm_factory import get_llm
import json

async def explore_and_generate_tests(start_url, user_description, secrets_manager):
    print(f"🕵️ Starting Explorer Agent...")
    
    llm = get_llm()
    
    # Headful browser to visualize the exploration
    browser = Browser(config=BrowserConfig(headless=False))
    context = await browser.new_context()
    page = await context.get_current_page()

    # Securely inject credentials first
    if secrets_manager:
        await secrets_manager.inject_login(page)
    
    # Task for the Agent
    exploration_task = f"""
    You are a QA Automation Architect.
    I have already logged you into the application.
    
    Your Goal: {user_description}
    
    Instructions:
    1. Navigate through the UI to understand the flow.
    2. Do NOT log out.
    3. Identify specific element IDs and flows.
    4. Output a JSON object with a list of test cases.
       Format: {{ "test_cases": [ {{ "id": "TC001", "title": "Login Check", "steps": ["step 1", "step 2"] }} ] }}
    """

    agent = Agent(
        task=exploration_task,
        llm=llm,
        browser_context=context
    )

    history = await agent.run()
    final_result = history.final_result()
    
    await browser.close()
    return final_result
7. test_executor.py (The Executor)from browser_use import Agent, Browser, BrowserConfig
from llm_factory import get_llm

async def execute_single_test(test_case_data, secrets_manager):
    llm = get_llm()
    
    browser = Browser(config=BrowserConfig(headless=False))
    context = await browser.new_context()
    page = await context.get_current_page()
    
    # Securely re-inject credentials for this test run
    if secrets_manager:
        await secrets_manager.inject_login(page)
    
    print(f"\n🚀 Executing: {test_case_data.get('title')}")
    
    steps_str = "\n".join(test_case_data.get('steps', []))
    
    execution_task = f"""
    You are a Test Executor.
    Execute these steps exactly:
    {steps_str}
    
    If the flow completes successfully, return exactly string "PASS".
    If it fails, return exactly string "FAIL".
    """
    
    agent = Agent(
        task=execution_task,
        llm=llm,
        browser_context=context
    )
    
    history = await agent.run()
    result = history.final_result()
    
    await browser.close()
    return result
8. server.py (Backend API)from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import json
import re
import os

from explorer_agent import explore_and_generate_tests
from test_executor import execute_single_test
from secrets_manager import SecretsManager

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# In-memory storage for demo (Use DB for production)
TEST_SUITES = {} 

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
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/generate")
async def generate_tests(req: GenerateRequest):
    print(f"Received Generation Request: {req.suite_name}")
    
    secrets = SecretsManager(req.username, req.password, req.url)
    
    try:
        # Run AI Agent
        raw_result = await explore_and_generate_tests(req.url, req.description, secrets)
        
        # Parse JSON from LLM response (Handles markdown wrappers)
        json_match = re.search(r'\{.*\}', raw_result, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)
            test_cases = data.get("test_cases", [])
        else:
            # Fallback if LLM didn't output JSON
            test_cases = [{"id": "ERR", "title": "Parse Error", "steps": [raw_result]}]

        # Save to memory
        TEST_SUITES[req.suite_name] = {"config": req.dict(), "cases": test_cases}
        
        return {"status": "success", "cases": test_cases}
    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/execute")
async def execute_test(req: ExecuteRequest):
    suite = TEST_SUITES.get(req.suite_name)
    if not suite: return {"status": "error", "message": "Suite not found"}
    
    target_case = next((tc for tc in suite['cases'] if tc['id'] == req.test_case_id), None)
    if not target_case: return {"status": "error", "message": "Test case not found"}

    # Re-hydrate secrets for execution
    config = suite['config']
    secrets = SecretsManager(config['username'], config['password'], config['url'])

    result = await execute_single_test(target_case, secrets)
    return {"status": "success", "result": result}

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
9. templates/index.html (Frontend UI)<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Test Agent</title>
    <script src="[https://cdn.tailwindcss.com](https://cdn.tailwindcss.com)"></script>
    <link href="[https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css](https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css)" rel="stylesheet">
</head>
<body class="bg-slate-900 text-white font-sans h-screen overflow-hidden">

    <!-- Navbar -->
    <nav class="bg-slate-800 border-b border-slate-700 p-4 flex justify-between items-center">
        <div class="flex items-center gap-3">
            <i class="fas fa-robot text-2xl text-blue-500"></i>
            <span class="text-xl font-bold">Secure QA Agent</span>
        </div>
        <div class="text-xs text-slate-400">Powered by Browser-Use & LangChain</div>
    </nav>

    <div class="flex h-full">
        
        <!-- Sidebar: Configuration -->
        <div class="w-1/3 bg-slate-800 p-6 border-r border-slate-700 overflow-y-auto pb-20">
            <h2 class="text-lg font-semibold mb-4 text-blue-400">1. Configure & Explore</h2>
            <form id="genForm" class="space-y-4">
                <div>
                    <label class="text-xs uppercase text-slate-400">Suite Name</label>
                    <input type="text" id="suiteName" value="Smoke Test A" class="w-full bg-slate-900 border border-slate-600 rounded p-2 text-sm">
                </div>
                <div>
                    <label class="text-xs uppercase text-slate-400">Target URL</label>
                    <input type="url" id="url" value="[https://saucedemo.com](https://saucedemo.com)" class="w-full bg-slate-900 border border-slate-600 rounded p-2 text-sm">
                </div>
                <div class="grid grid-cols-2 gap-2">
                    <div>
                        <label class="text-xs uppercase text-slate-400">Username</label>
                        <input type="text" id="username" value="standard_user" class="w-full bg-slate-900 border border-slate-600 rounded p-2 text-sm">
                    </div>
                    <div>
                        <label class="text-xs uppercase text-slate-400">Password</label>
                        <input type="password" id="password" value="secret_sauce" class="w-full bg-slate-900 border border-slate-600 rounded p-2 text-sm">
                    </div>
                </div>
                <div>
                    <label class="text-xs uppercase text-slate-400">Test Instructions</label>
                    <textarea id="desc" rows="4" class="w-full bg-slate-900 border border-slate-600 rounded p-2 text-sm">Verify the shopping cart flow: Add an item and proceed to checkout.</textarea>
                </div>
                <button type="submit" id="genBtn" class="w-full bg-blue-600 hover:bg-blue-500 py-3 rounded font-bold flex justify-center gap-2">
                    <i class="fas fa-search"></i> Explore & Generate
                </button>
            </form>
        </div>

        <!-- Main Content: Results -->
        <div class="w-2/3 p-8 bg-slate-900 overflow-y-auto pb-20">
            <h2 class="text-lg font-semibold mb-4 text-green-400">2. Generated Test Cases</h2>
            
            <!-- Loader -->
            <div id="loader" class="hidden text-center mt-20">
                <i class="fas fa-circle-notch fa-spin text-4xl text-blue-500"></i>
                <p class="mt-4 text-slate-400">Agent is exploring the UI securely...</p>
            </div>

            <!-- Table -->
            <div id="tableContainer" class="hidden">
                <table class="w-full text-left border-collapse">
                    <thead class="bg-slate-800 text-slate-400 uppercase text-xs">
                        <tr>
                            <th class="p-3 rounded-tl-lg">ID</th>
                            <th class="p-3">Title & Steps</th>
                            <th class="p-3">Status</th>
                            <th class="p-3 rounded-tr-lg text-center">Action</th>
                        </tr>
                    </thead>
                    <tbody id="tableBody" class="divide-y divide-slate-700 bg-slate-800/50"></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const form = document.getElementById('genForm');
        const loader = document.getElementById('loader');
        const tableContainer = document.getElementById('tableContainer');
        const tbody = document.getElementById('tableBody');
        let currentSuite = "";

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            loader.classList.remove('hidden');
            tableContainer.classList.add('hidden');
            document.getElementById('genBtn').disabled = true;

            const payload = {
                suite_name: document.getElementById('suiteName').value,
                url: document.getElementById('url').value,
                description: document.getElementById('desc').value,
                username: document.getElementById('username').value,
                password: document.getElementById('password').value
            };
            currentSuite = payload.suite_name;

            const res = await fetch('/api/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            loader.classList.add('hidden');
            document.getElementById('genBtn').disabled = false;

            if(data.status === 'success') {
                renderTable(data.cases);
                tableContainer.classList.remove('hidden');
            } else {
                alert("Error: " + data.message);
            }
        });

        function renderTable(cases) {
            tbody.innerHTML = '';
            cases.forEach(tc => {
                const row = document.createElement('tr');
                const stepsHtml = tc.steps.map(s => `<div class="text-xs text-slate-400">• ${s}</div>`).join('');
                row.innerHTML = `
                    <td class="p-4 font-mono text-blue-300">${tc.id}</td>
                    <td class="p-4">
                        <div class="font-bold">${tc.title}</div>
                        <div class="mt-2 pl-2 border-l-2 border-slate-600">${stepsHtml}</div>
                    </td>
                    <td class="p-4"><span id="status-${tc.id}" class="bg-slate-700 px-2 py-1 rounded text-xs">Draft</span></td>
                    <td class="p-4 text-center">
                        <button onclick="runTest('${tc.id}')" class="bg-green-600 hover:bg-green-500 text-white px-3 py-1 rounded text-sm">
                            <i class="fas fa-play"></i> Run
                        </button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }

        async function runTest(id) {
            const badge = document.getElementById(`status-${id}`);
            badge.className = "bg-yellow-600 px-2 py-1 rounded text-xs animate-pulse";
            badge.innerText = "Running...";

            const res = await fetch('/api/execute', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ suite_name: currentSuite, test_case_id: id })
            });
            const data = await res.json();

            if(data.result && data.result.includes("PASS")) {
                badge.className = "bg-green-600 px-2 py-1 rounded text-xs";
                badge.innerText = "PASS";
            } else {
                badge.className = "bg-red-600 px-2 py-1 rounded text-xs";
                badge.innerText = "FAIL";
            }
        }
    </script>
</body>
</html>
