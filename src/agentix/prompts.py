# Prompt management for Agentix CLI

import glob
import json
import sys

from .constants import SYSTEM_PROMPTS_DIR
from .file_utils import get_file


def get_system_prompt(args) -> str:
    """Load system prompts from files and return formatted."""
    systemprompt = ""
    # get the system prompts and map their paths to their friendly names (no dir, no ext)
    prompts = {
        p.replace(SYSTEM_PROMPTS_DIR, "").split(".")[0]: p
        for p in glob.glob(f"{SYSTEM_PROMPTS_DIR}*.*")
    }
    if args.debug:
        print(
            f"Available system prompts: {json.dumps(prompts, indent=2)}",
            file=sys.stderr,
        )
    for canned_system_prompt_path in args.system or []:
        prompt_path = prompts[canned_system_prompt_path]
        if args.debug:
            print(f"Loading system prompt from: {prompt_path}", file=sys.stderr)
        systemprompt += get_file(prompt_path)
    return f"[SYSTEM]\n{systemprompt}\n[END SYSTEM]\n\n"


def get_user_prompt(args) -> str:
    """Assemble user prompt from CLI arguments."""
    return "\n".join(args.user or [])


def get_prompts(args) -> dict:
    """List available system prompts with preview lines."""
    prompts = {}
    for prompt_glob in [glob.glob(f"{SYSTEM_PROMPTS_DIR}*.*")]:
        if args.debug:
            print(f"Prompt: {prompt_glob}", file=sys.stderr)
        if prompt_glob and isinstance(prompt_glob, list):
            for prompt in prompt_glob:
                with open(prompt, "r", encoding="utf8") as f:
                    lines = [l for l in f.readlines() if l != "\n" and l != ""]
                first_lines = lines[:2]
                prompts[prompt.replace(SYSTEM_PROMPTS_DIR, "").split(".")[0]] = (
                    first_lines
                )
    return prompts
