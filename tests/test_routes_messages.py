"""R7: routes show helpful messages instead of errors."""
from markupsafe import escape

import pytest


def page(response):
    assert response.status_code == 200
    return response.get_data(as_text=True)


@pytest.mark.parametrize("url", ["/search?q=", "/search?q=+++", "/search"])
def test_r7_empty_search_shows_message(indexed_client, url):
    assert "Please enter a search term." in page(indexed_client.get(url))


def test_r7_stopword_search_shows_message(indexed_client):
    assert "did not contain any searchable words" in page(indexed_client.get("/search?q=the+of"))


def test_r7_search_before_indexing_shows_message(client):
    html = page(client.get("/search?q=binary"))
    assert escape('No folder has been indexed yet. Choose a folder above and click "Index folder".') in html


def test_r7_no_matches_shows_message(indexed_client):
    html = page(indexed_client.get("/search?q=xylophone"))
    assert escape('No documents matched "xylophone". Try different or fewer words.') in html


def test_r7_empty_folder_path_shows_message(client):
    assert "Please enter a folder path." in page(client.post("/index", data={"folder": ""}))


def test_r7_missing_folder_shows_message(client, tmp_path):
    missing = str(tmp_path / "missing")
    assert "Folder not found: " + missing in page(client.post("/index", data={"folder": missing}))


def test_r7_folder_without_notes_shows_message(client, make_folder):
    folder = make_folder({"pic.jpg": b"\xff\xd8"})
    html = page(client.post("/index", data={"folder": folder}))
    assert "No .txt or .md files were found in " + folder in html


def test_r7_failed_index_keeps_previous_index(indexed_client, tmp_path):
    indexed_client.post("/index", data={"folder": str(tmp_path / "missing")})
    html = page(indexed_client.get("/search?q=binary+search"))
    assert "binary_search.txt" in html
