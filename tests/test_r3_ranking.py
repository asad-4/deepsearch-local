"""R3: rank matching documents by relevance with BM25."""
import math

from search_engine import Document, SearchIndex, query_terms


def build(docs):
    return SearchIndex([Document(doc_id, text) for doc_id, text in docs.items()])


def filler(n):
    return " ".join("filler{}".format(i) for i in range(n))


def test_r3_ranks_more_relevant_first():
    index = build({
        "a_once.txt": "python " + filler(20),
        "b_often.txt": "python python python " + filler(18),
    })
    assert index.ranked_ids("python") == ["b_often.txt", "a_once.txt"]


def test_r3_rare_term_outweighs_common_term():
    docs = {"doc{}.txt".format(i): "common " + filler(5) for i in range(5)}
    docs["rare.txt"] = "rare " + filler(5)
    index = build(docs)
    assert index.idf("rare") > index.idf("common")
    assert index.ranked_ids("common rare")[0] == "rare.txt"


def test_r3_matching_more_query_terms_ranks_higher():
    index = build({
        "a_one.txt": "merge " + filler(10),
        "b_both.txt": "merge sort " + filler(9),
        "c_none.txt": filler(11),
    })
    assert index.ranked_ids("merge sort") == ["b_both.txt", "a_one.txt"]


def test_r3_shorter_document_wins_with_equal_term_count():
    index = build({
        "a_long.txt": "cell " + filler(200),
        "b_short.txt": "cell " + filler(5),
    })
    assert index.ranked_ids("cell") == ["b_short.txt", "a_long.txt"]


def test_r3_order_is_by_relevance_not_alphabetical():
    index = build({
        "aaa.txt": "glucose " + filler(30),
        "zzz.txt": "glucose glucose glucose energy " + filler(5),
    })
    assert index.ranked_ids("glucose") == ["zzz.txt", "aaa.txt"]


def test_r3_scores_positive_and_descending():
    index = build({
        "a.txt": "sort sort array",
        "b.txt": "sort",
        "c.txt": "array of items",
        "d.txt": "unrelated words",
    })
    results = index.search("sort array")
    scores = [r.score for r in results]
    assert all(score > 0 for score in scores)
    assert scores == sorted(scores, reverse=True)
    assert "d.txt" not in [r.doc_id for r in results]


def test_r3_bm25_score_matches_formula():
    index = build({"a.txt": "x x y", "b.txt": "y z"})
    n, df, tf, dl, avgdl = 2, 1, 2, 3, 2.5
    idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
    expected = idf * tf * (1.5 + 1) / (tf + 1.5 * (1 - 0.75 + 0.75 * dl / avgdl))
    assert math.isclose(index.search("x")[0].score, expected)


def test_r3_idf_never_negative_for_term_in_every_document():
    index = build({"a.txt": "the cat", "b.txt": "the dog"})
    assert index.idf("cat") > 0
    assert index.idf("dog") > 0
    assert build({"a.txt": "word", "b.txt": "word"}).idf("word") > 0


def test_r3_ties_broken_by_document_path():
    index = build({"b.txt": "same words", "a.txt": "same words"})
    assert index.ranked_ids("same") == ["a.txt", "b.txt"]


def test_r3_results_limited_to_ten():
    index = build({"d{:02}.txt".format(i): "topic" for i in range(15)})
    assert len(index.search("topic")) == 10


def test_r3_query_terms_drop_stopwords_and_duplicates():
    assert query_terms("What is the Hash table, hash?") == ["hash", "table"]


def test_r3_sample_docs_rank_expected_document_first():
    from conftest import SAMPLE_DOCS

    index = SearchIndex.from_folder(SAMPLE_DOCS)
    assert index.ranked_ids("hash table collisions")[0] == "hash_tables.md"
    assert index.ranked_ids("chlorophyll")[0] == "biology/photosynthesis.md"
