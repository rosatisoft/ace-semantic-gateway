from gateway.context_matrix import ContextMatrix

cm = ContextMatrix()

tests = [
    "What is the meaning of life?",
    "Why is my server failing to boot after changing the storage controller?",
    "How do I prove a derivative?",
    "Why do people feel anxiety?",
    "What makes a painting beautiful?",
    "Should I tell the truth if it will hurt someone?",
]

for t in tests:
    r = cm.match_context(t)

    print("INPUT:", t)
    print("CONTEXT:", r.best_context.name if r.best_context else None)
    print("SUBCONTEXT:", r.best_subcontext)
    print("SCORE:", round(r.best_score, 4))
    print("AMBIGUOUS:", r.is_ambiguous)
    print("CLARIFY:", r.needs_clarification)
    print("CANDIDATES:", r.candidate_contexts)
    print("QUESTION:", r.clarification_question)
    print("METADATA:", r.metadata)
    print("-" * 70)