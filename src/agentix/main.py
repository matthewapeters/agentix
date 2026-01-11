import sys
import glob
import json
from datetime import datetime, UTC
import argparse
import requests

_MAX_TOKENS = 4096

def load_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def get_models(args):
    result = requests.get("http://localhost:11434/api/tags")
    models_json = result.json()
    
    if args.debug:
        print("Available models:", file=sys.stderr)
        print(json.dumps(models_json, indent=2), file=sys.stderr)
        print(f"Filtering models with prefix: {args.model}", file=sys.stderr)

    models =[m 
            for m in models_json["models"] 
            # filter based on model_name if provided
            if (args.model and m["name"].startswith(args.model)) or (not args.model)
            ]
    # return the first matching model or default to the first model
    if models and len(models) == 1:
        return models
    return models_json["models"]

def parse_parameter_size(param_size: str) -> int:
    """
    Convert a parameter size string (e.g., "1.5B") to an integer value.
    Supported suffixes: K (thousand), M (million), B (billion).
    """
    suffix_multipliers = {
        "K": 1000,
        "M": 1000000,
        "B": 1000000000,
    }
    try:
        # Split the numeric part and the suffix
        num = float(param_size[:-1])  # Extract the number (e.g., "1.5")
        suffix = param_size[-1].upper()  # Extract the suffix (e.g., "B")
        return int(num * suffix_multipliers.get(suffix, 1))  # Default multiplier is 1
    except (ValueError, KeyError):
        raise ValueError(f"Invalid parameter size format: {param_size}")


def get_model(args) -> tuple[str, int]:
    global _MAX_TOKENS
    models = get_models(args)
    if len(models)>1:
        if args.debug:
            print(f"Multiple models found matching '{args.model}':\n{json.dumps(models, indent=2)}",  file=sys.stderr)
            print("Using the first model found: {model[0]['name']}",  file=sys.stderr)
    model = models[0]
    if args.debug:
        print(f"Using model:\n{json.dumps(model, indent=2)}",  file=sys.stderr)
    # Convert parameter_size to _MAX_TOKENS
    try:
        MAX_TOKENS = parse_parameter_size(model["details"]["parameter_size"])
    except Exception as e:
        if args.debug:
            print(json.dumps(model, indent=2), file=sys.stderr)
        raise ValueError(f"Invalid parameter size format: {model['details']['parameter_size']}")
    args.model = model["name"]

def get_file(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = load_file(file_path)
        return f"---- FILE: {file_path} ----\n{content}\n---- END OF FILE ----\n\n"
    except Exception as e:
        print(f"Error loading file {file_path}: {e}", file=sys.stderr)
        return ""

def get_attachments(args) -> list[dict]:
    attachments = []
    for attachment_path in args.file_path or []:
        try:
            attachments.append(get_file(attachment_path))
        except Exception as e:
            print(f"Error loading attachment {attachment_path}: {e}", file=sys.stderr)
    return attachments

def get_system_prompt(args) -> str:
    """
    get_system_prompt

    
    :param args: Description
    :return: Description
    :rtype: str
    """
    systemprompt = ""
    dir="./system_prompts/"
    # get the system prompts and map their paths to their friendly names (no dir, no ext)
    prompts = {p.replace(dir,"").split(".")[0]:p for p in glob.glob(f"{dir}*.*")}
    if args.debug:
        print(f"Available system prompts: {json.dumps(prompts, indent=2)}", file=sys.stderr)
    for canned_system_prompt_path in args.system or []:
        prompt_path = prompts[canned_system_prompt_path] 
        if args.debug:
            print(f"Loading system prompt from: {prompt_path}", file=sys.stderr)
        systemprompt += get_file(prompt_path)
    return f"[SYSTEM]\n{systemprompt}\n[END SYSTEM]\n\n"

def get_user_prompt(args) -> str:
    return "\n".join(args.user or [])

def get_session_history(session_id: str) -> list[dict]:
    dir = "./sessions/"
    try:
        # find the most recent timestamped file matching the session id
        session_file = glob.glob(f"{dir}/{session_id}_*.json")[-1]
        with open(session_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
            return history
    except (FileNotFoundError, IndexError):
        return []

def trim_context(args, messages: list[dict]) -> list[dict]:
    history = get_session_history(args.session) or []
    history.extend(messages)

    # Checkpoint history
    dir = "./sessions/"
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    with open(f"{dir}{args.session}_{ts}.json", 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)

    # Trim history based on token limits (_MAX_TOKENS)
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
        if total_tokens + message_tokens > _MAX_TOKENS:
            break  # Stop adding messages if the limit is exceeded

        # Add the message to the trimmed history and update the token count
        trimmed_history.append(message)
        total_tokens += message_tokens

    # Reverse the trimmed history to maintain chronological order
    trimmed_history.reverse()

    return trimmed_history


def assemble_payload(args):
    messages =[
            {"role": "system", "content": get_system_prompt(args)},
            {"role": "user", 
             "content": get_user_prompt(args),
             "attachments": get_attachments(args)}] 

    contextual_messages = trim_context(args, messages)

    return {
        "model": args.model,
        "messages": contextual_messages,
        "temperature": args.temperature,
    }

def query_api(args, payload: dict) -> dict:
    headers = {
        "Content-Type": "application/json",
    }

    if args.debug:
        print("Payload:", file=sys.stderr)
        print(json.dumps(payload, indent=2), file=sys.stderr)

    response = requests.post("http://localhost:11434/v1/chat/completions", headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        result = response.json()

        if args.debug:
            print("Raw response:", file=sys.stderr)
            print(json.dumps(result, indent=2), file=sys.stderr)

        answer = result["choices"][0]["message"]["content"]
        reasoning = result["choices"][0]["message"].get("reasoning", "")
        finish_reason = result["choices"][0].get("finish_reason", "")

        if args.debug:
            print("Finish reason:", finish_reason, file=sys.stderr)
            print("Response:", file=sys.stderr)
            print(answer, file=sys.stderr)
            print("\nReasoning:", file=sys.stderr)
            print(reasoning, file=sys.stderr)
        return answer
    else:
        print("Error:", response.status_code, response.text)


def summarize_user_prompt(args: str) -> str:
    # Use query_api to generate a session summary name based on the user prompt
    summary_payload = {
        "model": args.model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an assistant that generates concise session names based on prompts.\n"
                    "Generate a short, descriptive session name (3-5 words) that captures the essence of the user's prompt.\n"
                    "Avoid using special characters or spaces in the session name.\n"
                    "Respond with only the session name without any additional text."
                )
            },
            {
                "role": "user",
                "content":get_user_prompt(args) 
            }
        ],
        "temperature": 0.8,
    }
    response = query_api(args, summary_payload)
    # Clean up the response to create a valid session ID
    session_id = response.strip().replace(" ", "_").replace("/", "_")
    args.session = session_id


