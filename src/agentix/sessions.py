# Session management for Agentix CLI

import os
import sys
import json
import glob
from datetime import datetime, UTC
from .constants import SESSIONS_DIR, SESSIONS_METADATA_FILE, MAX_TOKENS, DEFAULT_SESSION_ID


def get_session_history(session_id: str) -> list:
    """Retrieve session history JSON from timestamped files."""

    os.makedirs(f"{SESSIONS_DIR}{session_id}", exist_ok=True)
    try:
        # find the most recent timestamped file matching the session id
        session_file = glob.glob(f"{SESSIONS_DIR}{session_id}/*.json")[-1]
        with open(session_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
            return history
    except (FileNotFoundError, IndexError):
        return []


def trim_context(args, messages: list, max_tokens: int) -> list:
    """Handle message history with token-based trimming."""
    history = get_session_history(args.session) or []
    history.extend(messages)

    os.makedirs(f"{SESSIONS_DIR}{args.session}", exist_ok=True)
    # Checkpoint history
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    with open(f"{SESSIONS_DIR}{args.session}/{ts}.json", 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)

    # Trim history based on token limits (max_tokens)
    total_tokens = 0
    trimmed_history = []

    # Iterate over messages from the most recent to the oldest
    for message in reversed(history):
        # Estimate tokens for the current message
        # Assuming 1 token per 4 characters as a rough approximation
        message_tokens = len(message["content"]) // 4
        if "attachments" in message:
            for attachment in message["attachments"]:
                message_tokens += len(attachment) // 4

        # Check if adding this message exceeds the token limit
        if total_tokens + message_tokens > max_tokens:
            break  # Stop adding messages if the limit is exceeded

        # Add the message to the trimmed history and update the token count
        trimmed_history.append(message)
        total_tokens += message_tokens

    # Reverse the trimmed history to maintain chronological order
    trimmed_history.reverse()

    return trimmed_history


def manage_sessions(args):
    """Create, retrieve, and manage session state."""
    # if no specific session is requested, (session == agentix_session) then summarize 
    # the prompt and add it to the sessions metadata file

    match args.session:
        case "agentix_session":
            # summarize_user_prompt is called from api_client.py to avoid circular imports
            try:
                with open(SESSIONS_METADATA_FILE, "r", encoding='utf-8') as f:
                    sessions = json.load(f)
            except FileNotFoundError:
                sessions = {"sessions": []}

            sessions["sessions"].append({
                "session_id": args.session,
                "model": args.model,
                "created_at": datetime.now(UTC).isoformat(),
            })
            with open(SESSIONS_METADATA_FILE, "w", encoding='utf-8') as f:
                json.dump(sessions, f, indent=2)
        case "__continue":
            # continue the session
            try:
                with open(SESSIONS_METADATA_FILE, "r", encoding='utf-8') as f:
                    sessions = json.load(f)
            except FileNotFoundError:
                sessions = {"sessions": []}
            # get the last session
            if sessions["sessions"]:
                if args.debug:
                    print("Continuing session:", sessions["sessions"][-1], file=sys.stderr)
                args.session = sessions["sessions"][-1]["session_id"]
                # Continue with the same model if not specified
                if not args.model:
                    args.model = sessions["sessions"][-1]["model"]

def update_session(args, history: list, response: str):
    """Update session history with the latest interaction."""
    #history = get_session_history(args.session) or []

    # Append user message
    #user_message = next((msg for msg in payload["messages"] if msg["role"] == "user"), None)
    #if user_message:
    #    history.append(user_message)

    # Append assistant message
    assistant_message = {
        "role": "assistant",
        "content": response
    }
    history.append(assistant_message)

    # Save updated history
    os.makedirs(f"{SESSIONS_DIR}{args.session}", exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    with open(f"{SESSIONS_DIR}{args.session}/{ts}.json", 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)
