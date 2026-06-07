import os
import subprocess
from openai import AzureOpenAI

def get_client():
    token = subprocess.check_output([
        "az", "account", "get-access-token",
        "--scope", "https://cognitiveservices.azure.com/.default",
        "--query", "accessToken", "-o", "tsv"
    ]).decode().strip()

    return AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version="2025-01-01-preview",
        azure_ad_token=token,
    )

MODEL = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4.1-mini")
