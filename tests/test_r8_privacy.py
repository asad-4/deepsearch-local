"""R8: documents and index stay on the user's computer."""
import os
import re
import socket

import pytest

import app as app_module
from conftest import REPO_ROOT, SAMPLE_DOCS

PAGES = ["/", "/search?q=sort", "/search?q=", "/evaluate"]


def test_r8_server_listens_on_loopback_only():
    assert app_module.HOST == "127.0.0.1"
    assert set(app_module.HOSTS) <= {"127.0.0.1", "::1"}


def test_r8_servers_bind_only_loopback_addresses(app):
    servers = app_module.make_servers(app, 0)  # port 0: any free port
    try:
        for server in servers:
            assert server.server_address[0] in ("127.0.0.1", "::1")
    finally:
        for server in servers:
            server.server_close()


@pytest.fixture
def no_network(monkeypatch):
    """Fail the test if anything tries to open an outbound connection."""

    def refuse(*args, **kwargs):
        raise AssertionError("network access attempted: {} {}".format(args, kwargs))

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket.socket, "connect_ex", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)


def test_r8_index_search_and_evaluate_work_without_network(no_network, client):
    assert client.post("/index", data={"folder": SAMPLE_DOCS}).status_code == 200
    assert "binary_search.txt" in client.get("/search?q=binary").get_data(as_text=True)
    assert client.get("/evaluate").status_code == 200


def test_r8_pages_load_no_external_resources(indexed_client):
    for url in PAGES:
        html = indexed_client.get(url).get_data(as_text=True)
        external = re.findall(r'(?:src|href)\s*=\s*["\']?\s*(?:https?:)?//', html, re.I)
        assert external == [], "external resource on {}".format(url)


def test_r8_templates_and_static_files_have_no_external_urls():
    for folder in ("templates", "static"):
        for name in os.listdir(os.path.join(REPO_ROOT, folder)):
            with open(os.path.join(REPO_ROOT, folder, name), encoding="utf-8") as handle:
                text = handle.read()
            assert "http://" not in text and "https://" not in text, name
            assert "@import" not in text, name


def test_r8_indexing_writes_nothing_to_the_folder(client, make_folder):
    folder = make_folder({"a.md": "alpha", "sub/b.txt": "beta"})

    def snapshot():
        return sorted(
            (os.path.relpath(os.path.join(root, f), folder), os.path.getmtime(os.path.join(root, f)))
            for root, _, files in os.walk(folder)
            for f in files
        )

    before = snapshot()
    client.post("/index", data={"folder": folder})
    client.get("/search?q=alpha")
    assert snapshot() == before


def test_r8_requirements_are_only_flask_and_pytest():
    with open(os.path.join(REPO_ROOT, "requirements.txt"), encoding="utf-8") as handle:
        names = [
            re.split(r"[<>=!~\[ ]", line.strip(), maxsplit=1)[0].lower()
            for line in handle
            if line.strip() and not line.startswith("#")
        ]
    assert sorted(names) == ["flask", "pytest"]
