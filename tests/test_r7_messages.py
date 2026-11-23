"""R7: clear messages for empty searches, empty folders and no matches."""
import os

from search_engine import (
    MSG_EMPTY_FOLDER_PATH,
    MSG_EMPTY_QUERY,
    MSG_NO_INDEX,
    MSG_NO_SEARCHABLE_TERMS,
    Document,
    SearchIndex,
    index_folder,
    run_search,
)


def small_index():
    return SearchIndex([Document("a.md", "binary search on sorted arrays")])


def test_r7_empty_query_message():
    assert run_search(small_index(), "") == ([], MSG_EMPTY_QUERY)
    assert run_search(small_index(), "   \t ") == ([], MSG_EMPTY_QUERY)


def test_r7_stopword_only_query_message():
    assert run_search(small_index(), "the of is ?!") == ([], MSG_NO_SEARCHABLE_TERMS)


def test_r7_search_before_indexing_message():
    assert run_search(None, "binary") == ([], MSG_NO_INDEX)


def test_r7_no_matches_message_includes_query():
    results, message = run_search(small_index(), "zebra")
    assert results == []
    assert message == 'No documents matched "zebra". Try different or fewer words.'


def test_r7_successful_search_has_no_message():
    results, message = run_search(small_index(), "binary")
    assert len(results) == 1 and message is None


def test_r7_empty_folder_path_message():
    assert index_folder("  ") == (None, MSG_EMPTY_FOLDER_PATH)


def test_r7_missing_folder_message(tmp_path):
    missing = str(tmp_path / "nope")
    assert index_folder(missing) == (None, "Folder not found: {}".format(missing))


def test_r7_file_instead_of_folder_message(make_folder):
    folder = make_folder({"a.txt": "x"})
    path = os.path.join(folder, "a.txt")
    assert index_folder(path) == (None, "Not a folder: {}".format(path))


def test_r7_folder_without_supported_files_message(make_folder):
    folder = make_folder({"image.png": b"\x89PNG", "data.csv": "a,b"})
    index, message = index_folder(folder)
    assert index is None
    assert message == (
        "No .txt or .md files were found in {}. "
        "Choose a folder that contains notes.".format(folder)
    )


def test_r7_empty_index_search_message():
    results, message = run_search(SearchIndex([], folder="/notes"), "x")
    assert results == []
    assert "No .txt or .md files were found in /notes" in message
