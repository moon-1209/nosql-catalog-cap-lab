"""Root launch script for the Hospital Helper Robot RL Training & Telemetry Dashboard."""

import sys
from pathlib import Path

# Add project root to sys.path
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.ui.rl_dashboard import main

if __name__ == "__main__":
    main()
