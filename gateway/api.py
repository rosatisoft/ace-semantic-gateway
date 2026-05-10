from typing import Dict, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field
from .atlas_adapter import AtlasGatewayAdapter

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
    adapter = AtlasGatewayAdapter(profile=request.profile)
    result = adapter.guard(request.text)

    return {
        "input": result.input,
        "action": result.action,
        "allow_llm": result.allow_llm,
        "processing_mode": result.processing_mode,
        "route": result.route,
        "reason": result.reason,
        "best_field": result.best_field,
        "best_cost": result.best_cost,
        "second_field": result.second_field,
        "second_cost": result.second_cost,
        "field_margin": result.field_margin,
        "best_density": result.best_density,
        "density_margin": result.density_margin,
        "stability_index": result.stability_index,
        "clarification": result.clarification,
        "costs": result.costs,
        "densities": result.densities,
        "profile": result.profile,
    }