def manage_sessions(args):
    # if no specific session is requested, (session == agentix_session) then summarize 
    # the prompt and add it to the "agentix_sessions" file

    match args.session:
        case "agentix_session":
            summarize_user_prompt(args)
            try:
                with open("agentix_sessions.json", "r", encoding='utf-8') as f:
                    sessions = json.load(f)
            except FileNotFoundError:
                sessions = {"sessions": []}

            sessions["sessions"].append({
                "session_id": args.session,
                "model": args.model,
                "created_at": datetime.now(UTC).isoformat(),})
            with open("agentix_sessions.json", "w", encoding='utf-8') as f:
                json.dump(sessions, f, indent=2)
        case "__continue":
            # continue the session
            try:
                with open("agentix_sessions.json", "r", encoding='utf-8') as f:
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

def get_prompts(args):
    prompts = {}
    dir = "./system_prompts/"
    for prompt_glob in [glob.glob(f"{dir}*.*")]:
        if args.debug:
            print(f"Prompt: {prompt_glob}", file=sys.stderr)
        if prompt_glob and isinstance(prompt_glob, list):
            for prompt in prompt_glob:
               with open(prompt, 'r', encoding="utf8") as f:
                   lines = [l for l in f.readlines() if l != "\n" and l != ""]
               first_lines = lines[:2]
               prompts[prompt.replace(dir,'').split(".")[0]] = first_lines
    return prompts


def main():
    args = argparse.ArgumentParser(description="Agentix CLI")
    args.add_argument("--list-models", dest="list_models", default=False, action="store_true", help="List all available models")
    args.add_argument("--list-sessions", dest="list_sessions", default=False, action="store_true", help="List all sessions")
    args.add_argument("--list-prompts", dest="list_prompts", default=False, action="store_true", help="List all system prompts")
    args.add_argument("--session", type=str, dest="session", default="agentix_session", help="Session ID for the conversation")
    args.add_argument( "--system", type=str, action="append", dest="system", help="The system prompt to send to the API")
    args.add_argument( "--model", type=str,  dest="model", help="The model to use")
    args.add_argument( "--temp", type=float, dest="temperature", default=0.2, help="Sampling temperature")
    args.add_argument( "--user", type=str, action="append", dest="user", help="The user prompt to send to the API")
    args.add_argument( "--file", type=str, action="append", dest="file_path", help="Path to the file containing the prompt")
    args.add_argument( "--debug", type=bool, default=False,  help="The system prompt to send to the API")
    args.add_argument("--with-front-end", dest="with_front_end", default=False, action="store_true", help="Agentix is working with a front-end")
    args = args.parse_args()

    # if the user is requesting to list models, list them and return
    if args.list_models:
        print(json.dumps(get_models(args), indent=2))
        return

    if args.list_prompts:
        print(json.dumps(get_prompts(args), indent=2))
        return

    # if the user is requesting to list sessions, list the contents of agentix_sessions and return
    if args.list_sessions:
        try:
            with open("agentix_sessions.json", "r") as f:
                for line in f.readlines():
                    print(line.strip())
        except FileNotFoundError:
            print("No sessions found", file=sys.stderr)
        return

    get_model(args)
    manage_sessions(args)
    payload = assemble_payload(args)
    if args.with_front_end:
        print(query_api(args, payload))


if __name__ == "__main__":
    main()
