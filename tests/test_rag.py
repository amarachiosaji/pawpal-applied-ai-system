"""
Evaluation script for the RAGRetriever component.

Tests whether given queries retrieve chunks from the correct knowledge-base
source file, and confirms the guardrail correctly withholds a result when
no chunk clears the confidence threshold.
"""

import os
import sys

# Ensure the project root (where rag_retriever.py lives) is importable,
# regardless of whether this file is run directly or via pytest.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from rag_retriever import RAGRetriever

KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge")


@pytest.fixture(scope="module")
def retriever():
    """Build one RAGRetriever instance shared across all tests in this file."""
    return RAGRetriever(knowledge_dir=KNOWLEDGE_DIR)


# Each case: (query, expected_source_or_None).
# expected_source_or_None = None means we expect the guardrail to return [].
RETRIEVAL_CASES = [
    ("dog walking duration", "dog_walking.md"),
    ("cat matting fur brushing", "cat_grooming.md"),
    ("medication missed dose", "medication_safety.md"),
    ("Grooming Hygiene Cat", "cat_grooming.md"),
    ("Litter box cleaning Hygiene Cat", "pet_hygiene.md"),
    ("Feed & fresh water Feeding Cat", "feeding_schedules.md"),
    ("asdkjqwe nonsense gibberish", None),
]


@pytest.mark.parametrize("query,expected_source", RETRIEVAL_CASES)
def test_retrieval_returns_expected_source(retriever, query, expected_source):
    """For each query, check the top result comes from the expected file
    (or that no result is returned, for the guardrail case)."""
    results = retriever.retrieve(query, top_k=1)

    if expected_source is None:
        assert results == [], (
            f"Expected no confident match for '{query}', "
            f"but got {results[0]['source'] if results else None}"
        )
    else:
        assert results, f"Expected a match from '{expected_source}' for '{query}', got none"
        assert results[0]["source"] == expected_source, (
            f"Query '{query}' matched '{results[0]['source']}', "
            f"expected '{expected_source}'"
        )


def test_guardrail_never_returns_below_threshold(retriever):
    """No returned result should ever score below the retriever's min_score,
    regardless of query."""
    for query, _ in RETRIEVAL_CASES:
        results = retriever.retrieve(query, top_k=5, min_score=0.10)
        for r in results:
            assert r["score"] >= 0.10, f"Result below threshold leaked through: {r}"

def test_known_gray_zone_case_documented(retriever):
    """Documents a known limitation: 'vet appointment' queries sit near the
    threshold and may or may not surface vet_visits.md depending on tuning.
    This test doesn't assert a specific outcome — it just confirms the
    retriever runs without error on this case, since its correctness is a
    documented limitation rather than a hard requirement."""
    results = retriever.retrieve("Vet appointment Health Dog", top_k=1)
    # No assertion on content — just confirming no crash. Outcome (empty or
    # vet_visits.md) is discussed in README/model_card.md as a known limitation.
    assert isinstance(results, list)


if __name__ == "__main__":
    # Quick standalone summary run: python tests/test_rag.py
    r = RAGRetriever(knowledge_dir=KNOWLEDGE_DIR)
    passed = 0
    total = len(RETRIEVAL_CASES)

    print("RAG Retrieval Evaluation")
    print("=" * 50)
    for query, expected in RETRIEVAL_CASES:
        results = r.retrieve(query, top_k=1)
        actual = results[0]["source"] if results else None
        ok = actual == expected
        passed += ok
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] '{query}' -> expected={expected}, got={actual}")

    print("=" * 50)
    print(f"{passed}/{total} queries retrieved the expected source.")