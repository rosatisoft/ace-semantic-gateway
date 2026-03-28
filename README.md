# ACE Semantic Gateway

Semantic middleware for LLMs that routes requests using the ACE Minimum Energy Criterion and deep axiomatic reasoning.

## Overview

ACE Semantic Gateway is an orchestration layer for language model systems.

It evaluates incoming requests through a semantic stability criterion before deciding how the system should respond.

The gateway uses two levels of analysis:

1. **ACE Minimum Energy Criterion** for fast semantic screening  
2. **Axiomatic Criterion Engine** for deep reasoning when semantic deviation is high  

This makes the gateway suitable for systems that require stronger control over semantic drift, hallucination risk, and unstable responses.

---

## Core Idea

A request enters the gateway and is first evaluated with the **ACE Minimum Energy Criterion**.

- If the semantic cost is low, the request follows the **FAST path**
- If the semantic cost is high, the request is escalated to **deep axiomatic analysis**

This allows the system to remain lightweight for well-grounded inputs while still providing stronger reasoning when ambiguity or semantic instability is detected.

---
## Concept

ACE Semantic Gateway introduces **pre-prompt semantic control for LLM systems**.

Instead of relying solely on prompt engineering, the gateway evaluates the semantic stability of a request **before generation occurs**.

This creates a deterministic layer that routes requests according to their semantic alignment.

## Pre-Prompt Semantic Layer

```text
input
  │
  ▼
pre-prompt semantic layer
  │
  ▼
LLM
```
Traditional systems operate directly from prompt to generation.

ACE Semantic Gateway introduces a pre-prompt semantic layer that evaluates semantic stability before the request reaches the model.

This enables:

prompt-agnostic routing
geometric semantic evaluation
grounded vector alignment
deterministic semantic control
answer / clarify / abstain decisions before generation

## Architecture

```text
User Request
     │
     ▼
ACE Semantic Gateway
     │
     ├─ ACE Minimum Energy Criterion
     │        │
     │        ├─ low origin cost
     │        │        ▼
     │        │     FAST PATH
     │        │        ▼
     │        │     LLM Response
     │        │
     │        └─ high origin cost
     │                 ▼
     │           Deep Analysis
     │                 ▼
     │      Axiomatic Criterion Engine
     │
     ▼
Final Decision
```
Repository Structure
     ├─ answer
     ├─ clarify
     └─ abstain

```
     ace-semantic-gateway
│
├─ gateway/                    ← core middleware
│  ├─ __init__.py
│  ├─ gateway.py               ← main orchestrator
│  ├─ pipeline.py              ← request pipeline
│  ├─ decision.py              ← answer / clarify / abstain logic
│  ├─ embedding_layer.py       ← embedding interface
│  ├─ ace_layer.py             ← ACE Minimum Energy integration
│  └─ deep_reasoning.py        ← deep axiomatic reasoning integration
│
├─ adapters/                   ← external model providers
│  ├─ openai_adapter.py
│  ├─ ollama_adapter.py
│  └─ local_embedding_adapter.py
│
├─ api/                        ← REST or service interface
│  ├─ app.py
│  └─ routes.py
│
├─ configs/
│  └─ gateway_config.yaml
│
├─ examples/
│  └─ basic_gateway_demo.py
│
├─ tests/
│  └─ test_gateway.py
│
├─ README.md
├─ pyproject.toml
└─ LICENSE
```

