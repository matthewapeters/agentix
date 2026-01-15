import argparse
import json
import sys

from .api_client import query_api
from .constants import DEFAULT_SESSION_ID, DEFAULT_TEMPERATURE
from .file_utils import replace_file_content
from .models import get_model, get_models
from .prompts import get_prompts
from .sessions import assemble_payload, manage_sessions, update_session


def main():
    """agentix main entry point"""
    args = argparse.ArgumentParser(description="Agentix CLI")
    args.add_argument(
        "--list-models",
        dest="list_models",
        default=False,
        action="store_true",
        help="List all available models",
    )
    args.add_argument(
        "--list-sessions",
        dest="list_sessions",
        default=False,
        action="store_true",
        help="List all sessions",
    )
    args.add_argument(
        "--list-prompts",
        dest="list_prompts",
        default=False,
        action="store_true",
        help="List all system prompts",
    )
    args.add_argument(
        "--session",
        type=str,
        dest="session",
        default=DEFAULT_SESSION_ID,
        help="Session ID for the conversation",
    )
    args.add_argument(
        "--system",
        type=str,
        action="append",
        dest="system",
        help="The system prompt to send to the API",
    )
    args.add_argument("--model", type=str, dest="model", help="The model to use")
    args.add_argument(
        "--temp",
        "--temperature",
        type=float,
        dest="temperature",
        default=DEFAULT_TEMPERATURE,
        help="Sampling temperature",
    )
    args.add_argument(
        "--user",
        type=str,
        action="append",
        dest="user",
        help="The user prompt to send to the API",
    )
    args.add_argument(
        "--file",
        type=str,
        action="append",
        dest="file_path",
        help="Path to the file containing the prompt",
    )
    args.add_argument(
        "--replace-file",
        dest="replace_file",
        default=False,
        action="store_true",
        help="Replace the file contents with the LLM output",
    )
    args.add_argument("--debug", type=bool, default=False, help="Enable debug output")
    args.add_argument(
        "--with-front-end",
        dest="with_front_end",
        default=False,
        action="store_true",
        help="Agentix is working with a front-end",
    )
    args.add_argument(
        "--serve",
        dest="serve",
        default=False,
        action="store_true",
        help="Launch FastAPI server",
    )
    args.add_argument(
        "--port",
        type=int,
        dest="port",
        default=8000,
        help="Port to serve on (default: 8000)",
    )
    args = args.parse_args()

    # if the user is requesting to list models, list them and return
    if args.list_models:
        print(json.dumps(get_models(args), indent=2))
        return

    if args.list_prompts:
        print(json.dumps(get_prompts(args), indent=2))
        return

    # if the user is requesting to list sessions, list the contents of sessions metadata file and return
    if args.list_sessions:
        from .constants import SESSIONS_METADATA_FILE

        try:
            with open(SESSIONS_METADATA_FILE, "r", encoding="utf-8") as f:
                for line in f.readlines():
                    print(line.strip())
        except FileNotFoundError:
            print("No sessions found", file=sys.stderr)
        return

    # If --serve is passed, launch the FastAPI server
    if args.serve:
        from .server import start_server

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
    if "structured_response" in args.system:
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
    main()
