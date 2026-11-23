"""R4: show each result's file name and a short excerpt with the matching text."""
from search_engine import SNIPPET_CHARS, Document, SearchIndex, make_snippet

ELLIPSIS = "…"


def long_text_with(term, words_before=200, words_after=200):
    before = " ".join("before{}".format(i) for i in range(words_before))
    after = " ".join("after{}".format(i) for i in range(words_after))
    return "{} {} {}".format(before, term, after)


def test_r4_snippet_contains_term_deep_in_document():
    snippet = make_snippet(long_text_with("mitochondria"), ["mitochondria"])
    assert "mitochondria" in snippet


def test_r4_snippet_respects_length_limit():
    snippet = make_snippet(long_text_with("needle"), ["needle"])
    assert len(snippet) <= SNIPPET_CHARS + 2


def test_r4_ellipsis_marks_cut_ends_only():
    middle = make_snippet(long_text_with("needle"), ["needle"])
    assert middle.startswith(ELLIPSIS) and middle.endswith(ELLIPSIS)

    start = make_snippet(long_text_with("needle", words_before=0), ["needle"])
    assert not start.startswith(ELLIPSIS) and start.endswith(ELLIPSIS)

    end = make_snippet(long_text_with("needle", words_after=0), ["needle"])
    assert end.startswith(ELLIPSIS) and not end.endswith(ELLIPSIS)


def test_r4_short_document_snippet_is_full_text_with_collapsed_whitespace():
    assert make_snippet("Short   note\n\nabout cells.", ["cells"]) == "Short note about cells."


def test_r4_snippet_prefers_window_with_most_distinct_terms():
    text = long_text_with("merge") + " " + " ".join(["pad"] * 100) + " merge sort together " + " ".join(["tail"] * 100)
    snippet = make_snippet(text, ["merge", "sort"])
    assert "merge sort together" in snippet


def test_r4_snippet_without_match_is_start_of_document():
    text = long_text_with("x")
    snippet = make_snippet(text, ["absent"])
    assert snippet.startswith("before0")


def test_r4_snippet_does_not_cut_words_in_half():
    snippet = make_snippet(long_text_with("needle"), ["needle"])
    words = snippet.strip(ELLIPSIS).split(" ")
    assert all(w.startswith(("before", "after", "needle")) for w in words)
    assert all(w[len("before"):].isdigit() for w in words if w.startswith("before"))
    assert all(w[len("after"):].isdigit() for w in words if w.startswith("after"))


def test_r4_result_has_file_name_and_snippet():
    index = SearchIndex([Document("notes/cells.md", "The mitochondria make ATP.")])
    result = index.search("mitochondria")[0]
    assert result.name == "cells.md"
    assert result.doc_id == "notes/cells.md"
    assert "mitochondria" in result.snippet
