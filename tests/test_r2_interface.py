"""R2: a simple web interface for searching, with no account needed."""
import pytest


@pytest.mark.parametrize("url", ["/", "/search?q=binary", "/search", "/evaluate"])
def test_r2_pages_load_without_login(client, url):
    response = client.get(url)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/html")


def test_r2_home_has_search_box_and_folder_form(client):
    html = client.get("/").get_data(as_text=True)
    assert 'name="q"' in html
    assert 'name="folder"' in html
    assert 'action="/search"' in html
    assert 'action="/index"' in html


def test_r2_no_password_or_login_fields(client, indexed_client):
    for url in ["/", "/search?q=sort", "/evaluate"]:
        html = indexed_client.get(url).get_data(as_text=True).lower()
        assert 'type="password"' not in html
        assert "log in" not in html and "sign up" not in html


def test_r2_every_page_links_to_evaluation(client):
    for url in ["/", "/search?q=x", "/evaluate"]:
        assert 'href="/evaluate"' in client.get(url).get_data(as_text=True)


def test_r2_search_box_keeps_the_query(indexed_client):
    html = indexed_client.get("/search?q=merge+sort").get_data(as_text=True)
    assert 'value="merge sort"' in html


def test_r2_folder_field_prefilled_with_sample_docs(client):
    from conftest import SAMPLE_DOCS

    assert 'value="{}"'.format(SAMPLE_DOCS) in client.get("/").get_data(as_text=True)
