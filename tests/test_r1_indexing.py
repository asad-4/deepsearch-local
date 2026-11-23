"""R1: select a local folder of .txt/.md files and index it."""
import os

import pytest

from search_engine import FolderError, SearchIndex, index_folder, load_documents, tokenize


def test_r1_indexes_only_txt_and_md_files_including_subfolders(make_folder):
    folder = make_folder({
        "a.txt": "alpha",
        "b.md": "beta",
        "sub/c.md": "gamma",
        "d.pdf": "not supported",
        "e.py": "print('no')",
    })
    documents, skipped = load_documents(folder)
    assert sorted(d.doc_id for d in documents) == ["a.txt", "b.md", "sub/c.md"]
    assert skipped == 0


def test_r1_extensions_are_case_insensitive(make_folder):
    folder = make_folder({"UPPER.TXT": "one", "Notes.MD": "two"})
    documents, _ = load_documents(folder)
    assert sorted(d.doc_id for d in documents) == ["Notes.MD", "UPPER.TXT"]


def test_r1_skips_hidden_files_and_folders(make_folder):
    folder = make_folder({
        "visible.md": "yes",
        ".hidden.md": "no",
        ".git/config.txt": "no",
    })
    documents, _ = load_documents(folder)
    assert [d.doc_id for d in documents] == ["visible.md"]


def test_r1_invalid_utf8_is_still_indexed(make_folder):
    folder = make_folder({"latin.txt": b"caf\xe9 culture"})
    documents, _ = load_documents(folder)
    assert len(documents) == 1
    assert "culture" in documents[0].text


def test_r1_document_name_is_file_name_and_id_is_relative_path(make_folder):
    folder = make_folder({"biology/cells.md": "mitochondria"})
    documents, _ = load_documents(folder)
    assert documents[0].doc_id == "biology/cells.md"
    assert documents[0].name == "cells.md"


def test_r1_missing_folder_raises_folder_error(tmp_path):
    with pytest.raises(FolderError):
        load_documents(str(tmp_path / "does-not-exist"))


def test_r1_index_folder_reports_document_count(make_folder):
    folder = make_folder({"a.txt": "alpha", "b.md": "beta"})
    index, message = index_folder(folder)
    assert isinstance(index, SearchIndex)
    assert len(index) == 2
    assert message == "Indexed 2 documents from {}.".format(os.path.abspath(folder))


def test_r1_index_folder_expands_home_directory(monkeypatch, make_folder):
    folder = make_folder({"notes.md": "hello"})
    monkeypatch.setenv("HOME", folder)
    index, _ = index_folder("~")
    assert index is not None and len(index) == 1


def test_r1_indexed_terms_are_searchable(make_folder):
    folder = make_folder({"a.txt": "Photosynthesis happens in leaves", "b.txt": "Rivers flow"})
    index = SearchIndex.from_folder(folder)
    assert index.ranked_ids("photosynthesis") == ["a.txt"]


def test_r1_tokenize_lowercases_and_splits_on_non_alphanumerics():
    assert tokenize("Hash-Tables, O(1)!") == ["hash", "tables", "o", "1"]


def test_r1_sample_docs_folder_indexes():
    from conftest import SAMPLE_DOCS

    index, _ = index_folder(SAMPLE_DOCS)
    assert index is not None and len(index) >= 10


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root can read anything")
def test_r1_unreadable_file_is_skipped_and_reported(make_folder):
    folder = make_folder({"ok.md": "fine", "locked.md": "secret"})
    locked = os.path.join(folder, "locked.md")
    os.chmod(locked, 0)
    try:
        index, message = index_folder(folder)
    finally:
        os.chmod(locked, 0o644)
    assert [d.doc_id for d in index.documents] == ["ok.md"]
    assert message.endswith("1 file could not be read and was skipped.")
