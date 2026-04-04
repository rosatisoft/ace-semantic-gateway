import json
import numpy as np
from pathlib import Path
from prototypes import PROTOTYPES
from openai import OpenAI

client = OpenAI()

MODEL = "text-embedding-3-small"
BUNDLE_FILE = "context_matrix_bundle.npz"
META_FILE = "context_matrix_meta.json"


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
    return np.array(response.data[0].embedding, dtype=float)


def build_category_centroid(sentences: list[str]) -> np.ndarray:
    vectors = np.array([embed(s) for s in sentences], dtype=float)
    centroid = np.mean(vectors, axis=0)
    return centroid


def normalize_columns(matrix: np.ndarray) -> np.ndarray:
    normalized = np.zeros_like(matrix, dtype=float)
    for i in range(matrix.shape[1]):
        normalized[:, i] = l2_normalize(matrix[:, i])
    return normalized


def build_context_bundle():
    labels = []
    counts = []
    raw_vectors = []

    for label, sentences in PROTOTYPES.items():
        centroid = build_category_centroid(sentences)
        labels.append(label)
        counts.append(len(sentences))
        raw_vectors.append(centroid)

    c_raw = np.column_stack(raw_vectors)
    c_norm = normalize_columns(c_raw)

    mean_vector = np.mean(c_norm, axis=1, keepdims=True)
    c_centered = c_norm - mean_vector

    u, s, _ = np.linalg.svd(c_centered, full_matrices=False)

    return {
        "C_raw": c_raw,
        "C_norm": c_norm,
        "C_centered": c_centered,
        "basis": u,
        "singular_values": s,
        "mean_vector": mean_vector,
        "labels": np.array(labels, dtype=object),
        "counts": np.array(counts, dtype=int),
    }


def save_bundle(bundle: dict):
    np.savez(
        BUNDLE_FILE,
        C_raw=bundle["C_raw"],
        C_norm=bundle["C_norm"],
        C_centered=bundle["C_centered"],
        basis=bundle["basis"],
        singular_values=bundle["singular_values"],
        mean_vector=bundle["mean_vector"],
        labels=bundle["labels"],
        counts=bundle["counts"],
    )

    meta = {
        "model": MODEL,
        "bundle_file": BUNDLE_FILE,
        "num_labels": int(len(bundle["labels"])),
        "labels": bundle["labels"].tolist(),
        "counts": bundle["counts"].tolist(),
        "dimension": int(bundle["C_norm"].shape[0]),
        "num_columns": int(bundle["C_norm"].shape[1]),
    }

    Path(META_FILE).write_text(
        json.dumps(meta, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    return meta


def main():
    bundle = build_context_bundle()
    meta = save_bundle(bundle)

    print("Context bundle built successfully")
    print(f"Bundle file : {BUNDLE_FILE}")
    print(f"Meta file   : {META_FILE}")
    print(f"Shape       : {bundle['C_norm'].shape}")
    print(f"Labels      : {meta['labels']}")
    print(f"Counts      : {meta['counts']}")
    print("Singular values:")
    print(bundle["singular_values"])


if __name__ == "__main__":
    main()