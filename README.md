# TradeFlow Command System
### AI-Powered Multi-Agent Trade Intelligence for African Importers and Exporters

> Built for the Microsoft Agents League Hackathon 2026 — Reasoning Agents Track

---

## What is TradeFlow?

TradeFlow is a multi-agent AI system that helps African SME importers and exporters make high-confidence cross-border trade decisions.

It does not give you a number. It gives you a **decision** — with reasoning, confidence levels, risk flags, and a full audit trail of every assumption made.

**Example query:**
> "I want to import 500 units of Samsung smartphones from China to Lagos via Apapa port."

**TradeFlow responds with:**
- Market intelligence analysis (FX risk, duties, demand signals)
- Logistics routing options (Apapa vs Tincan vs Cotonou)
- Compliance and risk assessment (SONCAP, NCC, customs requirements)
- A verified final trade recommendation (PROCEED / PROCEED WITH CAUTION / PAUSE)
- A full decision traceability report showing every assumption and data flag

---

## The Crisis Commander Loop

TradeFlow is not a static query system. It is a dynamic re-planning intelligence system.

When a disruption signal arrives — a port closure, FX spike, policy change, or supplier fraud alert — TradeFlow automatically re-runs the entire agent chain with the new context and produces a revised recommendation.

---

## Agent Architecture

- Orchestrator Agent: decomposes query, routes to specialists, manages state
- Market Intelligence Agent: FX rates, duties, demand signals, landed cost
- Route and Logistics Agent: port conditions, freight options, transit times
- Risk and Compliance Agent: SONCAP, NCC, NAFDAC, supplier risk, FX risk
- Critic and Verifier Agent: cross-checks all outputs, scores confidence, final verdict

---

## Responsible AI Design

- Every data point flagged as ESTIMATED or ASSUMED
- Every assumption listed explicitly
- Confidence levels assigned per agent
- No fabricated tariff rates or regulatory requirements
- Traders directed to verify with SON, NAFDAC, NCC, Nigeria Customs

---

## Tech Stack

- Platform: Microsoft Azure AI Foundry
- Model: gpt-4.1-mini (East US 2)
- SDK: azure-ai-projects, openai Python SDK
- Authentication: Azure DefaultAzureCredential
- Language: Python 3.11+

---

## Setup

```bash
export AZURE_OPENAI_ENDPOINT="your_azure_openai_endpoint"
export MODEL_DEPLOYMENT_NAME="gpt-4.1-mini"
pip install openai azure-ai-projects azure-identity
python3 tradeflow.py
```

---

## Hackathon Track

Track: Reasoning Agents — Microsoft Foundry
Additional category: Hack for Good

---

## Built by

Mary Ezinne Obasi (Ria-Zee)
AI Automation and Agentic Engineer
Lagos/Abuja, Nigeria
