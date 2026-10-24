"""闲鱼模块：风控预检 + 自动修正 + subprocess 发布 + 进程内限流。

goofish-cli 发布命令（已验证）：
  goofish.exe item publish "标题" "描述" 图1.png 图2.png 价格 --format json
约束：写操作限流 1件/分钟；发布不可逆，必须由用户在 UI 明确确认后调用。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path

from config import settings
from core.risk_words import ABSOLUTE_WORDS, EXTERNAL_WORDS, REPLACE_MAP

_last_publish_ts: float = 0.0          # 进程内限流（UI 与 CLI 同进程）
RATE_LIMIT_SECONDS = 65                # goofish 写操作 1 次/分钟，留 5s 裕量


def precheck(title: str, desc: str) -> list[str]:
    """返回命中的风控词。"""
    text = f"{title} {desc}"
    hits = [w for w in ABSOLUTE_WORDS + EXTERNAL_WORDS if w in text]
    return hits


def sanitize(title: str, desc: str) -> tuple[str, str, list[str]]:
    """自动修正：绝对化词按 REPLACE_MAP 替换，外联词直接删除。返回 (title, desc, 修正日志)。"""
    log: list[str] = []

    def _fix(text: str) -> str:
        for w in REPLACE_MAP:
            if w in text:
                text = text.replace(w, REPLACE_MAP[w])
                log.append(f"已替换风控词「{w}」")
        for w in EXTERNAL_WORDS:
            if w in text:
                text = text.replace(w, "")
                log.append(f"已删除外联词「{w}」")
        return re.sub(r"[ \t]{2,}", " ", text).strip()

    return _fix(title), _fix(desc), log


def guard_rate_limit() -> int:
    """距下次可发布还需等待的秒数（0=现在就能发）。"""
    wait = RATE_LIMIT_SECONDS - (time.time() - _last_publish_ts)
    return max(0, int(wait) + 1)


def publish_item(title: str, desc: str, images: list[Path], price: float,
                 *, timeout: int = 240) -> dict:
    """调用 goofish-cli 发布商品。成功返回 {"ok":True,"item_id":...,"raw":...}。

    编码三件套（Windows GBK 控制台是最大坑）：
    encoding=utf-8 / errors=replace / env PYTHONIOENCODING=utf-8
    """
    global _last_publish_ts
    if not settings.goofish_exe:
        return {"ok": False, "error": "未配置 GOOFISH_EXE"}
    hits = precheck(title, desc)
    if hits:
        return {"ok": False, "error": f"文案含风控词未修正：{hits}"}

    wait = guard_rate_limit()
    if wait > 0:
        return {"ok": False, "error": f"限流中，距下次可发布还需 {wait}s", "wait": wait}

    cmd = [
        settings.goofish_exe, "item", "publish",
        title, desc,
        *[str(p) for p in images],
        str(int(price)),
        "--format", "json",
    ]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.run(  # noqa: S603 路径来自本地 .env 配置
        cmd, capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=env, timeout=timeout,
    )
    _last_publish_ts = time.time()
    combined = (proc.stdout or "") + (proc.stderr or "")
    # goofish 的 stdout 混有日志行：从首个 { 到最后一个 } 切片
    start, end = combined.find("{"), combined.rfind("}")
    payload = None
    if start >= 0 and end > start:
        try:
            payload = json.loads(combined[start:end + 1])
        except json.JSONDecodeError:
            payload = None
    if proc.returncode == 0 and payload is not None:
        item_id = payload.get("item_id") or payload.get("itemId") or payload.get("item_id_str")
        url = payload.get("url") or payload.get("item_url")
        return {"ok": True, "item_id": item_id, "url": url, "raw": payload}
    return {"ok": False, "error": f"exit={proc.returncode}", "raw": combined[-800:]}
