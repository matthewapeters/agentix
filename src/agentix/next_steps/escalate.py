from agentix import AgentixConfig
from agentix.message import Message
from agentix.prompt_classification_response import NextStep


def escalate(
    args: AgentixConfig, next_step: NextStep, history: list[Message], max_tokens: int
) -> str:
    pass
