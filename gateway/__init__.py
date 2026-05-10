# Runtime firewall exports
from .field_competition import FieldCompetitionResult, analyze_field_competition
from .runtime_firewall import RuntimeFirewallResult, SemanticRuntimeFirewall
from .runtime_policy import (
    AGGRESSIVE_PROFILE,
    ENTERPRISE_PROFILE,
    SAFE_PROFILE,
    RuntimePolicyProfile,
    RuntimePolicyResult,
    decide_runtime_policy,
)

# Legacy v1 gateway exports
# These may require the external/minimum-energy ACE package.
try:
    from .ace_layer import ACELayer, ACELayerResult
    from .context_field import ContextField, ContextFieldBuilder
    from .context_matrix import ContextMatrix
    from .gateway import GatewayResult, SemanticGateway
except ModuleNotFoundError as e:
    print("Legacy gateway import failed:", e)
    ACELayer = None
    ACELayerResult = None
    ContextField = None
    ContextFieldBuilder = None
    ContextMatrix = None
    GatewayResult = None
    SemanticGateway = None

try:
    from .runtime_firewall import SemanticRuntimeFirewall, RuntimeFirewallResult
except ModuleNotFoundError as e:
    print("Legacy gateway import failed:", e)
    SemanticRuntimeFirewall = None
    RuntimeFirewallResult = None

__all__ = [
    "FieldCompetitionResult",
    "analyze_field_competition",
    "RuntimeFirewallResult",
    "SemanticRuntimeFirewall",
    "RuntimePolicyProfile",
    "RuntimePolicyResult",
    "ENTERPRISE_PROFILE",
    "AGGRESSIVE_PROFILE",
    "SAFE_PROFILE",
    "decide_runtime_policy",
    "ACELayer",
    "ACELayerResult",
    "ContextField",
    "ContextFieldBuilder",
    "ContextMatrix",
    "GatewayResult",
    "SemanticGateway",
]