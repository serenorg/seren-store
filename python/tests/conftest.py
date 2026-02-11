# ABOUTME: Pytest configuration for seren-agent SDK tests.
# ABOUTME: Adds the python/ directory to sys.path so tests can import seren_agent.
import sys
from pathlib import Path

# Add the python SDK root to sys.path so seren_agent is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

# Prevent pytest from collecting test_agent alias in seren_agent/testing.py
collect_ignore_glob = ["**/seren_agent/**"]
