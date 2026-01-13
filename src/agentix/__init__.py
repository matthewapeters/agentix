# Agentix CLI package

from .main import main
from .models import get_models, get_model
from .prompts import get_system_prompt, get_user_prompt, get_prompts
from .sessions import (
    get_session_history,
    trim_context,
    manage_sessions,
    assemble_payload,
)
from .api_client import query_api, summarize_user_prompt
from .file_utils import load_file, get_file, get_attachments
from .transforms import transform_ollama_tags_to_openai_engines
from .constants import (
    MAX_TOKENS,
    SYSTEM_PROMPTS_DIR,
    SESSIONS_DIR,
    SESSIONS_METADATA_FILE,
    OLLAMA_API_BASE,
    DEFAULT_TEMPERATURE,
    DEFAULT_SESSION_ID,
)

__all__ = [
    "main",
    "get_models",
    "get_model",
    "get_system_prompt",
    "get_user_prompt",
    "get_prompts",
    "get_session_history",
    "trim_context",
    "manage_sessions",
    "assemble_payload",
    "query_api",
    "summarize_user_prompt",
    "load_file",
    "get_file",
    "get_attachments",
    "MAX_TOKENS",
    "SYSTEM_PROMPTS_DIR",
    "SESSIONS_DIR",
    "SESSIONS_METADATA_FILE",
    "OLLAMA_API_BASE",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_SESSION_ID",
    "transform_ollama_tags_to_openai_engines",
]
