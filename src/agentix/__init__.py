# Agentix CLI package

from .api_client import query_api, summarize_user_prompt
from .constants import (
    DEFAULT_SESSION_ID,
    DEFAULT_TEMPERATURE,
    MAX_TOKENS,
    OLLAMA_API_BASE,
    SESSIONS_DIR,
    SESSIONS_METADATA_FILE,
    SYSTEM_PROMPTS_DIR,
)
from .file_utils import get_attachments, get_file, load_file
from .main import main
from .models import get_model, get_models
from .prompts import get_prompts, get_system_prompt, get_user_prompt
from .sessions import (
    assemble_payload,
    get_session_history,
    manage_sessions,
    trim_context,
)
from .transforms import transform_ollama_tags_to_openai_engines

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
