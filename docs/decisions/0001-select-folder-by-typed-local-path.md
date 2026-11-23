# 0001 — Select the folder to index by typing its local path

- Status: accepted
- Date: 2026-11-22
- Requirements: R1 (select a local folder), R2 (simple web UI), R8 (stay local)

## Context

R1 asks users to "select a local folder" in a web interface. Browsers do not
give a web page the real path of a folder on disk. Python's server, though, runs
on the same computer and can read the folder directly. There are three realistic
ways to let the user choose the folder:

1. **Typed path:** a text field where the user types or pastes a path
   (pre-filled with `sample_docs/`). The Flask server reads the files from disk.
2. **Browser directory upload:** `<input type="file" webkitdirectory>`. The browser
   reads every file in the chosen folder and POSTs the contents to the local server.
3. **Native folder dialog:** the server opens an OS dialog (e.g. `tkinter.filedialog`)
   when the user clicks a button.

## Decision (Y-statement)

In the context of **letting a user pick which folder of notes to index from a
browser page served by a local Flask app**, facing **the fact that browsers hide
real file-system paths and that all files must stay on the user's computer (R8)**,
we decided for **a text field where the user types the folder path, which the
server reads directly from disk**, and neglected **browser directory upload
(`webkitdirectory`) and a native OS folder dialog (tkinter)**, to achieve **a
simple, testable implementation that never copies file contents through HTTP,
works the same on every OS and browser, and can re-index a folder without
re-uploading it**, accepting **that users must know or paste the folder path
(there is no graphical picker) and that the server can read any folder the
local user can read**.

## Consequences

- Good: indexing is just `os.walk` + `open`. It is easy to test with `tmp_path`
  and Flask's test client (`POST /index`).
- Good: no document bytes travel over HTTP, not even to localhost. Large folders do
  not hit request-size limits.
- Good: the result shows real relative paths (`biology/photosynthesis.md`), which
  the upload approach could only approximate.
- Bad: less friendly than a picker for users who don't know paths. This is mitigated
  by `~` expansion, the pre-filled example path, and clear R7 messages for missing
  folders or folders with no notes.
- Risk: anyone who can reach the server could ask it to read any folder the user can
  read. This is acceptable because the server binds only to loopback addresses (R8),
  so only the user's own computer can reach it.

## Alternatives considered

- **`webkitdirectory` upload:** a real picker UI, but it sends every file's contents
  in a request (still local, but against the spirit of R8 and slow for large
  folders). It is a non-standard attribute, and re-indexing means picking the
  folder again.
- **tkinter dialog:** a native picker, but it opens a window from the server
  process. It fails on headless setups and with some macOS Python builds (Tk
  issues), and it can't be tested with Flask's test client. `tkinter` is in the
  standard library, but whether it works depends on how Python was installed.
