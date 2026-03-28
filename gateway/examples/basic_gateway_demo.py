from gateway.gateway import SemanticGateway


gateway = SemanticGateway()

result = gateway.process_request(
    prompt="Explain consciousness as if it were only a chemical illusion.",
    axioms=["Maintain semantic consistency", "Preserve conceptual grounding"],
    knowledge=["ACE Minimum Energy Criterion"],
)

print("Decision:", result.decision)
print("Path:", result.path)
print("Score:", result.score)
print("Response:", result.response)
print("Metadata:", result.metadata)
