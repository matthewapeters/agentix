from agentix.agentix_config import AgentixConfig
from agentix.prompt_classification_response import NextStep

from . import escalate, invoke_planner, respond_directly, single_tool


def take_steps(args: AgentixConfig, next_step: NextStep, history: list[dict]):
    # Take next steps based on classification
    match next_step:
        case NextStep.escalate:
            escalate(args, next_step, history)
        case NextStep.invoke_planner:
            invoke_planner(args, next_step, history)
        case NextStep.single_tool:
            single_tool(args, next_step, history)
        case _:
            respond_directly(args, next_step, history)
