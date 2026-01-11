# File I/O utilities for Agentix CLI

import sys
from .constants import SYSTEM_PROMPTS_DIR


def load_file(file_path: str) -> str:
    """Load the raw contents of a file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def get_file(file_path: str) -> str:
    """Load a file and return it with formatted output wrapper."""
    try:
        content = load_file(file_path)
        return f"---- FILE: {file_path} ----\n{content}\n---- END OF FILE ----\n\n"
    except Exception as e:
        print(f"Error loading file {file_path}: {e}", file=sys.stderr)
        return ""


def get_attachments(args) -> list:
    """Load multiple file attachments from file paths provided in args."""
    attachments = []
    for attachment_path in args.file_path or []:
        try:
            attachments.append(get_file(attachment_path))
        except Exception as e:
            print(f"Error loading attachment {attachment_path}: {e}", file=sys.stderr)
    return attachments
