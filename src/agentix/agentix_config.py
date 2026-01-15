"""
Docstring for agentix.agentix_config
"""

import argparse
from argparse import Namespace
from dataclasses import dataclass

from .constants import DEFAULT_SESSION_ID, DEFAULT_TEMPERATURE

# pylint: disable=too-many-instance-attributes


@dataclass
class AgentixConfig:
    """Configuration settings for Agentix"""

    list_models: bool = False
    list_sessions: bool = False
    list_prompts: bool = False
    session: str = "default_session"
    system: list[str] | None = None
    model: str | None = None
    temperature: float = 0.7
    user: list[str] | None = None
    file: str | None = None
    replace_file: bool = False
    server: bool = False
    port: int = 8000
    with_frontend: bool = False

    @staticmethod
    def cli_arguments() -> "AgentixConfig":
        """
        Docstring for cli_arguments

        :return: Description
        :rtype: AgentixConfig
        """
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
        args.add_argument(
            "--debug", type=bool, default=False, help="Enable debug output"
        )
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
        args: Namespace = args.parse_args()

        return AgentixConfig(
            list_models=args.list_models,
            list_sessions=args.list_sessions,
            list_prompts=args.list_prompts,
            session=args.session,
            system=args.system,
            model=args.model,
            temperature=args.temperature,
            user=args.user,
            file=args.file,
            replace_file=args.replace_file,
            server=args.server,
            port=args.port,
            with_frontend=args.with_frontend,
        )
