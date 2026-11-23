"""DeepSearch Local web app. Run with: python app.py, then open http://localhost:5000"""

import errno
import os
import socket
import sys
import threading
from typing import List, Optional

from flask import Flask, render_template, request
from werkzeug.serving import BaseWSGIServer, make_server

from evaluation import DEFAULT_K, MAX_K, evaluate, load_queries
from search_engine import SearchIndex, index_folder, run_search

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DOCS = os.path.join(BASE_DIR, "sample_docs")
EVALUATION_QUERIES = os.path.join(BASE_DIR, "evaluation_queries.json")

# R8: listen on the loopback interfaces only, so no other machine can reach the app.
# Both IPv4 and IPv6 loopback are used because browsers resolve "localhost" to ::1
# first, and on macOS the AirPlay Receiver answers on *:5000 otherwise.
HOST = "127.0.0.1"
HOSTS = ("127.0.0.1", "::1")
DEFAULT_PORT = 5000


def create_app(
    default_folder: str = SAMPLE_DOCS,
    eval_folder: str = SAMPLE_DOCS,
    eval_queries: str = EVALUATION_QUERIES,
) -> Flask:
    app = Flask(__name__)
    app.config.update(
        DEFAULT_FOLDER=default_folder,
        EVAL_FOLDER=eval_folder,
        EVAL_QUERIES=eval_queries,
        SEARCH_INDEX=None,  # the in-memory index of the folder the user chose
    )

    def current_index() -> Optional[SearchIndex]:
        return app.config["SEARCH_INDEX"]

    def render_home(**context):
        index = current_index()
        context.setdefault("folder", index.folder if index else app.config["DEFAULT_FOLDER"])
        context.setdefault("query", "")
        context.setdefault("results", [])
        context.setdefault("message", None)
        context.setdefault("message_kind", "info")
        return render_template("index.html", index=index, **context)

    @app.route("/")
    def home():
        return render_home()

    @app.route("/index", methods=["POST"])
    def index_route():
        folder = request.form.get("folder", "")
        index, message = index_folder(folder)
        if index is not None:
            app.config["SEARCH_INDEX"] = index
            return render_home(message=message, message_kind="success")
        # R7: keep any previous index, and show the problem instead of failing.
        return render_home(folder=folder, message=message, message_kind="error")

    @app.route("/search")
    def search_route():
        query = request.args.get("q", "")
        results, message = run_search(current_index(), query)
        return render_home(query=query, results=results, message=message)

    @app.route("/evaluate")
    def evaluate_route():
        raw_k = request.args.get("k", str(DEFAULT_K))
        notice = None
        try:
            k = int(raw_k)
            if not 1 <= k <= MAX_K:
                raise ValueError
        except ValueError:
            k = DEFAULT_K
            notice = "k must be a whole number from 1 to {}; showing k = {}.".format(
                MAX_K, DEFAULT_K
            )
        report = None
        error = None
        try:
            queries = load_queries(app.config["EVAL_QUERIES"])
            index, message = index_folder(app.config["EVAL_FOLDER"])
            if index is None:
                error = message
            else:
                report = evaluate(index, queries, k)
        except (OSError, ValueError) as problem:
            error = "Could not load the evaluation queries: {}".format(problem)
        return render_template(
            "evaluate.html", report=report, error=error, notice=notice, k=k, max_k=MAX_K
        )

    return app


def make_servers(app: Flask, port: int) -> List[BaseWSGIServer]:
    """Create one server per loopback address; skip IPv6 if this machine lacks it."""
    servers = []
    for host in HOSTS:
        try:
            servers.append(make_server(host, port, app, threaded=True))
        except OSError as error:
            ipv6_missing = host == "::1" and (
                not socket.has_ipv6
                or error.errno in (errno.EADDRNOTAVAIL, errno.EAFNOSUPPORT)
            )
            if not ipv6_missing:
                for server in servers:
                    server.server_close()
                raise
    return servers


def main() -> None:
    port = int(os.environ.get("PORT", DEFAULT_PORT))
    app = create_app()
    try:
        servers = make_servers(app, port)
    except OSError as error:
        if error.errno == errno.EADDRINUSE:
            sys.exit(
                "Port {} is already in use. Stop the other program, or run "
                "PORT=5001 python app.py".format(port)
            )
        raise
    print("DeepSearch Local running at http://localhost:{} (only on this computer)".format(port), flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    for server in servers[1:]:
        threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        servers[0].serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        for server in servers:
            server.server_close()


if __name__ == "__main__":
    main()
