"""图片工厂：闲鱼主图（生图API）。小红书卡片图由 render_xhs.py 排版生成，不走这里。"""
from __future__ import annotations

from pathlib import Path

from core import llm_client
from core.pipeline import GenCtx, ReportFn

# 统一视觉风格后缀：主图要干净、无文字（文字由平台/排版负责）
STYLE_SUFFIX = ", flat illustration style, warm color palette, clean composition, no text, no watermark"


def gen_xianyu_main(ctx: GenCtx, report: ReportFn) -> Path:
    """闲鱼主图（服务卡展示也复用这张）。"""
    pkg = ctx.pkg
    prompts = pkg.get("xianyu", {}).get("image_prompts") or []
    prompt = (prompts[0] if prompts else
              f"poster for the service: {ctx.skill}") + STYLE_SUFFIX
    out = ctx.out_dir / "xianyu_main.png"
    report(f"生图中（gpt-image-2，约 25 秒）…")
    llm_client.gen_image(prompt, out)
    report(f"已保存 xianyu_main.png")
    return out
