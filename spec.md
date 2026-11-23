# DeepSearch Local — Specification (Round 1)

This spec turns the initial requirements R1–R8 in `problem.md` into behaviour
that can be tested. Each section lists what the app does and the acceptance
criteria the tests in `tests/` check.

## Overview

DeepSearch Local is a small Flask web app that runs on the user's own computer.
The user picks a folder of `.txt` and `.md` notes. The app indexes them in memory
and ranks them for a query with BM25. Each result shows the file name and a
highlighted snippet. A separate page measures ranking quality on a fixed set of
test queries.

Components:

| Module | Responsibility |
|---|---|
| `search_engine.py` | loading documents, tokenizing, BM25 index, snippets, highlighting, user-facing messages |
| `evaluation.py` | Precision@k, reciprocal rank, MRR, loading the evaluation queries |
| `app.py` | Flask routes and startup (`python app.py`) |
| `templates/`, `static/` | HTML pages and local CSS |
| `sample_docs/` | sample notes for searching and for evaluation |
| `evaluation_queries.json` | the predefined R6 queries and their relevant documents |

## Text processing (shared by R1, R3, R4, R5)

- **Tokenizing:** lowercase the text and split it into runs of ASCII letters and
  digits (`[a-z0-9]+`). For example, `"Hash-Tables, O(1)!"` becomes
  `["hash", "tables", "o", "1"]`.
- **Query terms:** tokenize the query, drop a small fixed list of English
  stopwords (e.g. "the", "a", "is", "of"), and remove duplicates while keeping order.
  Documents are indexed with all their tokens. Stopwords are only removed from queries.

## R1 — Select a local folder and index it

- The home page has a text field for a folder path. It is pre-filled with the
  path of the bundled `sample_docs/` folder. Submitting the form indexes that folder.
- `~` is expanded. Relative paths are resolved against the directory the app was started from.
- Indexing includes files whose extension is `.txt` or `.md` (case-insensitive),
  including files in subfolders. Hidden files and folders (names starting with `.`) are skipped.
- Files are read as UTF-8. Undecodable bytes are replaced instead of raising an error.
  A file that cannot be read (for example, because of permissions) is skipped and counted as skipped.
- Each document is identified by its path relative to the selected folder, using
  `/` separators (for example, `biology/photosynthesis.md`).
- The index is held in memory only. Indexing a new folder replaces the previous index.
- After indexing succeeds, the page says how many documents were indexed, e.g.
  `Indexed 10 documents from /path/to/folder.`

Acceptance:
- Indexing a folder with `a.txt`, `b.md`, `sub/c.md` and `d.pdf` indexes exactly 3 documents.
- `.TXT` / `.MD` extensions are accepted.
- Hidden files and folders are not indexed.
- A file containing invalid UTF-8 is still indexed.
- Posting a folder path to the index route indexes it, and later searches use it.

## R2 — Web interface, no account

- `GET /` shows the folder form, a search box and the current index status.
- `GET /search?q=<query>` shows results on the same layout. The search box keeps the query.
- A link to the evaluation page (`/evaluate`) is visible on every page.
- There is no login, sign-up or session. Every page returns 200 without credentials.

Acceptance:
- `/`, `/search?q=x` and `/evaluate` return HTTP 200 with no redirect.
- The home page contains a search form (`name="q"`) and a folder form (`name="folder"`).
- No page contains a password field.

## R3 — Relevance ranking (BM25)

- Documents are scored with Okapi BM25, written in plain Python, with
  `k1 = 1.5` and `b = 0.75`, and
  `idf(t) = ln(1 + (N - df + 0.5) / (df + 0.5))`. This IDF is never negative.
- A document matches if it contains at least one query term (OR semantics).
  Documents with a score of 0 are not returned.
- Results are sorted by score, highest first. Equal scores are ordered by document path.
  At most 10 results are shown per search.

Acceptance:
- A document that mentions the query term more often ranks above one that mentions it
  once (with similar lengths).
- A document that matches a rare term ranks above one that matches only a common term.
- A document that matches more of the query terms ranks above one that matches fewer.
- Length normalisation: with equal term counts, a shorter document ranks above a longer one.
- Results are not simply alphabetical (a test where alphabetical order and relevance disagree).
- Every returned score is > 0 and the list is sorted in descending order.

## R4 — File name and excerpt

- Each result shows the document's file name, its relative path (if it is in a subfolder),
  and a snippet of at most about 200 characters taken from the document text.
