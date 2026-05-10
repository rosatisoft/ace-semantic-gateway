import numpy as np


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector)

    if norm == 0:
        return vector

    return vector / norm


def normalize_matrix(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def build_svd_basis(anchor_vectors: np.ndarray) -> np.ndarray:
    """
    Build an orthonormal semantic field basis using SVD.

    anchor_vectors shape:
        (n_anchors, embedding_dim)

    Context matrix:
        C = anchor_vectors.T
    """

    anchor_vectors = normalize_matrix(anchor_vectors)

    C = anchor_vectors.T

    U, S, Vt = np.linalg.svd(C, full_matrices=False)

    return U


def origin_cost(vector: np.ndarray, basis: np.ndarray) -> float:
    """
    Compute semantic origin cost:

        O(z) = ||z - P_S(z)||²

    where:
        z = candidate vector
        S = contextual semantic subspace
        P_S(z) = projection of z onto S
    """

    z = normalize_vector(vector)

    projection = basis @ (basis.T @ z)

    residual = z - projection

    return float(np.linalg.norm(residual) ** 2)