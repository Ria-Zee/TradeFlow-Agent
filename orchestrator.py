import importlib.util
import os
import subprocess

DEFAULT_ENDPOINT = "https://ai-account-dvku52phelw2o.openai.azure.com"
DEFAULT_API_VERSION = "2025-01-01-preview"
DEFAULT_MODEL = "gpt-4.1-mini"


def get_azure_token() -> str:
    return subprocess.check_output([
        "az", "account", "get-access-token",
        "--scope", "https://cognitiveservices.azure.com/.default",
        "--query", "accessToken", "-o", "tsv"
    ]).decode().strip()


def run_orchestrator(prompt: str) -> str:
    if importlib.util.find_spec("openai") is None:
        raise RuntimeError("The openai package is required to run orchestrator.py. Install it before using this script.")

    from openai import AzureOpenAI

    token = get_azure_token()
    client = AzureOpenAI(
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", DEFAULT_ENDPOINT),
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", DEFAULT_API_VERSION),
        azure_ad_token=token,
    )

    response = client.chat.completions.create(
        model=os.environ.get("MODEL_DEPLOYMENT_NAME", DEFAULT_MODEL),
        messages=[
            {"role": "system", "content": "You are TradeFlow Orchestrator for African trade intelligence. Decompose trade queries into: 1) market intelligence needs 2) logistics routing needs 3) compliance/risk needs. Reason step by step. Focus on Nigerian/African context."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    default_prompt = "I want to import 500 units of Samsung smartphones from China to Lagos via Apapa port. What do I need to know?"
    print("=== TradeFlow Orchestrator Response ===")
    print(run_orchestrator(default_prompt))
