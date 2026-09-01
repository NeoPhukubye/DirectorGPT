"""Base agent class with communication protocol."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from director_gpt.models.project import ProjectState


class MessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    PROPOSAL = "proposal"
    CRITIQUE = "critique"
    REVISION = "revision"
    APPROVAL = "approval"
    REJECTION = "rejection"


@dataclass
class AgentMessage:
    sender: str
    recipient: str
    message_type: MessageType
    content: str
    data: dict = field(default_factory=dict)
    requires_response: bool = False

    def to_dict(self) -> dict:
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type.value,
            "content": self.content,
            "data": self.data,
            "requires_response": self.requires_response,
        }


class BaseAgent(ABC):
    """Base class for all DirectorGPT agents."""

    def __init__(self, name: str, state: ProjectState):
        self.name = name
        self.state = state
        self.inbox: list[AgentMessage] = []
        self.outbox: list[AgentMessage] = []
        self.context: dict = {}

    @abstractmethod
    def process(self, input_data: dict) -> dict:
        """Main processing method for the agent."""
        pass

    @abstractmethod
    def get_role_description(self) -> str:
        """Return description of this agent's role."""
        pass

    def send_message(self, recipient: str, message_type: MessageType,
                     content: str, data: dict = None, requires_response: bool = False):
        """Send a message to another agent."""
        msg = AgentMessage(
            sender=self.name,
            recipient=recipient,
            message_type=message_type,
            content=content,
            data=data or {},
            requires_response=requires_response,
        )
        self.outbox.append(msg)
        self.state.add_message(self.name, f"-> {recipient}: {content}")

    def receive_message(self, message: AgentMessage):
        """Receive a message from another agent."""
        self.inbox.append(message)
        self.state.add_message(self.name, f"<- {message.sender}: {message.content}")

    def get_pending_responses(self) -> list[AgentMessage]:
        """Get messages that require a response."""
        return [m for m in self.inbox if m.requires_response and m.sender != self.name]

    def clear_inbox(self):
        """Clear processed messages."""
        self.inbox = [m for m in self.inbox if m.requires_response]

    def clear_outbox(self):
        """Clear sent messages."""
        self.outbox = []

    def update_context(self, key: str, value: Any):
        """Update agent's working context."""
        self.context[key] = value

    def log(self, message: str):
        """Log agent activity."""
        self.state.add_message(self.name, message)
