import importlib.util
import os
from enum import Enum

MODEL = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4.1-mini")
PROJECT_ENDPOINT = os.environ.get("PROJECT_ENDPOINT", "")

class MessageRole(str, Enum):
    USER = "user"


def is_agent_service_available() -> bool:
    """Return whether the Azure AI Agents SDK and endpoint are configured."""
    return bool(PROJECT_ENDPOINT) and importlib.util.find_spec("azure.ai.agents") is not None


def get_agents_client():
    """Create an Azure AI Agents client when the optional SDK is installed."""
    if not PROJECT_ENDPOINT:
        raise RuntimeError("PROJECT_ENDPOINT is not set; Azure AI Agents service is unavailable.")
    if importlib.util.find_spec("azure.ai.agents") is None:
        raise RuntimeError("azure-ai-projects/azure-ai-agents SDK is not installed.")

    from azure.ai.agents import AgentsClient
    from azure.identity import DefaultAzureCredential

    return AgentsClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    )
