"""Ranking-quality metrics for the evaluation page (R6)."""

import json
from typing import Dict, List, Sequence

from search_engine import SearchIndex

DEFAULT_K = 3
MAX_K = 10


def precision_at_k(ranked: Sequence[str], relevant: Sequence[str], k: int) -> float:
    """Fraction of the top k results that are relevant. The denominator is always k."""
    if k <= 0:
        raise ValueError("k must be a positive integer")
    relevant_set = set(relevant)
    hits = sum(1 for doc_id in ranked[:k] if doc_id in relevant_set)
    return hits / k


def reciprocal_rank(ranked: Sequence[str], relevant: Sequence[str]) -> float:
    """1 / rank of the first relevant result, or 0.0 if none is retrieved."""
    relevant_set = set(relevant)
    for position, doc_id in enumerate(ranked, start=1):
        if doc_id in relevant_set:
            return 1.0 / position
    return 0.0


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def mean_reciprocal_rank(reciprocal_ranks: Sequence[float]) -> float:
    return mean(reciprocal_ranks)


def load_queries(path: str) -> List[Dict]:
    """Load [{"query": str, "relevant": [doc ids]}, ...] and validate its shape."""
    with open(path, "r", encoding="utf-8") as handle:
        try:
            data = json.load(handle)
        except json.JSONDecodeError as error:
            raise ValueError("Evaluation file is not valid JSON: {}".format(error))
    if not isinstance(data, list):
        raise ValueError("Evaluation file must contain a list of queries.")
    queries = []
    for number, item in enumerate(data, start=1):
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("query"), str)
            or not item["query"].strip()
            or not isinstance(item.get("relevant"), list)
            or not item["relevant"]
            or not all(isinstance(doc, str) for doc in item["relevant"])
        ):
            raise ValueError(
                "Evaluation query #{} needs a non-empty \"query\" string and a "
                "non-empty \"relevant\" list of document paths.".format(number)
            )
        queries.append({"query": item["query"], "relevant": list(item["relevant"])})
    return queries


def evaluate(index: SearchIndex, queries: Sequence[Dict], k: int = DEFAULT_K) -> Dict:
    """Run every query and compute P@k per query, mean P@k and MRR."""
    rows = []
    for item in queries:
        ranked = index.ranked_ids(item["query"], limit=MAX_K)
        relevant = item["relevant"]
        rows.append({
            "query": item["query"],
            "top_k": [
                {"doc_id": doc_id, "relevant": doc_id in relevant} for doc_id in ranked[:k]
            ],
            "relevant": relevant,
            "precision": precision_at_k(ranked, relevant, k),
            "reciprocal_rank": reciprocal_rank(ranked, relevant),
        })
    return {
        "k": k,
        "rows": rows,
        "mean_precision": mean([row["precision"] for row in rows]),
        "mrr": mean_reciprocal_rank([row["reciprocal_rank"] for row in rows]),
    }
