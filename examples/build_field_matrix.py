import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from openai import OpenAI

from gateway.origin_cost import build_svd_basis, normalize_matrix
from gateway.semantic_fields import DEFAULT_SEMANTIC_FIELDS


BASE_DIR = Path(__file__).resolve().parent.parent
FIELDS_DIR = BASE_DIR / "fields"

EMBEDDING_MODEL = "text-embedding-3-small"


def embed_texts(texts):
    client = OpenAI()

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )

    vectors = np.array(
        [item.embedding for item in response.data],
        dtype=float,
    )

    return normalize_matrix(vectors)


def save_field(field_name, anchors):
    field_dir = FIELDS_DIR / field_name
    field_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print(f"Building field: {field_name}")
    print(f"Anchors: {len(anchors)}")

    vectors = embed_texts(anchors)
    basis = build_svd_basis(vectors)

    anchors_payload = {
        "field": field_name,
        "anchors": anchors,
    }

    metadata = {
        "field": field_name,
        "embedding_model": EMBEDDING_MODEL,
        "method": "svd_context_matrix",
        "normalization": True,
        "anchor_count": len(anchors),
        "embedding_dim": int(vectors.shape[1]),
        "basis_shape": list(basis.shape),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    (field_dir / "anchors.json").write_text(
        json.dumps(anchors_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (field_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    np.save(field_dir / "vectors.npy", vectors)
    np.save(field_dir / "basis.npy", basis)

    print("Saved:", field_dir)
    print("Vectors:", vectors.shape)
    print("Basis:", basis.shape)


def main():
    fields = DEFAULT_SEMANTIC_FIELDS.as_dict()

    for field_name in ["conceptual", "operational", "narrative", "scientific", "legal", "business"]:
        save_field(field_name, fields[field_name])


if __name__ == "__main__":
    main()