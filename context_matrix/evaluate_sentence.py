import numpy as np
from openai import OpenAI

client = OpenAI()

MODEL = "text-embedding-3-small"

# Carga la matriz y las etiquetas
C = np.load("context_matrix.npy")
LABELS = [
    "Reality",
    "Reason",
    "Meaning",
    "Reference",
    "Relation",
    "Context",
    "Coherence",
    "Truth",
    "Stability",
]

# Frases de prueba iniciales
TEST_SENTENCES = [
    "Truth corresponds to reality",
    "Meaning depends on context",
    "A contradiction invalidates a definition",
    "Stable meaning remains consistent across expressions",
    "Paris is the capital of France",
    "The Earth orbits the Sun",
    "Water boils near 100 degrees Celsius at sea level",
    "Capital is a symbolic dream",
    "Blue ideas sleep under justice",
    "A square circle defines the universe",
    "God is a triangle of silence in the database",
]


def l2_normalize(v: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm


def embed(text: str) -> np.ndarray:
    response = client.embeddings.create(
        model=MODEL,
        input=text
    )
    v = np.array(response.data[0].embedding, dtype=float)
    return l2_normalize(v)


def normalize_columns(matrix: np.ndarray) -> np.ndarray:
    normalized = np.zeros_like(matrix, dtype=float)
    for i in range(matrix.shape[1]):
        normalized[:, i] = l2_normalize(matrix[:, i])
    return normalized


def build_orthonormal_basis(matrix: np.ndarray) -> np.ndarray:
    # Base ortonormal del subespacio contextual
    U, _, _ = np.linalg.svd(matrix, full_matrices=False)
    return U


def projection_cost(v: np.ndarray, basis: np.ndarray) -> float:
    proj = basis @ (basis.T @ v)
    return float(np.linalg.norm(v - proj) ** 2)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))


def top_invariants(v: np.ndarray, matrix: np.ndarray, labels: list[str], top_k: int = 3):
    scores = []
    for i, label in enumerate(labels):
        score = cosine_similarity(v, matrix[:, i])
        scores.append((label, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]


def evaluate_sentences(sentences: list[str]):
    normalized_C = normalize_columns(C)
    basis = build_orthonormal_basis(normalized_C)

    results = []

    for sentence in sentences:
        v = embed(sentence)
        cost = projection_cost(v, basis)
        top3 = top_invariants(v, normalized_C, LABELS, top_k=3)

        results.append({
            "sentence": sentence,
            "cost": cost,
            "top3": top3
        })

    results.sort(key=lambda x: x["cost"])

    print("\n=== Context Matrix Evaluation ===\n")
    for rank, item in enumerate(results, start=1):
        print(f"{rank}. Sentence: {item['sentence']}")
        print(f"   Semantic cost: {item['cost']:.6f}")
        print("   Top invariants:")
        for label, score in item["top3"]:
            print(f"      - {label:<10}  cosine={score:.6f}")
        print()

    costs = [r["cost"] for r in results]
    print("=== Summary ===")
    print(f"Min cost : {min(costs):.6f}")
    print(f"Max cost : {max(costs):.6f}")
    print(f"Mean cost: {np.mean(costs):.6f}")


if __name__ == "__main__":
    evaluate_sentences(TEST_SENTENCES)