"""
pytest configuration for autonomous-test-agent.

Ensures that the project root is on sys.path so that `src.*` imports resolve
correctly when running `pytest` from the project root directory.
"""
import sys
from pathlib import Path

# Add the repo root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))
