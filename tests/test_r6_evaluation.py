"""R6: evaluation metrics (Precision@k, MRR) on predefined queries."""
import json
import math
import os

import pytest

from conftest import REPO_ROOT, SAMPLE_DOCS
from evaluation import (
    evaluate,
    load_queries,
    mean_reciprocal_rank,
    precision_at_k,
    reciprocal_rank,
)
from search_engine import Document, SearchIndex, load_documents

QUERIES_FILE = os.path.join(REPO_ROOT, "evaluation_queries.json")


def test_r6_precision_at_k_counts_relevant_in_top_k():
    assert precision_at_k(["a", "b", "c", "d"], ["a", "c", "z"], 3) == pytest.approx(2 / 3)


def test_r6_precision_at_k_ignores_relevant_beyond_k():
    assert precision_at_k(["x", "y", "a"], ["a"], 2) == 0.0


def test_r6_precision_at_k_denominator_is_k_when_fewer_results():
    assert precision_at_k(["a"], ["a"], 3) == pytest.approx(1 / 3)


def test_r6_precision_at_k_with_no_results():
    assert precision_at_k([], ["a"], 3) == 0.0


def test_r6_precision_at_k_rejects_non_positive_k():
    with pytest.raises(ValueError):
        precision_at_k(["a"], ["a"], 0)


def test_r6_reciprocal_rank_of_first_relevant():
    assert reciprocal_rank(["a", "b", "c"], ["a"]) == 1.0
    assert reciprocal_rank(["x", "b", "c"], ["c", "b"]) == 0.5
    assert reciprocal_rank(["x", "y"], ["a"]) == 0.0


def test_r6_mean_reciprocal_rank():
    assert mean_reciprocal_rank([1.0, 0.5, 0.0]) == 0.5
    assert mean_reciprocal_rank([]) == 0.0


def test_r6_evaluate_computes_per_query_and_means():
    index = SearchIndex([
        Document("cats.md", "cats cats cats"),
        Document("dogs.md", "dogs dogs"),
        Document("pets.md", "cats and dogs are pets"),
    ])
    queries = [
        {"query": "cats", "relevant": ["cats.md"]},  # cats.md first -> RR 1
        {"query": "dogs", "relevant": ["pets.md"]},  # pets.md second -> RR 0.5
        {"query": "fish", "relevant": ["cats.md"]},  # nothing -> RR 0
    ]
    report = evaluate(index, queries, k=2)
    assert [row["reciprocal_rank"] for row in report["rows"]] == [1.0, 0.5, 0.0]
    assert [row["precision"] for row in report["rows"]] == [0.5, 0.5, 0.0]
    assert report["mrr"] == pytest.approx(0.5)
    assert report["mean_precision"] == pytest.approx(1 / 3)
    assert report["rows"][1]["top_k"] == [
        {"doc_id": "dogs.md", "relevant": False},
        {"doc_id": "pets.md", "relevant": True},
    ]


def test_r6_load_queries_reads_predefined_file():
    queries = load_queries(QUERIES_FILE)
    assert len(queries) >= 5
    assert all(q["query"] and q["relevant"] for q in queries)


def test_r6_every_relevant_doc_exists_in_sample_docs():
    documents, _ = load_documents(SAMPLE_DOCS)
    ids = {d.doc_id for d in documents}
    for query in load_queries(QUERIES_FILE):
        for doc_id in query["relevant"]:
            assert doc_id in ids, "{} missing for query {!r}".format(doc_id, query["query"])


@pytest.mark.parametrize("content", [
    "not json",
    json.dumps({"query": "x"}),
    json.dumps([{"query": "x"}]),
    json.dumps([{"query": "", "relevant": ["a.md"]}]),
    json.dumps([{"query": "x", "relevant": []}]),
    json.dumps([{"query": "x", "relevant": [1]}]),
])
def test_r6_malformed_query_file_raises_value_error(tmp_path, content):
    path = tmp_path / "queries.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        load_queries(str(path))


def test_r6_sample_evaluation_metrics_are_in_range():
    report = evaluate(SearchIndex.from_folder(SAMPLE_DOCS), load_queries(QUERIES_FILE), k=3)
    assert 0.0 <= report["mean_precision"] <= 1.0
    assert 0.0 < report["mrr"] <= 1.0
    assert not math.isnan(report["mrr"])
