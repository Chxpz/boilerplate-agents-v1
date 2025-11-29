from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from operator import add


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add]
    context: str
    next_action: str
