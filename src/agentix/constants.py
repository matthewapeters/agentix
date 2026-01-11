# Constants for Agentix CLI

# Token limits
MAX_TOKENS = 4096

# Directory paths
SYSTEM_PROMPTS_DIR = "./system_prompts/"
SESSIONS_DIR = "./sessions/"
SESSIONS_METADATA_FILE = "agentix_sessions.json"

# API configuration
OLLAMA_API_BASE = "http://localhost:11434"
OLLAMA_MODELS_ENDPOINT = "/api/tags"
OLLAMA_CHAT_ENDPOINT = "/v1/chat/completions"

# Default values
DEFAULT_TEMPERATURE = 0.2
DEFAULT_SESSION_ID = "agentix_session"
CONTINUE_SESSION_ID = "__continue"
