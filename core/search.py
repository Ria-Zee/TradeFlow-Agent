import os
import json
import urllib.request
import subprocess

SEARCH_ENDPOINT = os.environ.get("SEARCH_ENDPOINT", "https://tradeflow-search.search.windows.net")
INDEX_NAME = "african-trade-knowledge"

def get_search_key():
    result = subprocess.run([
        "az", "search", "admin-key", "show",
        "--service-name", "tradeflow-search",
        "--resource-group", "rg-tradeflow-east",
        "--query", "primaryKey", "-o", "tsv"
    ], capture_output=True, text=True)
    return result.stdout.strip()

def search_knowledge(query: str, top: int = 2) -> str:
    try:
        search_key = get_search_key()
        payload = {
            "search": query,
            "select": "title,content",
            "top": top,
            "queryType": "simple"
        }
        url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}/docs/search?api-version=2023-11-01"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json", "api-key": search_key},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            results = json.loads(response.read())
            docs = results.get("value", [])
            if not docs:
                return "No relevant knowledge base documents found."
            combined = []
            for doc in docs:
                combined.append(f"[SOURCE: {doc['title']}]\n{doc['content'][:800]}")
            return "\n\n".join(combined)
    except Exception as e:
        return f"Knowledge base search unavailable: {str(e)}"
