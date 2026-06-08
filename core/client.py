import os
from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential

def get_agents_client():
    return AgentsClient(
        endpoint=os.environ["PROJECT_ENDPOINT"],
        credential=DefaultAzureCredential(),
    )

MODEL = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4.1-mini")
PROJECT_ENDPOINT = os.environ.get("PROJECT_ENDPOINT", "")
