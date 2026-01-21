"""
Docstring for agentix.next_steps.invoke_planner
"""

from agentix import AgentixConfig
from agentix.api_client import query_api
from agentix.next_steps.take_steps import NextStep

INVOKE_PLANNER_PROMPT = "invoke_planner"


def invoke_planner(
    args: AgentixConfig, next_step: NextStep, history: list[dict]
) -> str:
    """
    Docstring for invoke_planner

    invoke the LLM for a structured plan to address the user's prompt

    The goal is produce a machine-readable todo-list with tool-calls

    params:
    args: AgentixConfig User prompt and settings
    next_step: NextStep The LLM's directions for how to handle the user request
    history: list[dict] The conversation history between the user and the LLM
    """
    planner_args: AgentixConfig = AgentixConfig()
    planner_args.debug = args.debug
    planner_args.system = [INVOKE_PLANNER_PROMPT]
    planner_args.user = args.user
    planner_args.file_path = args.file_path
    planner_args.model = args.model

    result = query_api(planner_args, history)
