"""话术包 + 服务打包卡：pack.json → markdown 落盘。"""
from __future__ import annotations

from pathlib import Path

from core.pipeline import GenCtx, ReportFn


def render_service_card_md(ctx: GenCtx) -> Path:
    pkg = ctx.pkg
    pos, card = pkg["positioning"], pkg["service_card"]
    lines = [f"# {pos['name']} · 服务卡", "", f"> {pos['one_liner']}", ""]

    lines.append("## 定价")
    lines.append("")
    lines.append("| 档位 | 价格 | 包含 |")
    lines.append("|---|---|---|")
    for tier in pos.get("tiers", []):
        lines.append(f"| {tier['name']} | ¥{tier['price']} | {tier['includes']} |")

    lines += ["", f"**目标客户**：{pos.get('target_customer','')}", ""]

    lines.append("## 卖点")
    lines.append("")
    for i, h in enumerate(card.get("highlights", []), 1):
        lines.append(f"{i}. {h}")

    lines += ["", "## 交付标准", "", card.get("delivery_standard", ""),
              "", f"**修改政策**：{card.get('revision_policy','')}", ""]

    lines.append("## 常见问题")
    lines.append("")
    for faq in card.get("faq", []):
        lines += [f"**Q：{faq['q']}**", "", f"A：{faq['a']}", ""]

    path = ctx.out_dir / "服务卡.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def render_talk_track_md(ctx: GenCtx) -> Path:
    talk = ctx.pkg.get("talk_track", {})
    lines = ["# 接待话术包", ""]

    lines += ["## 30 秒开场白", "", talk.get("opening_30s", ""), ""]

    lines.append("## 评论区回复")
    lines.append("")
    for item in talk.get("comment_replies", []):
        lines += [f"**{item['scene']}**", "", f"> {item['reply']}", ""]

    lines.append("## 私信应答")
    lines.append("")
    for item in talk.get("inquiry_replies", []):
        lines += [f"**{item['scenario']}**", "", item["script"], ""]

    lines += ["## 嫌贵应对", "", talk.get("price_objection", ""), ""]

    path = ctx.out_dir / "话术包.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run_step(ctx: GenCtx, report: ReportFn) -> list[Path]:
    p1 = render_service_card_md(ctx)
    p2 = render_talk_track_md(ctx)
    report("已保存 服务卡.md + 话术包.md")
    return [p1, p2]
