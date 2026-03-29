from gateway import SemanticGateway

gw = SemanticGateway(verbose=True)

tests = [
    "What is the meaning of life?",
    "Why is my server failing to boot after changing the storage controller?",
    "How do I prove a derivative?",
    "Why do people feel anxiety?",
    "What makes a painting beautiful?",
    "Should I tell the truth if it will hurt someone?",
]

for t in tests:
    print("=" * 80)
    print("INPUT:", t)
    result = gw.process_request(t)
    print("DECISION:", result.decision)
    print("PATH:", result.path)
    print("SCORE:", result.score)
    print("RESPONSE:", result.response)
    print("METADATA:", result.metadata)
    print()