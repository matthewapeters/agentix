"""
Docstring for agentix.message
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Message:
    def __init__(self, role: str, content: str, attachments: list = None):
        self.role = role
        self.content = content
        self.attachments: Optional[list] = attachments
