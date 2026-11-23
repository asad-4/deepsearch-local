"""R5: highlight matching terms in result snippets."""
from markupsafe import Markup

from search_engine import Document, SearchIndex, highlight


def test_r5_wraps_term_in_mark():
    assert highlight("Hash tables are fast", ["hash"]) == "<mark>Hash</mark> tables are fast"


def test_r5_highlight_is_case_insensitive_and_preserves_case():
    assert highlight("DNA and dna", ["dna"]) == "<mark>DNA</mark> and <mark>dna</mark>"


def test_r5_highlights_every_query_term():
    html = highlight("merge sort uses merge", ["merge", "sort"])
    assert html == "<mark>merge</mark> <mark>sort</mark> uses <mark>merge</mark>"


def test_r5_does_not_highlight_partial_words():
    assert highlight("category of cat", ["cat"]) == "category of <mark>cat</mark>"


def test_r5_escapes_html_in_document_text():
    html = highlight("<script>alert(1)</script> cells", ["cells"])
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "<mark>cells</mark>" in html


def test_r5_entity_names_as_terms_do_not_break_escaping():
    html = highlight("salt & pepper < amp", ["amp", "lt"])
    assert html == "salt &amp; pepper &lt; <mark>amp</mark>"


def test_r5_returns_markup_safe_for_templates():
    assert isinstance(highlight("text", ["text"]), Markup)


def test_r5_search_result_snippet_html_is_highlighted():
    index = SearchIndex([Document("a.md", "Chlorophyll absorbs light.")])
    result = index.search("chlorophyll")[0]
    assert "<mark>Chlorophyll</mark>" in result.snippet_html
