"""
AI QA Testing Agent - Main Entry Point
Starts the FastAPI server for the testing automation system
"""
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 AI QA Testing Agent")
    print("=" * 60)
    print("Starting server on http://localhost:8000")
    print("Press CTRL+C to stop")
    print("=" * 60)
    
    uvicorn.run(
        "src.core.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
