import os
from langchain_openai import ChatOpenAI

def get_llm(assigned_llm: str = "sarvam-105b"):
    """
    Factory to instantiate the Sarvam API LangChain model.
    Uses ChatOpenAI as a client for the Sarvam OpenAI-compatible endpoint.
    Requires SARVAM_API_KEY environment variable.
    """
    api_key = os.getenv("SARVAM_API_KEY", "your-sarvam-api-key")
    # Assuming Sarvam provides an OpenAI-compatible API endpoint.
    # Update base_url to the actual Sarvam endpoint if different.
    base_url = os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai/v1")
    
    return ChatOpenAI(
        model=assigned_llm,
        api_key=api_key,
        base_url=base_url,
        temperature=0.2,
        max_tokens=2048
    )
