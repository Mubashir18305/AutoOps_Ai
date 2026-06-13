import asyncio
import uuid
from langchain_core.messages import HumanMessage
from src.triggers.celery_app import celery_app
from src.orchestrator import create_orchestrator_graph

def run_graph_sync(message_content: str, user_id: str):
    """
    Helper to run the LangGraph orchestrator synchronously from a Celery worker.
    """
    graph = create_orchestrator_graph()
    thread_id = f"cron_{uuid.uuid4()}"
    
    initial_state = {
        "messages": [HumanMessage(content=message_content)],
        "context": {"user_id": user_id, "source": "celery_cron"},
        "next_node": "",
        "final_response": ""
    }
    config = {"configurable": {"thread_id": thread_id}}
    
    # Run the event loop synchronously for the worker
    result = asyncio.run(graph.ainvoke(initial_state, config=config))
    return result.get("final_response")

@celery_app.task
def run_scheduled_research():
    """
    Periodic task: Executes a scheduled web research workflow.
    """
    prompt = "Research the latest competitor pricing changes and synthesize the findings."
    print(f"Triggering background research task...")
    result = run_graph_sync(prompt, user_id="system_cron")
    return result

@celery_app.task
def run_scheduled_crm_sync():
    """
    Periodic task: Executes a daily CRM sync workflow.
    """
    prompt = "Sync all new leads from Salesforce into the Notion database."
    print(f"Triggering background CRM sync task...")
    result = run_graph_sync(prompt, user_id="system_cron")
    return result

@celery_app.task
def trigger_event_workflow(event_payload: dict):
    """
    Event-driven task: Called by Webhooks (like GitHub Actions) to run async workflows.
    """
    prompt = f"Process incoming event from {event_payload.get('source')}: {event_payload.get('action')}"
    result = run_graph_sync(prompt, user_id="system_webhook")
    return result
