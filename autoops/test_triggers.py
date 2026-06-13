from src.triggers.tasks import run_scheduled_research

def test_celery_task_locally():
    # Calling the task function directly without the Celery worker just to verify the LangGraph integration
    print("Executing Research Task directly...")
    result = run_scheduled_research()
    print("\nResult from Triggered Orchestrator:")
    print(result)

if __name__ == "__main__":
    test_celery_task_locally()
