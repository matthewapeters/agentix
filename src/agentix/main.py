import sys
import json
import argparse
from .constants import DEFAULT_TEMPERATURE, DEFAULT_SESSION_ID
from .models import get_models, get_model
from .prompts import get_prompts
from .sessions import manage_sessions, update_session, assemble_payload
from .api_client import query_api


def main():
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
            with open(SESSIONS_METADATA_FILE, "r") as f:
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
    agent_content = query_api(args, payload)
    print(json.dumps(agent_content, indent=2).encode("utf-8").decode("unicode_escape"))
    update_session(args, payload["messages"], agent_content)


if __name__ == "__main__":
    main()
