import numpy as np
from openai import OpenAI

client = OpenAI()

MODEL = "text-embedding-3-small"

GENERAL_BUNDLE = "context_matrix_bundle.npz"
FACTUAL_BUNDLE = "factual_context_bundle.npz"

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
    response = client.embeddings.create(model=MODEL, input=text)
    v = np.array(response.data[0].embedding, dtype=float)
    return l2_normalize(v)


def load_bundle(path: str) -> dict:
    data = np.load(path, allow_pickle=True)
    return {
        "C_norm": data["C_norm"],
        "basis": data["basis"],
        "mean_vector": data["mean_vector"],
        "labels": data["labels"].tolist(),
    }


def projection_cost(v: np.ndarray, basis: np.ndarray, mean_vector: np.ndarray) -> float:
    v_centered = v.reshape(-1, 1) - mean_vector
    proj = basis @ (basis.T @ v_centered)
    residual = v_centered - proj
    return float(np.linalg.norm(residual) ** 2)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))


def top_invariants(v: np.ndarray, matrix: np.ndarray, labels: list[str], top_k: int = 3):
    scores = []
    for i, label in enumerate(labels):
        scores.append((label, cosine_similarity(v, matrix[:, i])))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]


def evaluate_dual(sentences: list[str]):
    general = load_bundle(GENERAL_BUNDLE)
    factual = load_bundle(FACTUAL_BUNDLE)

    print("\n=== Dual Context Evaluation ===\n")

    for sentence in sentences:
        v = embed(sentence)

        g_cost = projection_cost(v, general["basis"], general["mean_vector"])
        f_cost = projection_cost(v, factual["basis"], factual["mean_vector"])

        g_top = top_invariants(v, general["C_norm"], general["labels"])
        f_top = top_invariants(v, factual["C_norm"], factual["labels"])

        print(f"Sentence: {sentence}")
        print(f"   General cost : {g_cost:.6f}")
        print(f"   Factual cost : {f_cost:.6f}")
        print("   Top general invariants:")
        for label, score in g_top:
            print(f"      - {label:<18} cosine={score:.6f}")
        print("   Top factual invariants:")
        for label, score in f_top:
            print(f"      - {label:<18} cosine={score:.6f}")
        print()


if __name__ == "__main__":
    evaluate_dual(TEST_SENTENCES)