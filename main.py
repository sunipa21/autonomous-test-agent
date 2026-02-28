"""
Autonomous Test Agent — Main Entry Point
Starts the FastAPI server for the AI-powered browser testing system.
"""
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 Autonomous Test Agent")
    print("=" * 60)
    print("  Server : http://localhost:8000")
    print("  Docs   : http://localhost:8000/docs")
    print("  Audit  : http://localhost:8000/audit")
    print("  Press CTRL+C to stop")
    print("=" * 60)

    uvicorn.run(
        "src.core.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
