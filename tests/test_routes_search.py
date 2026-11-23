"""Routes for R1 (indexing), R3 (ranking), R4 (name + excerpt), R5 (highlighting)."""
import re

from conftest import SAMPLE_DOCS


def result_names(html):
    return re.findall(r'<span class="name">([^<]+)</span>', html)


def test_r1_index_route_indexes_chosen_folder(client, make_folder):
    folder = make_folder({"one.md": "quantum physics notes", "two.txt": "cooking recipes"})
    html = client.post("/index", data={"folder": folder}).get_data(as_text=True)
    assert "Indexed 2 documents from" in html
    assert result_names(client.get("/search?q=quantum").get_data(as_text=True)) == ["one.md"]


def test_r1_indexing_new_folder_replaces_old_index(indexed_client, make_folder):
    folder = make_folder({"only.md": "volcano"})
    indexed_client.post("/index", data={"folder": folder})
    html = indexed_client.get("/search?q=binary").get_data(as_text=True)
    assert result_names(html) == []


def test_r1_status_shows_indexed_folder(indexed_client):
    html = indexed_client.get("/").get_data(as_text=True)
    assert "Searching 11 documents in" in html
    assert SAMPLE_DOCS in html


def test_r3_search_page_lists_most_relevant_first(indexed_client):
    html = indexed_client.get("/search?q=hash+table+collisions").get_data(as_text=True)
    assert result_names(html)[0] == "hash_tables.md"


def test_r4_search_page_shows_file_name_path_and_snippet(indexed_client):
    html = indexed_client.get("/search?q=chlorophyll").get_data(as_text=True)
    assert result_names(html) == ["photosynthesis.md"]
    assert "biology/photosynthesis.md" in html
    assert re.search(r'<p class="snippet">[^<]*<mark>Chlorophyll</mark>', html)


def test_r5_search_page_highlights_terms_with_mark(indexed_client):
    html = indexed_client.get("/search?q=mitochondria").get_data(as_text=True)
    assert "<mark>mitochondria</mark>" in html.lower()


def test_r5_document_html_is_escaped_on_page(client, make_folder):
    folder = make_folder({"x.md": "<script>alert('x')</script> danger"})
    client.post("/index", data={"folder": folder})
    html = client.get("/search?q=danger").get_data(as_text=True)
    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html
