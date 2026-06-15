"""Modal download entry for crawl4ai.

Run:
  modal run download.py::download
"""

from __future__ import annotations

import modal

app = modal.App("crawl4ai-download")


@app.local_entrypoint()
def download() -> None:
    print("No download step required for crawl4ai.")
