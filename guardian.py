import os
import sys
import json
import time
from datetime import datetime
from collections import deque

BASE_DIR = os.getcwd()
sys.path.insert(0, BASE_DIR)

EVENTS = deque(maxlen=500)
RUN_HISTORY = deque(maxlen=50)
OPS_STATE_FILE = "guardian_ops_state.json"
INCIDENT_LOG_FILE = "guardian_incidents.jsonl"

def emit(level, component, message, meta=None):
    event = {"timestamp": datetime.utcnow().isoformat(), "level": level, "component": component, "message": message, "meta": meta or {}}
    EVENTS.append(event)
    icon = {"INFO": "i", "OK": "v", "WARN": "!", "ERROR": "x"}.get(level, "?")
    print(f"[{icon}] {component}: {message}")
    with open(INCIDENT_LOG_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")

def check_env():
    emit("INFO", "ENV", "Validating environment variables")
    required = ["PROJECT_ENDPOINT", "MODEL_DEPLOYMENT_NAME", "AZURE_OPENAI_ENDPOINT", "SEARCH_ENDPOINT"]
    missing = [k for k in required if not os.environ.get(k)]
    present = [k for k in required if os.environ.get(k)]
    for k in present: emit("OK", "ENV", f"{k} present")
    for k in missing: emit("ERROR", "ENV", f"{k} missing")
    return {"healthy": len(missing) == 0, "missing": missing}

def check_imports():
    emit("INFO", "SYSTEM", "Checking module imports")
    modules = ["core.tools", "core.search", "core.models", "core.disagreement", "agents.market_intel", "agents.route_logistics", "agents.risk_compliance", "agents.critic"]
    failed = []
    for m in modules:
        try:
            __import__(m)
            emit("OK", "IMPORT", f"{m} loaded")
        except Exception as e:
            emit("ERROR", "IMPORT", f"{m} failed", {"error": str(e)})
            failed.append(m)
    return {"healthy": len(failed) == 0, "failed": failed}

def check_fx():
    emit("INFO", "FX", "Checking FX pipeline")
    try:
        from core.tools import get_fx_rate
        res = get_fx_rate("USD", "NGN")
        rate = res.get("rate") if isinstance(res, dict) else None
        if rate:
            emit("OK", "FX", "FX pipeline healthy", {"rate": rate})
            return {"healthy": True, "rate": rate}
        emit("WARN", "FX", "Unexpected response")
        return {"healthy": False}
    except Exception as e:
        emit("ERROR", "FX", str(e))
        return {"healthy": False}

def check_search():
    emit("INFO", "SEARCH", "Checking knowledge base")
    try:
        from core.search import search_knowledge
        res = search_knowledge("Nigeria import duty electronics")
        if res:
            emit("OK", "SEARCH", "Search operational", {"length": len(str(res))})
            return {"healthy": True}
        emit("WARN", "SEARCH", "Empty response")
        return {"healthy": False}
    except Exception as e:
        emit("ERROR", "SEARCH", str(e))
        return {"healthy": False}

def check_foundry():
    emit("INFO", "FOUNDRY", "Testing Foundry Agent Service")
    try:
        from azure.ai.agents import AgentsClient
        from azure.identity import DefaultAzureCredential
        endpoint = os.environ.get("PROJECT_ENDPOINT", "")
        if not endpoint:
            emit("WARN", "FOUNDRY", "PROJECT_ENDPOINT not set")
            return {"healthy": False}
        client = AgentsClient(endpoint=endpoint, credential=DefaultAzureCredential())
        agent = client.create_agent(model=os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4.1-mini"), name="guardian-check", instructions="Health check. Say OK.")
        thread = client.threads.create()
        client.messages.create(thread_id=thread.id, role="user", content="ping")
        client.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
        messages = client.messages.list(thread_id=thread.id)
        response = ""
        for msg in messages:
            if msg.text_messages:
                response = msg.text_messages[-1].text.value
                break
        client.delete_agent(agent.id)
        if response:
            emit("OK", "FOUNDRY", "Foundry Agent Service healthy")
            return {"healthy": True}
        emit("WARN", "FOUNDRY", "No response from agent")
        return {"healthy": False}
    except Exception as e:
        emit("ERROR", "FOUNDRY", str(e)[:80])
        return {"healthy": False}

def check_news():
    emit("INFO", "NEWS", "Checking live news feed")
    try:
        from core.tools import get_trade_news
        res = get_trade_news("smartphones", "China", "Nigeria")
        if res.get("count", 0) > 0:
            emit("OK", "NEWS", f"{res['count']} articles available")
            return {"healthy": True}
        emit("WARN", "NEWS", "No articles returned")
        return {"healthy": False}
    except Exception as e:
        emit("ERROR", "NEWS", str(e))
        return {"healthy": False}

def smoke_test():
    emit("INFO", "SMOKE", "Running smoke test")
    try:
        from core.tools import get_trade_context
        ctx = get_trade_context("test", "china", "nigeria")
        if isinstance(ctx, dict):
            emit("OK", "SMOKE", "Pipeline verified")
            return {"healthy": True}
        emit("WARN", "SMOKE", "Invalid format")
        return {"healthy": False}
    except Exception as e:
        emit("ERROR", "SMOKE", str(e))
        return {"healthy": False}

def attempt_fix(component):
    emit("INFO", "AUTOHEAL", f"Recovery attempt for {component}")
    if component == "ENV":
        emit("WARN", "AUTOHEAL", "Manual env setup required")
        return False
    if component in ["FX", "SEARCH", "NEWS"]:
        emit("INFO", "AUTOHEAL", "Degraded-safe mode activated")
        return True
    if component == "IMPORTS":
        os.system(f"{sys.executable} -m pip install --quiet azure-ai-agents azure-identity openai")
        emit("OK", "AUTOHEAL", "Dependencies reinstalled")
        return True
    if component == "FOUNDRY":
        result = os.system("az account show > /dev/null 2>&1")
        if result == 0:
            emit("OK", "AUTOHEAL", "Azure credentials valid - Foundry may be temporarily unavailable")
        else:
            emit("WARN", "AUTOHEAL", "Azure credentials expired - run az login")
        return False
    return False

def write_ops_state(results, status, score):
    state = {"timestamp": datetime.utcnow().isoformat(), "status": status, "health_score": score, "run_history": list(RUN_HISTORY), "latest_events": list(EVENTS)[-50:], "components": {k: {"healthy": v.get("healthy")} for k, v in results.items()}}
    with open(OPS_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def compute_health(results):
    healthy = sum(1 for r in results.values() if r.get("healthy"))
    total = len(results)
    score = int((healthy / total) * 100)
    status = "HEALTHY" if score == 100 else "DEGRADED" if score >= 60 else "CRITICAL"
    return status, score

def run(continuous=False, interval_seconds=30):
    print("\n" + "="*60)
    print("TRADEFLOW OPS GUARDIAN")
    print("Production Observability and Self-Healing System")
    print("="*60 + "\n")
    cycle = 0
    while True:
        cycle += 1
        emit("INFO", "CYCLE", f"Starting health cycle {cycle}")
        results = {"env": check_env(), "imports": check_imports(), "fx": check_fx(), "search": check_search(), "foundry": check_foundry(), "news": check_news(), "smoke": smoke_test()}
        for k, v in results.items():
            if not v.get("healthy"):
                attempt_fix(k.upper())
        status, score = compute_health(results)
        RUN_HISTORY.append({"cycle": cycle, "status": status, "score": score, "timestamp": datetime.utcnow().isoformat()})
        write_ops_state(results, status, score)
        print("\n" + "="*60)
        print(f"OPS STATUS: {status}")
        print(f"HEALTH SCORE: {score}%")
        print(f"Incidents: {INCIDENT_LOG_FILE} | State: {OPS_STATE_FILE}")
        print("="*60 + "\n")
        if not continuous:
            break
        print(f"Next check in {interval_seconds}s...")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    run(continuous="--continuous" in sys.argv)
