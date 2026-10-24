"""同行情报：闲鱼真实搜索 + LLM 分析。"""
from __future__ import annotations

import json
import os
import subprocess

from config import settings


def search_xianyu(query: str, limit: int = 10) -> list[dict]:
    """goofish search items 真实搜索，返回精简商品列表。"""
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.run(  # noqa: S603 .env 配置的本地 CLI
        [settings.goofish_exe, "search", "items", query,
         "--limit", str(limit), "--format", "json"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, timeout=120, stdin=subprocess.DEVNULL)
    combined = (proc.stdout or "") + (proc.stderr or "")
    start, end = combined.find("{"), combined.rfind("}")
    if proc.returncode != 0 or start < 0:
        raise RuntimeError(f"闲鱼搜索失败 exit={proc.returncode}: {combined[-300:]}")
    try:
        payload = json.loads(combined[start:end + 1])
    except json.JSONDecodeError as e:
        raise RuntimeError(f"搜索结果解析失败: {e}") from e
    items = []
    for it in payload.get("items", [])[:limit]:
        items.append({
            "title": it.get("title", "")[:60],
            "price": it.get("price", ""),
            "want": (it.get("extra") or "").split(" | ")[0],
            "seller": it.get("seller_nick", ""),
            "url": it.get("url", ""),
        })
    return items
