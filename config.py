import os
from pathlib import Path
from typing import Literal

# Base Directory paths
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.getenv("COMPILER_DB_PATH", str(BASE_DIR / "compiler.db"))

# Execution settings
ExecutionMode = Literal["FAST", "BALANCED", "HIGH_QUALITY"]
DEFAULT_MODE: ExecutionMode = "BALANCED"

# Gemini API details (for future phases)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Ensure required runtime directories exist
def init_directories():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

init_directories()
