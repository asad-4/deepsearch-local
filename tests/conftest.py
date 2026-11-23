import os

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_DOCS = os.path.join(REPO_ROOT, "sample_docs")


@pytest.fixture
def make_folder(tmp_path):
    """Create a folder of files from {relative_path: text or bytes}; return its path."""

    def _make(files):
        for relative, content in files.items():
            path = tmp_path / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                path.write_bytes(content)
            else:
                path.write_text(content, encoding="utf-8")
        return str(tmp_path)

    return _make
