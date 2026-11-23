# CLAUDE.md — standing rules for this project

DeepSearch Local: a local-only Flask app that indexes a folder of `.txt`/`.md`
notes and ranks them with BM25. Requirements are in `problem.md`. Testable
behaviour is in `spec.md`.

## Rules

- **Python 3.9 compatible.** No `match` statements. No `X | Y` type hints (use
  `Optional[...]` / `Union[...]` from `typing`). No other 3.10+ features.
- **Dependencies: Flask and pytest only.** Ranking (BM25), tokenizing, snippets and
  metrics are written in plain Python. Do not add other packages.
- **Privacy (R8).** Never send document contents to any external service. No CDN
  links, web fonts, analytics or external scripts in pages. All CSS/JS is served
  locally from `static/`. The server binds to `127.0.0.1` only.
- **Test naming.** Every test names the requirement ID it checks, e.g.
  `test_r3_ranks_more_relevant_first`.
- **Run `pytest` before every commit. Never commit failing tests.**
- **Never edit `problem.md`. Never amend or undo a commit** (no `--amend`, `reset`,
  `revert`, or force-push). Fix mistakes with a new commit.
- **Never track** `.venv/`, `__pycache__/`, `*.jsonl` or `*.db` files (see `.gitignore`).

## Commands

- Setup: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Run: `python app.py`, then open http://localhost:5000
- Test: `pytest`
