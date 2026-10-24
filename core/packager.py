"""服务打包器：一次 LLM 调用生成全套开张文案（pack.json）。"""
from __future__ import annotations

import json
from pathlib import Path

from config import settings
from core import llm_client

_REQUIRED_KEYS = ["positioning", "service_card", "xianyu", "xhs", "talk_track", "video"]

# 风控词（与 xianyu.py 共用词表源，这里只做展示级校验）
try:
    from core.risk_words import RISK_WORDS_ALL
except ImportError:  # 词表文件还没生成时的兜底
    RISK_WORDS_ALL = []


class PackageError(Exception):
    """打包失败。"""


def build_master_prompt(role: str, skill: str, case: str | None) -> str:
    template = (settings.prompts_dir / "master_prompt.md").read_text(encoding="utf-8")
    return template.format(role=role, skill=skill, case=(case or "").strip() or "（无）")


def validate(pkg: dict) -> list[str]:
    """返回问题列表（空=通过）。超长做提示，不整趟重跑。"""
    problems = []
    for key in _REQUIRED_KEYS:
        if key not in pkg or not isinstance(pkg[key], dict):
            problems.append(f"缺少字段：{key}")
    if problems:
        return problems
    xy = pkg["xianyu"]
    if len(xy.get("title", "")) > 30:
        problems.append(f"闲鱼标题超长（{len(xy['title'])}字>30），将自动截断")
    try:
        price = float(xy.get("price", 0))
        if not 1 <= price <= 9999:
            problems.append("闲鱼价格超出 1-9999 区间，将回退 69")
    except (TypeError, ValueError):
        problems.append("闲鱼价格不是数字，将回退 69")
    body = pkg["xhs"].get("body_md", "")
    if len(body) < 100:
        problems.append("小红书正文偏短（<100字）")
    return problems


def _autofix(pkg: dict) -> dict:
    """本地自动修正超长/非法字段，避免整趟重跑。"""
    xy = pkg.get("xianyu", {})
    if len(xy.get("title", "")) > 30:
        xy["title"] = xy["title"][:30]
    try:
        price = float(xy.get("price", 69))
        if not 1 <= price <= 9999:
            price = 69
    except (TypeError, ValueError):
        price = 69
    xy["price"] = int(price)
    pkg["xianyu"] = xy
    return pkg


def risk_scan(pkg: dict) -> list[str]:
    """扫全部文本字段里的风控词（发布前 UI 展示用）。"""
    text = json.dumps(pkg, ensure_ascii=False)
    return [w for w in RISK_WORDS_ALL if w in text]


def build_package(role: str, skill: str, case: str | None = None) -> dict:
    """主入口：构建并校验 pack（不落盘，落盘由 pipeline 负责）。"""
    prompt = build_master_prompt(role, skill, case)
    system = "你是一人公司开张专家，只输出合法 JSON，不输出任何多余文字。"
    try:
        pkg = llm_client.chat_json(system, prompt)
    except llm_client.LLMError as e:
        raise PackageError(str(e)) from e
    problems = validate(pkg)
    fatal = [p for p in problems if p.startswith("缺少字段")]
    if fatal:
        raise PackageError("打包不完整：" + "；".join(fatal))
    pkg = _autofix(pkg)
    pkg["_warnings"] = [p for p in problems if not p.startswith("缺少字段")]
    return pkg


def save_package(pkg: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "package.json"
    path.write_text(json.dumps(pkg, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
