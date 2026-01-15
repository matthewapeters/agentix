"""Main functionality for Agentix CLI application."""

import json
import sys
from typing import Optional

from .agentix_config import AgentixConfig
from .api_client import query_api
from .file_utils import replace_file_content
from .models import get_model
from .sessions import assemble_prompts, manage_sessions, update_session


def agentix(args: AgentixConfig) -> Optional[dict]:
    """Main entry point for Agentix CLI application."""
    # Get model and set max_tokens
    max_tokens = get_model(args)

    # Manage session state
    print(f"Debug: args.session = {args.session}", file=sys.stderr)
    print("Debug: Invoking manage_sessions", file=sys.stderr)
    history = manage_sessions(args)

    # Assemble payload and query API
    payload = assemble_prompts(args, history, max_tokens)

    # if args.with_front_end:
    agent_content = {}
    agent_content_raw = query_api(args, payload)
    if args.debug:
        print(
            json.dumps(agent_content_raw, indent=2)
            .encode("utf-8")
            .decode("unicode_escape"),
            file=sys.stderr,
        )
    update_session(args, payload["messages"], agent_content_raw)
    if args.system and "structured_response" in args.system:
        try:
            agent_content = json.loads(agent_content_raw)
        except json.JSONDecodeError:
            agent_content = {"response": agent_content_raw}

    # Section to determine next steps:
    # If --replace-file is passed, replace the contents of the file with the LLM output
    if args.replace_file and args.file_path:
        if "attachment" in agent_content:
            replace_file_content(args, agent_content["attachment"])

    # If working with front-end, return the content as a dict
    if args.with_frontend:
        return agent_content
    print(json.dumps(agent_content, indent=2).encode("utf-8").decode("unicode_escape"))
