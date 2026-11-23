"""Local document indexing and BM25 search (R1, R3, R4, R5, R7).

Everything here is plain Python: no network access, nothing written to disk (R8).
"""

import math
import os
import re
from collections import Counter
from typing import Dict, List, Optional, Sequence, Tuple

from markupsafe import Markup, escape

SUPPORTED_EXTENSIONS = (".txt", ".md")
MAX_RESULTS = 10
SNIPPET_CHARS = 200

# BM25 parameters (spec.md, R3)
K1 = 1.5
B = 0.75

STOPWORDS = frozenset(
    """a an and are as at be but by for from how i in into is it its of on or
    that the this to was what when where which who why will with""".split()
)

# R7 messages
MSG_EMPTY_QUERY = "Please enter a search term."
MSG_NO_SEARCHABLE_TERMS = (
    "Your search did not contain any searchable words. Try more specific terms."
)
MSG_NO_INDEX = (
    'No folder has been indexed yet. Choose a folder above and click "Index folder".'
)
MSG_EMPTY_FOLDER_PATH = "Please enter a folder path."
MSG_FOLDER_NOT_FOUND = "Folder not found: {path}"
MSG_NOT_A_FOLDER = "Not a folder: {path}"
MSG_NO_SUPPORTED_FILES = (
    "No .txt or .md files were found in {path}. Choose a folder that contains notes."
)
MSG_NO_MATCHES = 'No documents matched "{query}". Try different or fewer words.'
MSG_INDEXED = "Indexed {count} document{plural} from {path}."
MSG_SKIPPED = " {count} file{plural} could not be read and {verb} skipped."

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_WORD_RE = re.compile(r"[A-Za-z0-9]+")


class FolderError(Exception):
    """Raised when a folder cannot be indexed; the message is shown to the user."""


def tokenize(text: str) -> List[str]:
    """Lowercase text and split it into runs of ASCII letters and digits."""
    return _TOKEN_RE.findall(text.lower())


def query_terms(query: str) -> List[str]:
    """Tokenize a query, drop stopwords and duplicates, keep order."""
    terms = []  # type: List[str]
    for token in tokenize(query):
        if token not in STOPWORDS and token not in terms:
            terms.append(token)
    return terms


class Document:
    def __init__(self, doc_id: str, text: str):
        self.doc_id = doc_id  # path relative to the indexed folder, "/" separated
        self.name = doc_id.rsplit("/", 1)[-1]
        self.text = text

    def __repr__(self) -> str:
        return "Document({!r})".format(self.doc_id)


class SearchResult:
    def __init__(self, document: Document, score: float, snippet: str, terms: List[str]):
        self.document = document
        self.score = score
        self.snippet = snippet
        self.snippet_html = highlight(snippet, terms)

    @property
    def doc_id(self) -> str:
        return self.document.doc_id

    @property
    def name(self) -> str:
        return self.document.name


def _is_hidden(name: str) -> bool:
    return name.startswith(".")


def load_documents(folder: str) -> Tuple[List[Document], int]:
    """Read every .txt/.md file under folder (recursively, skipping hidden entries).

    Returns (documents, number_of_unreadable_files). Raises FolderError if the
    path does not exist or is not a directory.
    """
    if not os.path.exists(folder):
        raise FolderError(MSG_FOLDER_NOT_FOUND.format(path=folder))
    if not os.path.isdir(folder):
        raise FolderError(MSG_NOT_A_FOLDER.format(path=folder))

    documents = []  # type: List[Document]
    skipped = 0
    for root, dirs, files in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if not _is_hidden(d))
        for filename in sorted(files):
            if _is_hidden(filename):
                continue
            if not filename.lower().endswith(SUPPORTED_EXTENSIONS):
                continue
            full_path = os.path.join(root, filename)
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as handle:
                    text = handle.read()
            except OSError:
                skipped += 1
                continue
            doc_id = os.path.relpath(full_path, folder).replace(os.sep, "/")
            documents.append(Document(doc_id, text))
    return documents, skipped


