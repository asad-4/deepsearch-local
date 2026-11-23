"""R6: the evaluation page."""
import os
import re

import pytest

from app import create_app
from conftest import REPO_ROOT, SAMPLE_DOCS
from evaluation import evaluate, load_queries
from search_engine import SearchIndex


def test_r6_evaluation_page_shows_queries_and_metrics(client):
    html = client.get("/evaluate").get_data(as_text=True)
    for query in load_queries(os.path.join(REPO_ROOT, "evaluation_queries.json")):
        assert query["query"] in html
    assert "Mean Precision@3" in html
    assert "MRR" in html


def test_r6_page_values_match_computed_metrics(client):
    report = evaluate(
        SearchIndex.from_folder(SAMPLE_DOCS),
        load_queries(os.path.join(REPO_ROOT, "evaluation_queries.json")),
        k=3,
    )
    html = client.get("/evaluate").get_data(as_text=True)
    assert re.search(r'id="mrr">{:.3f}<'.format(report["mrr"]), html)
    assert re.search(r'id="mean-precision">{:.3f}<'.format(report["mean_precision"]), html)


def test_r6_k_parameter_changes_cutoff(client):
    html = client.get("/evaluate?k=5").get_data(as_text=True)
    assert "Mean Precision@5" in html


@pytest.mark.parametrize("bad_k", ["0", "abc", "11", "-2"])
def test_r6_invalid_k_falls_back_with_notice(client, bad_k):
    response = client.get("/evaluate?k=" + bad_k)
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Mean Precision@3" in html
    assert "k must be a whole number from 1 to 10" in html


def test_r6_evaluation_independent_of_user_folder(client, make_folder):
    folder = make_folder({"other.md": "nothing relevant"})
    client.post("/index", data={"folder": folder})
    assert "hash_tables.md" in client.get("/evaluate").get_data(as_text=True)


def test_r6_broken_query_file_shows_message(tmp_path):
    bad = tmp_path / "queries.json"
    bad.write_text("{oops", encoding="utf-8")
    client = create_app(eval_queries=str(bad)).test_client()
    response = client.get("/evaluate")
    assert response.status_code == 200
    assert "Could not load the evaluation queries" in response.get_data(as_text=True)
