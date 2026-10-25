"""同行情报：闲鱼真实搜索 + LLM 分析。"""
from __future__ import annotations

import json
import os
import subprocess

from config import settings


def search_xianyu(query: str, limit: int = 10) -> list[dict]:
    """goofish search items 真实搜索，返回精简商品列表。

    闲鱼搜索页偶发跳验证/登录刷新（playwright 报"Execution context was
    destroyed"），属于风控间歇错误——自动重试一次通常就过。
    子进程剔除代理环境变量（闲鱼国内直连，走代理反而添乱）。
    """
    last_err = ""
    for attempt in range(2):
        env = {k: v for k, v in os.environ.items()
               if k.upper() not in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY")}
        env["PYTHONIOENCODING"] = "utf-8"
        try:
            proc = subprocess.run(  # noqa: S603 .env 配置的本地 CLI
                [settings.goofish_exe, "search", "items", query,
                 "--limit", str(limit), "--format", "json"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                env=env, timeout=120, stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired as e:
            last_err = f"搜索超时: {e}"
            continue
        combined = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode == 0:
            start, end = combined.find("{"), combined.rfind("}")
            if start >= 0 and end > start:
                try:
                    payload = json.loads(combined[start:end + 1])
                    items = []
                    for it in payload.get("items", [])[:limit]:
                        items.append({
                            "title": it.get("title", "")[:60],
                            "price": it.get("price", ""),
                            "want": (it.get("extra") or "").split(" | ")[0],
                            "seller": it.get("seller_nick", ""),
                            "url": it.get("url", ""),
                        })
                    if items:
                        return items
                    last_err = "搜索返回空结果"
                except json.JSONDecodeError as e:
                    last_err = f"搜索结果解析失败: {e}"
            else:
                last_err = "搜索输出中无 JSON"
        else:
            last_err = f"exit={proc.returncode}: {combined[-300:]}"
    raise RuntimeError(f"闲鱼搜索失败（已重试）：{last_err}。"
                       "可稍等几秒再试，或换个关键词。")