class SearchIndex:
    """In-memory inverted index scored with Okapi BM25."""

    def __init__(self, documents: Sequence[Document], folder: Optional[str] = None):
        self.folder = folder
        self.documents = list(documents)
        self.postings = {}  # type: Dict[str, Dict[int, int]]
        self.doc_lengths = []  # type: List[int]
        for index, document in enumerate(self.documents):
            counts = Counter(tokenize(document.text))
            self.doc_lengths.append(sum(counts.values()))
            for term, count in counts.items():
                self.postings.setdefault(term, {})[index] = count
        total = sum(self.doc_lengths)
        self.avg_length = total / len(self.documents) if self.documents else 0.0

    @classmethod
    def from_folder(cls, folder: str) -> "SearchIndex":
        documents, _ = load_documents(folder)
        return cls(documents, folder=folder)

    def __len__(self) -> int:
        return len(self.documents)

    def idf(self, term: str) -> float:
        n = len(self.documents)
        df = len(self.postings.get(term, {}))
        return math.log(1.0 + (n - df + 0.5) / (df + 0.5))

    def scores(self, terms: Sequence[str]) -> Dict[int, float]:
        """BM25 score for every document containing at least one term."""
        scores = {}  # type: Dict[int, float]
        for term in terms:
            postings = self.postings.get(term)
            if not postings:
                continue
            idf = self.idf(term)
            for doc_index, tf in postings.items():
                length = self.doc_lengths[doc_index]
                norm = 1 - B + B * (length / self.avg_length if self.avg_length else 0)
                gain = idf * tf * (K1 + 1) / (tf + K1 * norm)
                scores[doc_index] = scores.get(doc_index, 0.0) + gain
        return scores

    def search(self, query: str, limit: int = MAX_RESULTS) -> List[SearchResult]:
        terms = query_terms(query)
        scored = [(s, i) for i, s in self.scores(terms).items() if s > 0]
        scored.sort(key=lambda pair: (-pair[0], self.documents[pair[1]].doc_id))
        results = []
        for score, doc_index in scored[:limit]:
            document = self.documents[doc_index]
            snippet = make_snippet(document.text, terms)
            results.append(SearchResult(document, score, snippet, terms))
        return results

    def ranked_ids(self, query: str, limit: int = MAX_RESULTS) -> List[str]:
        return [result.doc_id for result in self.search(query, limit)]


def make_snippet(text: str, terms: Sequence[str], max_chars: int = SNIPPET_CHARS) -> str:
    """Return the window of text (about max_chars long) with the most distinct terms.

    Whitespace is collapsed. An ellipsis marks each end where text was cut.
    """
    flat = " ".join(text.split())
    if len(flat) <= max_chars:
        return flat

    term_set = set(terms)
    hits = [
        (m.start(), m.group(0).lower())
        for m in _WORD_RE.finditer(flat)
        if m.group(0).lower() in term_set
    ]

    # Sliding window over the hits: both window edges only move forward.
    best_start = 0
    best_count = 0
    lead = max_chars // 5  # show a little context before the first hit
    window = Counter()  # type: Counter
    left = right = 0
    for position, _ in hits:
        start = max(0, position - lead)
        end = start + max_chars
        while right < len(hits) and hits[right][0] < end:
            window[hits[right][1]] += 1
            right += 1
        while hits[left][0] < start:
            window[hits[left][1]] -= 1
            if not window[hits[left][1]]:
                del window[hits[left][1]]
            left += 1
        if len(window) > best_count:
            best_count = len(window)
            best_start = start

    start = min(best_start, len(flat) - max_chars)
    end = start + max_chars
    # Avoid cutting words in half at either edge.
    if start > 0:
        space = flat.find(" ", start)
        if space != -1 and space < start + 20:
            start = space + 1
    if end < len(flat):
        space = flat.rfind(" ", start, end)
        if space > end - 20:
            end = space

    snippet = flat[start:end].strip()
    if start > 0:
        snippet = "…" + snippet
    if end < len(flat):
        snippet = snippet + "…"
    return snippet


def highlight(text: str, terms: Sequence[str]) -> Markup:
    """HTML-escape text and wrap whole-word, case-insensitive term matches in <mark>."""
    term_set = {term.lower() for term in terms}
    parts = []
    last = 0
    for match in _WORD_RE.finditer(text):
        word = match.group(0)
        if word.lower() not in term_set:
            continue
        parts.append(str(escape(text[last:match.start()])))
        parts.append("<mark>{}</mark>".format(escape(word)))
        last = match.end()
    parts.append(str(escape(text[last:])))
    return Markup("".join(parts))


def index_folder(folder: str) -> Tuple[Optional[SearchIndex], str]:
    """Index a user-chosen folder (R1). Returns (index or None, message for the user)."""
    folder = (folder or "").strip()
    if not folder:
        return None, MSG_EMPTY_FOLDER_PATH
    path = os.path.abspath(os.path.expanduser(folder))
    try:
        documents, skipped = load_documents(path)
    except FolderError as error:
        return None, str(error)
    if not documents:
        return None, MSG_NO_SUPPORTED_FILES.format(path=path)
    message = MSG_INDEXED.format(
        count=len(documents), plural="" if len(documents) == 1 else "s", path=path
    )
    if skipped:
        message += MSG_SKIPPED.format(
            count=skipped,
            plural="" if skipped == 1 else "s",
            verb="was" if skipped == 1 else "were",
        )
    return SearchIndex(documents, folder=path), message


def run_search(index: Optional[SearchIndex], query: str) -> Tuple[List[SearchResult], Optional[str]]:
    """Search with user-facing messages for every non-happy path (R7).

    Returns (results, message). message is None when there are results.
    """
    query = (query or "").strip()
    if not query:
        return [], MSG_EMPTY_QUERY
    if index is None:
        return [], MSG_NO_INDEX
    if len(index) == 0:
        return [], MSG_NO_SUPPORTED_FILES.format(path=index.folder or "this folder")
    if not query_terms(query):
        return [], MSG_NO_SEARCHABLE_TERMS
    results = index.search(query)
    if not results:
        return [], MSG_NO_MATCHES.format(query=query)
    return results, None
