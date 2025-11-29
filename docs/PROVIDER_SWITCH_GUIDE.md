# LLM Provider Switch Guide

## Summary of Changes Made (Gemini → Ollama Fara-7B)

### Changed Files: 1
**File:** `.env` (3 lines modified)

### Exact Changes Made:

```diff
# Line 3: Provider Selection
- LLM_PROVIDER=gemini
+ LLM_PROVIDER=custom

# Line 16: Ollama Base URL
- CUSTOM_BASE_URL=http://localhost:8000/v1
+ CUSTOM_BASE_URL=http://localhost:11434/v1

# Line 18: Model Name
- CUSTOM_MODEL_NAME=microsoft/Fara-7B
+ CUSTOM_MODEL_NAME=hf.co/bartowski/microsoft_Fara-7B-GGUF:latest
```

### What This Does:
1. **Switches provider** to `custom` (triggers Ollama integration)
2. **Points to Ollama** API endpoint (port 11434)
3. **Uses correct model name** as it appears in Ollama

---

## How to Switch Back to Gemini

### Option 1: Quick One-Line Change (Recommended)
**Edit `.env` file - Change line 3 only:**
```bash
LLM_PROVIDER=custom    # CHANGE THIS
↓
LLM_PROVIDER=gemini    # TO THIS
```

That's it! Restart server and you're back to Gemini.

### Option 2: Full Restore (If you modified other lines)
**Edit `.env` file - Restore these 3 lines:**
```bash
# Line 3
LLM_PROVIDER=gemini

# Line 16 (optional - not used when provider=gemini)
CUSTOM_BASE_URL=http://localhost:8000/v1

# Line 18 (optional - not used when provider=gemini)
CUSTOM_MODEL_NAME=microsoft/Fara-7B
```

---

## Quick Reference: Provider Values

| Provider | Value in .env | What it uses |
|----------|---------------|--------------|
| **Google Gemini** | `LLM_PROVIDER=gemini` | Cloud API (GOOGLE_API_KEY) |
| **OpenAI GPT** | `LLM_PROVIDER=openai` | Cloud API (OPENAI_API_KEY) |
| **Anthropic Claude** | `LLM_PROVIDER=anthropic` | Cloud API (ANTHROPIC_API_KEY) |
| **Ollama (Local)** | `LLM_PROVIDER=custom` | Local Ollama (port 11434) |

---

## How to Restart Server

After ANY change to `.env`:
```bash
# Kill existing server
lsof -t -i:8000 | xargs kill -9

# Restart
python server.py
```

Or if server is running in terminal: `Ctrl+C` then `python server.py`

---

## Verification Commands

### Check Current Provider:
```bash
grep "LLM_PROVIDER" .env
```

### Test Ollama is Running:
```bash
curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | head -3
```

### Test Gemini API Key:
```bash
grep "GOOGLE_API_KEY" .env | grep -v "^#"
```

---

## Code Files (NO CHANGES NEEDED)

These files already support both providers - NO modifications required:
- ✅ `config.py` - Already has multi-provider config
- ✅ `llm_factory.py` - Already has custom provider support
- ✅ `server.py` - Provider-agnostic
- ✅ `explorer_agent.py` - Works with any LLM

**Everything is already built to support switching!**

---

## Performance Comparison

| Metric | Gemini (Cloud) | Fara-7B (Local Ollama) |
|--------|----------------|------------------------|
| **Speed** | Fast (~2-3s/call) | Slower (~5-10s/call) |
| **Privacy** | Data sent to cloud | 100% local |
| **Cost** | Free tier limits | Free forever |
| **Requires Internet** | Yes | No |
| **Quality** | Very good | Good (smaller model) |

---

## Troubleshooting

### If Ollama doesn't work:
1. Check Ollama is running: `ollama list`
2. Check port: `lsof -i :11434`
3. Verify model name matches: `ollama list | grep Fara`

### If Gemini doesn't work:
1. Check API key is set: `grep GOOGLE_API_KEY .env`
2. Check quota: Visit https://ai.google.dev/usage
3. Verify provider: `grep LLM_PROVIDER .env`

---

**Last Updated:** 2025-11-29
**Current Status:** Using Ollama + Fara-7B (Local)
