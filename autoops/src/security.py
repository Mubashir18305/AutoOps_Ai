from src.schema import AgentState
from langchain_core.messages import HumanMessage, AIMessage
import re
import uuid

def pii_scrubber_node(state: AgentState) -> dict:
    """
    Security by Design: Dedicated node to intercept and strip PII before routing.
    """
    messages = state.get("messages", [])
    if not messages:
        return {"pii_scrubbed": True}
        
    last_message = messages[-1]
    
    scrubbed_content = last_message.content
    # Mask emails
    scrubbed_content = re.sub(r'[\w\.-]+@[\w\.-]+', '[EMAIL_REDACTED]', scrubbed_content)
    # Mask 10-digit phone numbers
    scrubbed_content = re.sub(r'\b\d{10}\b', '[PHONE_REDACTED]', scrubbed_content)
    
    # If content changed, we want to update the last message.
    # In LangGraph, to update a message, we must provide a message with the same ID.
    if scrubbed_content != last_message.content:
        msg_id = last_message.id if hasattr(last_message, "id") and last_message.id else str(uuid.uuid4())
        
        if isinstance(last_message, HumanMessage):
            updated_msg = HumanMessage(content=scrubbed_content, id=msg_id)
        else:
            updated_msg = AIMessage(content=scrubbed_content, id=msg_id)
            
        # We only return the updated message, LangGraph will replace the existing one with the same ID.
        return {"messages": [updated_msg], "pii_scrubbed": True}
        
    return {"pii_scrubbed": True}
