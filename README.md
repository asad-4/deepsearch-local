# DeepSearch Local

Search your own folder of `.txt` and `.md` notes from a browser without uploading
anything. DeepSearch Local indexes the folder in memory on your computer, ranks
matching files with the BM25 relevance algorithm, and shows each result's file name
with a short excerpt where your search terms are highlighted. A built-in evaluation
page measures ranking quality with Precision@k and Mean Reciprocal Rank (MRR) on a
small set of test queries.

- No account and no internet connection needed. No document content leaves your computer.
- The server listens only on this computer's loopback address (`localhost`).
- Requirements: see `problem.md`. Detailed behaviour: see `spec.md`.

## Setup

Requires Python 3.9 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Then open http://localhost:5000.

1. The folder box is pre-filled with the bundled `sample_docs/` folder. Change it to
   the path of your own notes (e.g. `~/Documents/notes`) if you like, then click
   **Index folder**. Subfolders are included. Hidden files are skipped.
2. Type a search and press **Search**.
3. Open **Evaluation** in the header to see Precision@k and MRR for the test
   queries in `evaluation_queries.json` (run against `sample_docs/`).

If port 5000 is taken, run `PORT=5001 python app.py` and open http://localhost:5001.

## Test

```bash
pytest
```

Each test name contains the requirement it checks (e.g. `test_r3_ranks_more_relevant_first`),
so `pytest -k r5` runs only the highlighting tests.

## Project layout

| Path | What it is |
|---|---|
| `app.py` | Flask routes and the `python app.py` entry point |
| `search_engine.py` | folder loading, tokenizing, BM25 index, snippets, highlighting, messages |
| `evaluation.py` | Precision@k, reciprocal rank, MRR |
| `templates/`, `static/` | HTML pages and local CSS (no CDN) |
| `sample_docs/` | example notes |
| `evaluation_queries.json` | test queries with their known relevant documents |
| `tests/` | pytest suite, one file per requirement plus route tests |
| `docs/decisions/` | architecture decision records |
