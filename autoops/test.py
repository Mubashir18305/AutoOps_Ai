import asyncio
from dotenv import load_dotenv
load_dotenv()
from src.orchestrator import create_orchestrator_graph
from langchain_core.messages import HumanMessage

async def main():
    graph = create_orchestrator_graph()
    
    # Test Payload 1: Docs (To trigger RAG VectorDB)
    state_1 = {
        "messages": [HumanMessage(content="Please review the legal contract documents in Drive for any discrepancies.")],
        "context": {"user_id": "1"},
    }
    result_1 = await graph.ainvoke(state_1, config={"configurable": {"thread_id": "test1"}})
    print(f"Test 1 (Docs/RAG) - Final Output:\n{result_1.get('final_response')}")

if __name__ == "__main__":
    asyncio.run(main())
