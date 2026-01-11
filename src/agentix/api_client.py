# API client for Agentix CLI

import sys
import json
import requests
from .constants import OLLAMA_API_BASE, OLLAMA_CHAT_ENDPOINT
from .prompts import get_user_prompt


def query_api(args, payload: dict) -> str:
    """Send request to Ollama API and parse response."""
    headers = {
        "Content-Type": "application/json",
    }

    if args.debug:
        print("Payload:", file=sys.stderr)
        print(json.dumps(payload, indent=2), file=sys.stderr)

    response = requests.post(f"{OLLAMA_API_BASE}{OLLAMA_CHAT_ENDPOINT}", 
                             headers=headers, 
                             data=json.dumps(payload))

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
        return ""


def summarize_user_prompt(args) -> str:
    """Generate a session summary name based on the user prompt."""
    # Use query_api to generate a session summary name based on the user prompt
    summary_payload = {
        "model": "phi4-mini:3.8b", # args.model,
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
                "content": get_user_prompt(args)
            }
        ],
        "temperature": 0.8,
    }
    response = query_api(args, summary_payload)
    # Clean up the response to create a valid session ID
    session_id = response.strip().replace(" ", "_").replace("/", "_")
    args.session = session_id