- The snippet is the window that contains the most distinct query terms. If two windows
  tie, the earlier one is used. Whitespace is collapsed to single spaces. An ellipsis `…`
  is added at either end where the text was cut.
- If no query term occurs (which should not happen for a returned result), the
  snippet is the start of the document.

Acceptance:
- The snippet contains a query term that appears deep inside a long document.
- The snippet is no longer than the limit plus the two ellipses.
- An ellipsis appears only where text was actually cut. A short document gives its full text.
- The search page shows the file name and snippet of each result.

## R5 — Highlight matching terms

- In the snippet, every whole-word, case-insensitive occurrence of a query term is
  wrapped in `<mark>…</mark>`.
- Everything else in the snippet is HTML-escaped. Document text can never inject HTML
  (e.g. `<script>` in a note is shown as text), and a term like `amp` never matches
  inside an escape sequence such as `&amp;`.
- Partial words are not highlighted (query `cat` does not mark `category`).

Acceptance:
- `highlight("Hash tables are fast", ["hash"])` produces `<mark>Hash</mark> tables are fast`.
- Case is preserved inside the mark.
- `<script>` in a document is escaped.
- `amp`/`lt` terms do not corrupt escaped entities.
- The search results page contains `<mark>` for the query term.

## R6 — Search evaluation page

- `evaluation_queries.json` holds a list of `{"query": ..., "relevant": [doc ids]}`
  objects. The doc ids are relative paths in `sample_docs/`.
- `GET /evaluate` builds an index of `sample_docs/` (it does not depend on whatever
  folder the user indexed), runs each query and shows a table with columns query,
  top-k results, relevant documents, Precision@k and reciprocal rank. It also shows
  the mean Precision@k and the MRR.
- `k` defaults to 3 and can be set with `?k=N` (1–10). An invalid `k` falls back to 3,
  and the page says so.
- Definitions:
  - `Precision@k = (# relevant documents in top k) / k`. The denominator is always
    `k`, even if fewer than k results were returned.
  - `RR = 1 / rank of the first relevant result`, or 0 if none is retrieved.
  - `MRR = mean of RR over all queries`. It is 0 for an empty query set.

Acceptance:
- Hand-computed P@k and RR values match for known ranked lists (including no relevant results
  and fewer than k results).
- `k <= 0` raises `ValueError`.
- MRR of `[1, 0.5, 0]` is 0.5.
- Malformed evaluation files raise a clear `ValueError`.
- Every relevant doc id in `evaluation_queries.json` exists in `sample_docs/`.
- `/evaluate` shows each query, a P@k and an MRR value.

## R7 — Helpful messages instead of errors

| Situation | Message |
|---|---|
| Empty or whitespace-only query | `Please enter a search term.` |
| Query with only stopwords/punctuation | `Your search did not contain any searchable words. Try more specific terms.` |
| Search before any folder was indexed | `No folder has been indexed yet. Choose a folder above and click "Index folder".` |
| Empty folder path | `Please enter a folder path.` |
| Folder does not exist | `Folder not found: <path>` |
| Path is a file, not a folder | `Not a folder: <path>` |
| Folder has no `.txt`/`.md` files | `No .txt or .md files were found in <path>. Choose a folder that contains notes.` |
| Query matches nothing | `No documents matched "<query>". Try different or fewer words.` |

- None of these cases produces a 4xx/5xx response or a traceback. Each page returns 200 and shows the message.
- When indexing fails, the previous index (if any) is kept.

Acceptance: each row above has a logic test and a route test.

## R8 — Everything stays local

- The server only listens on `127.0.0.1` (port 5000), so other machines cannot reach it.
- The app makes no network requests. Documents and the index stay in process memory.
  Nothing is written to disk.
- Pages load no external resources: no CDN links, web fonts, analytics or external
  scripts. CSS is served from the app's own `static/` folder.
- Only Flask (and its dependencies) and pytest are used.

Acceptance:
- The configured host is `127.0.0.1`.
- With outbound socket connections blocked in the test, indexing, searching and evaluating
  all still work.
- No rendered page contains `http://` or `https://` in a `src` or `href` attribute.
- Indexing does not create any file in the indexed folder.

## Out of scope for round 1

- Persisting the index between restarts, watching folders for changes, file types other than
  `.txt`/`.md`, stemming, phrase queries, opening full documents from the results page.
