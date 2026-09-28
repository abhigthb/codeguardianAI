import os

# Check the current model name in Google AI Studio if this one stops working.
MODEL_NAME = os.getenv("CG_MODEL", "gemini-2.0-flash")

ALLOWED_EXT = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".php", ".rb", ".c", ".cpp"}
SKIP_DIRS = ("node_modules", "venv", ".git", "dist", "build", "__pycache__", "site-packages", ".venv")
MAX_FILE_BYTES = 40_000
MAX_FILES = 8              # keep low for free API limits
DELAY_BETWEEN_CALLS = 2.0  # seconds, avoids rate-limit errors