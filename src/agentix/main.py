"""agentix main module"""

import json
import sys

from .agentix_config import AgentixConfig
from .api_client import query_api
from .constants import SESSIONS_METADATA_FILE
from .file_utils import replace_file_content
from .models import get_model, get_models
from .prompts import get_prompts
from .server import start_server
from .sessions import assemble_payload, manage_sessions, update_session


def main(args: AgentixConfig):
    """agentix main functionality"""

    # if the user is requesting to list models, list them and return
    if args.list_models:
        print(json.dumps(get_models(args), indent=2))
        return

    if args.list_prompts:
        print(json.dumps(get_prompts(args), indent=2))
        return

    # if the user is requesting to list sessions, list the contents of sessions
    #  metadata file and return
    if args.list_sessions:

        try:
            with open(SESSIONS_METADATA_FILE, "r", encoding="utf-8") as f:
                for line in f.readlines():
                    print(line.strip())
        except FileNotFoundError:
            print("No sessions found", file=sys.stderr)
        return

    # If --serve is passed, launch the FastAPI server
    if args.serve:
        start_server(args.port)
        return

    # Get model and set max_tokens
    max_tokens = get_model(args)

    # Manage session state
    print(f"Debug: args.session = {args.session}", file=sys.stderr)
    print("Debug: Invoking manage_sessions", file=sys.stderr)
    history = manage_sessions(args)

    # Assemble payload and query API
    payload = assemble_payload(args, history, max_tokens)

    # if args.with_front_end:
    agent_content = {}
    agent_content_raw = query_api(args, payload)
    print(
        json.dumps(agent_content_raw, indent=2).encode("utf-8").decode("unicode_escape")
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


if __name__ == "__main__":
    main(AgentixConfig.cli_arguments())
