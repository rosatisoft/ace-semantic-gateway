from typing import Dict, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field
from .embedding_router import EmbeddingRouter

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
    router = EmbeddingRouter()
    semantic_profile = router.analyze_text(request.text)

    profile = PROFILE_MAP.get(request.profile, ENTERPRISE_PROFILE)
    firewall = SemanticRuntimeFirewall(profile=profile)

    result = firewall.analyze(
        costs=semantic_profile.costs,
        coherence_risk=semantic_profile.coherence_risk,
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
        "costs": result.costs,
        "profile": profile.name,
    }

