# Contributing to ACE Semantic Gateway

First off, thank you for considering contributing to the **ACE Semantic Gateway**. This project aims to stabilize Large Language Model inference through deterministic semantic alignment.

By participating in this project, you help build a more reliable and safe framework for AI interaction.

---

## Citation

If you use the ACE Semantic Gateway in academic work, please cite:

Rosati Beristain, Ernesto.  
ACE Semantic Gateway: Stabilizing Semantic Context in LLM Inference.  
Zenodo. DOI: https://doi.org/10.5281/zenodo.19304475

## How Can You Contribute?

### 1. Research & Theory
The ACE architecture is grounded in the **Minimum Energy Criterion** and **Contextual Reference Fields**. We welcome:
* Formal proofs or mathematical refinements of the Energy Cost function $O(z)$.
* Papers or articles expanding on the linguistic entropy concepts discussed in our documentation.

### 2. Contextual Matrix Expansion
The `context_matrix.py` defines the semantic regions used for alignment. You can contribute by:
* Adding new semantic anchors or intent markers for specialized domains (e.g., Medicine, Law, or specific Industrial Logistics).
* Improving the negative constraints to better detect semantic drift.

### 3. Code & Implementation
* **Bug Reports:** If you find a stability issue or a failure in the context detection, please open an Issue.
* **Feature Requests:** Suggestions for new layers in the pipeline (e.g., integration with RAG systems) are welcome.
* **Optimization:** Improving the efficiency of the ACE Layer's energy estimation.

---

## Contribution Process

1. **Fork the Repository:** Create your own copy of the `rosatisoft/ace-semantic-gateway`.
2. **Create a Branch:** Use descriptive names (e.g., `feature/new-context-domain` or `fix/energy-calculation`).
3. **Commit with Purpose:** Ensure your commit messages reflect the semantic change you are introducing.
4. **Submit a Pull Request:** Provide a clear description of the changes and how they align with the ACE core principles.

## Research Collaboration

Researchers interested in extending the theoretical foundations of ACE 
(e.g., semantic attractors, contextual reference fields, or energy-based 
language inference models) are encouraged to open discussions through 
GitHub Issues or contact the author.

---

## Scientific Integrity & Standards

Since this project is published with a **Zenodo DOI**, we maintain high standards for technical documentation. 
* Ensure any changes to the core logic are reflected in the `docs/` folder.
* If your contribution is substantial for a research paper update, you will be considered for acknowledgement in future revisions.

## Core Architectural Principles

All contributions must respect the following architectural principles:

1. **Semantic Stability First**  
   The system must prioritize contextual coherence before generation.

2. **Deterministic Alignment**  
   The ACE layer should remain deterministic and interpretable.

3. **Separation of Concerns**  
   Semantic interpretation must remain independent from language generation.

4. **Energy-based evaluation**  
   The Origin Cost function $O(z)$ must remain the fundamental stability metric.

Any architectural changes should preserve these principles.

## License

By contributing, you agree that your contributions will be licensed under the **Apache License 2.0**.

---
**Author:** Ernesto Rosati Beristain
**Organization:** rosatisoft