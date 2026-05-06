from typing import Dict, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .runtime_firewall import SemanticRuntimeFirewall
from .runtime_policy import (
    AGGRESSIVE_PROFILE,
    ENTERPRISE_PROFILE,
    SAFE_PROFILE,
    RuntimePolicyProfile,
)


app = FastAPI(
    title="ACE Semantic Gateway",
    description="Semantic Runtime Firewall for LLM inference routing.",
    version="1.1.0",
)


PROFILE_MAP = {
    "enterprise": ENTERPRISE_PROFILE,
    "aggressive": AGGRESSIVE_PROFILE,
    "safe": SAFE_PROFILE,
}


class AnalyzeRequest(BaseModel):
    costs: Dict[str, float] = Field(
        ...,
        description="Semantic field costs, e.g. conceptual, operational, narrative.",
    )
    coherence_risk: float = Field(
        0.0,
        description="Estimated contradiction or semantic coherence risk.",
    )
    profile: Optional[str] = Field(
        "enterprise",
        description="Runtime profile: enterprise, aggressive, safe.",
    )


class AnalyzeResponse(BaseModel):
    decision: str
    processing_mode: str
    route: str
    confidence: float
    reason: str
    best_field: str
    best_cost: float
    second_field: str
    second_cost: float
    field_margin: float
    coherence_risk: float
    costs: Dict[str, float]
    profile: str


class GuardRequest(BaseModel):
    text: str
    profile: str = "enterprise"


@app.get("/")
def root():
    return {
        "service": "ACE Semantic Gateway",
        "version": "1.1.0",
        "mode": "semantic_runtime_firewall",
        "endpoints": ["/health", "/analyze", "/guard"],
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "ace-semantic-gateway",
        "version": "1.1.0",
    }


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    profile_name = request.profile or "enterprise"
    profile: RuntimePolicyProfile = PROFILE_MAP.get(profile_name, ENTERPRISE_PROFILE)

    firewall = SemanticRuntimeFirewall(profile=profile)

    result = firewall.analyze(
        costs=request.costs,
        coherence_risk=request.coherence_risk,
    )

    return AnalyzeResponse(
        decision=result.decision,
        processing_mode=result.processing_mode,
        route=result.route,
        confidence=result.confidence,
        reason=result.reason,
        best_field=result.best_field,
        best_cost=result.best_cost,
        second_field=result.second_field,
        second_cost=result.second_cost,
        field_margin=result.field_margin,
        coherence_risk=result.coherence_risk,
        costs=result.costs,
        profile=profile.name,
    )


@app.post("/guard")
def guard(request: GuardRequest):
    text = request.text.lower()

    if any(word in text for word in ["square circle", "true and false"]):
        costs = {
            "conceptual": 0.28,
            "operational": 0.74,
            "narrative": 0.79,
        }
        coherence_risk = 0.72

    elif any(word in text for word in ["capital", "temperature", "oxygen", "fact"]):
        costs = {
            "conceptual": 0.82,
            "operational": 0.22,
            "narrative": 0.88,
        }
        coherence_risk = 0.08

    elif any(word in text for word in ["meaning", "truth", "existence", "identity"]):
        costs = {
            "conceptual": 0.18,
            "operational": 0.71,
            "narrative": 0.63,
        }
        coherence_risk = 0.12

    elif any(word in text for word in ["dragon", "wizard", "kingdom", "castle"]):
        costs = {
            "conceptual": 0.62,
            "operational": 0.91,
            "narrative": 0.20,
        }
        coherence_risk = 0.10

    
    else:
        costs = {
            "conceptual": 0.68,
            "operational": 0.70,
            "narrative": 0.69,
        }
        coherence_risk = 0.20

    profile = PROFILE_MAP.get(request.profile, ENTERPRISE_PROFILE)
    firewall = SemanticRuntimeFirewall(profile=profile)

    result = firewall.analyze(
        costs=costs,
        coherence_risk=coherence_risk,
    )

    allow_llm = result.processing_mode != "short"

    return {
        "input": request.text,
        "allow_llm": allow_llm,
        "decision": result.decision,
        "processing_mode": result.processing_mode,
        "route": result.route,
        "confidence": result.confidence,
        "reason": result.reason,
        "best_field": result.best_field,
        "best_cost": result.best_cost,
        "second_field": result.second_field,
        "second_cost": result.second_cost,
        "field_margin": result.field_margin,
        "coherence_risk": result.coherence_risk,
        "profile": profile.name,
    }