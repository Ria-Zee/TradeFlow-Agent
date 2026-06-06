import os
import subprocess
from openai import AzureOpenAI

token = subprocess.check_output([
    "az", "account", "get-access-token",
    "--scope", "https://cognitiveservices.azure.com/.default",
    "--query", "accessToken", "-o", "tsv"
]).decode().strip()

client = AzureOpenAI(
    azure_endpoint="https://ai-account-dvku52phelw2o.openai.azure.com",
    api_version="2025-01-01-preview",
    azure_ad_token=token,
)

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": "You are TradeFlow Orchestrator for African trade intelligence. Decompose trade queries into: 1) market intelligence needs 2) logistics routing needs 3) compliance/risk needs. Reason step by step. Focus on Nigerian/African context."},
        {"role": "user", "content": "I want to import 500 units of Samsung smartphones from China to Lagos via Apapa port. What do I need to know?"}
    ]
)

print("=== TradeFlow Orchestrator Response ===")
print(response.choices[0].message.content)
