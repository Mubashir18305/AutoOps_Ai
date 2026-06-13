from typing import TypedDict, Annotated, Sequence, Any, Optional
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_node: str
    context: dict[str, Any]
    final_response: str
    assigned_llm: Optional[str]  # Passed down by Orchestrator (e.g. "gpt-4o", "claude-3-5-sonnet")
    pii_scrubbed: bool           # True if the PII scrubber node has processed the state
