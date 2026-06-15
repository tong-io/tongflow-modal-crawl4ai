"""Modal deploy entry for crawl4ai.

Deploy:
  modal deploy deploy.py
"""

from __future__ import annotations
from pathlib import Path

import asyncio
import logging
from typing import Any

import modal
from tongflow import deploy
from tongflow.models.link import LinkInput, LinkOutput
from tongflow.node_slots import NodeSlots
from tongflow.slots import node_slot


_cfg: dict[str, Any] = {}
_ = _cfg

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

image = (
    modal.Image.from_registry("unclecode/crawl4ai:0.7.7")
    .pip_install(
        "tongflow==0.1.0",
    )
)

app = modal.App(Path(__file__).resolve().parent.name, image=image)
secrets = modal.Secret.from_name("OPENAPI")

with image.imports():
    from crawl4ai import AsyncWebCrawler


def _maybe_fix_utf8_misdecode(text: str) -> str:
    if not text:
        return text

    def cjk_count(s: str) -> int:
        return sum(1 for c in s if "\u4e00" <= c <= "\u9fff")

    best = text
    best_n = cjk_count(text)
    for enc in ("latin-1", "cp1252"):
        try:
            fixed = text.encode(enc).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError, LookupError):
            continue
        n = cjk_count(fixed)
        if n > best_n:
            best = fixed
            best_n = n
    return best


def _crawl_task_core(task: Dict[str, Any]) -> Dict[str, Any]:
    try:
        task_id = task["taskId"]
        prompt = task["prompt"]

        url = prompt.get("url")
        if not url:
            return {
                "success": False,
                "status": "error",
                "error": "missing url in prompt",
            }

        logger.info(f"[{task_id}] crawl start: {url}")

        async def _arun():
            async with AsyncWebCrawler() as crawler:
                return await crawler.arun(url=url)

        result = asyncio.run(_arun())

        success = bool(result.success)
        error_message = str(result.error_message) if result.error_message else None
        markdown_content = str(result.markdown) if result.markdown else ""
        markdown_content = _maybe_fix_utf8_misdecode(markdown_content)

        if not success:
            error_msg = f"crawl failed: {error_message}"
            logger.error(f"[{task_id}] {error_msg}")
            return {"success": False, "status": "error", "error": error_msg}

        response_data = {
            "success": True,
            "url": str(url),
            "markdown": markdown_content,
            "content_length": len(markdown_content),
        }
        logger.info(
            f"[{task_id}] crawl ok: {url} len={response_data['content_length']}"
        )
        return response_data

    except Exception as e:
        logger.error(f"crawl failed: {e}", exc_info=True)
        return {"success": False, "status": "error", "error": str(e)}


@app.function(cpu=2.0, memory=4096, timeout=600, secrets=[secrets], scaledown_window=5)
def crawl(task: Dict[str, Any]) -> Dict[str, Any]:
    return _crawl_task_core(task)


@deploy
@app.cls(cpu=2.0, memory=4096, timeout=600, secrets=[secrets], scaledown_window=5)
class Inference:
    @modal.method()
    @node_slot(NodeSlots.LINK)
    def link(self, input: LinkInput) -> LinkOutput:
        if not input.url:
            return LinkOutput(success=False, error="missing url in prompt")
        result = _crawl_task_core(
            {"taskId": "openflow-crawl", "prompt": {"url": input.url}}
        )
        if not result.get("success"):
            return LinkOutput(
                success=False,
                error=str(result.get("error") or "crawl failed"),
            )
        return LinkOutput(
            success=True,
            mainText=str(result.get("markdown") or ""),
        )
