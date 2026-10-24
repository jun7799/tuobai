"""小红书卡片：pack.json → content.md → render_xhs.py 渲染 → cover+cards。

渲染用系统 Python312（playwright+chromium 现成），成败以"产物文件是否产出"判定
（不解析 stdout，规避中文编码问题）。
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from config import settings
from core.pipeline import GenCtx, ReportFn


def write_content_md(ctx: GenCtx) -> Path:
    """按 render_xhs.py 要求的格式写 content.md（frontmatter + 正文）。"""
    pkg = ctx.pkg
    xhs = pkg["xhs"]
    workdir = ctx.out_dir / "xhs"
    workdir.mkdir(parents=True, exist_ok=True)
    front = (
        "---\n"
        f'emoji: "{xhs.get("cover_emoji", "🚀")}"\n'
        f'title: "{xhs.get("cover_title", "")}"\n'
        f'subtitle: "{xhs.get("cover_subtitle", "")}"\n'
        "---\n\n"
    )
    body = xhs.get("body_md", "")
    if not any(t.startswith("#") for t in body.splitlines() if t.strip()):
        body = "# " + pkg["positioning"]["one_liner"] + "\n\n" + body
    path = workdir / "content.md"
    path.write_text(front + body + "\n", encoding="utf-8")
    return path


def render_cards(ctx: GenCtx, report: ReportFn) -> list[Path]:
    """subprocess 调 render_xhs.py（系统 Python312）。返回产出的图片列表。"""
    import time as _time
    if not settings.py_main or not settings.render_xhs:
        raise RuntimeError("未配置 PY_MAIN / RENDER_XHS")
    workdir = ctx.out_dir / "xhs"
    theme = ctx.pkg.get("xhs", {}).get("theme_hint") or settings.xhs_theme
    cmd = [
        settings.py_main, settings.render_xhs,
        str(workdir / "content.md"),
        "-t", theme, "-m", "auto-split",
        "-o", str(workdir),
    ]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    log = workdir / "render.log"

    def _log(msg: str) -> None:
        with open(log, "a", encoding="utf-8") as f:
            f.write(f"[{_time.strftime('%H:%M:%S')}] {msg}\n")

    _log(f"cmd: {' '.join(cmd)}")
    report(f"渲染卡片中（主题 {theme}，约 40 秒）…")
    _t0 = _time.time()
    proc = subprocess.run(  # noqa: S603 路径来自本地 .env 配置
        cmd, capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=env,
        timeout=150, stdin=subprocess.DEVNULL,
    )
    _log(f"exit={proc.returncode} 耗时={_time.time()-_t0:.1f}s")
    images = sorted(
        list(workdir.glob("cover*.png")) + list(workdir.glob("card_*.png")),
        key=lambda p: (0 if p.name.startswith("cover") else 1, p.name),
    )
    if not images:
        tail = ((proc.stdout or "") + (proc.stderr or ""))[-500:]
        _log(f"无产出。tail: {tail}")
        raise RuntimeError(f"渲染无产出。exit={proc.returncode} 输出尾部：{tail}")
    report(f"已产出 {len(images)} 张图：{', '.join(p.name for p in images)}")
    return images


def build_publish_command(ctx: GenCtx) -> str:
    """生成可复制的 Claude Code 发布指令（面板"复制发布命令"按钮用）。"""
    workdir = ctx.out_dir / "xhs"
    images = sorted(
        list(workdir.glob("cover*.png")) + list(workdir.glob("card_*.png")),
        key=lambda p: (0 if p.name.startswith("cover") else 1, p.name),
    )
    img_names = " ".join(p.name for p in images) or "cover.png card_1.png"
    title = ctx.pkg.get("xhs", {}).get("title", "")
    return (
        f'用 xhs-note-creator skill 发布小红书笔记：标题「{title}」，'
        f'内容用 {workdir / "content.md"}，配图 {img_names}（目录 {workdir}），'
        "先仅自己可见预览，确认后公开发布"
    )


def run_step(ctx: GenCtx, report: ReportFn) -> list[Path]:
    write_content_md(ctx)
    return render_cards(ctx, report)
