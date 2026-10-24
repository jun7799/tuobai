"""📣 推广服务：为已开张的服务生成推广素材（小红书笔记 / 公众号文章），先看效果再发。"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import streamlit as st

from config import PROJECT_ROOT, settings
from core import llm_client
from core.pipeline import GenCtx

st.markdown("## 📣 推广服务")
st.caption("选一个已开张的服务，生成推广素材——小红书卡片 / 公众号文章，先预览效果，满意再发。")


def _my_runs() -> list[tuple[str, Path]]:
    runs = []
    if settings.output_dir.exists():
        for d in sorted(settings.output_dir.iterdir(),
                        key=lambda x: x.stat().st_mtime, reverse=True):
            if (d / "package.json").exists():
                try:
                    pkg = json.loads((d / "package.json").read_text(encoding="utf-8"))
                    runs.append((pkg["positioning"]["name"], d))
                except (json.JSONDecodeError, KeyError):
                    continue
    return runs


runs = _my_runs()
if not runs:
    st.info("还没有已开张的服务。先去「上架服务」开一家，再来推广。", icon="🐟")
    if st.button("🐟 去上架服务"):
        st.switch_page("ui/launch.py")
    st.stop()

sel = st.selectbox("选择要推广的服务",
                   runs, format_func=lambda x: x[0], key="pm_run")
svc_name, run_dir = sel
pkg = json.loads((run_dir / "package.json").read_text(encoding="utf-8"))
st.caption(f"📍 {run_dir.name}")

promo_dir = PROJECT_ROOT / "data" / "promote" / run_dir.name

tab1, tab2 = st.tabs(["📕 小红书笔记", "📄 公众号文章"])

# ---------- 小红书 ----------
with tab1:
    xhs_dir = run_dir / "xhs"
    cards = sorted(
        list(xhs_dir.glob("cover*.png")) + list(xhs_dir.glob("card_*.png")),
        key=lambda p: (0 if p.name.startswith("cover") else 1, p.name)) \
        if xhs_dir.exists() else []
    if cards:
        cols = st.columns(min(len(cards), 4))
        for i, img in enumerate(cards[:4]):
            with cols[i]:
                st.image(str(img), use_container_width=True)
        st.caption(f"已有 {len(cards)} 张卡片（开张时生成的）。不满意可以换一版 ↓")
    else:
        st.warning("这个服务还没有小红书素材，点下面生成")

    if st.button("🎲 换一版笔记（重新生成文案+卡片）", use_container_width=True):
        with st.status("重新创作中…（AI 写文案 + 渲染卡片，约 60 秒）", expanded=True):
            try:
                new_xhs = llm_client.chat_json(
                    "你是小红书爆款写手，只输出 JSON。",
                    f"为这个服务写一版全新的小红书笔记（与之前不同角度）："
                    f"{json.dumps(pkg.get('xhs', {}), ensure_ascii=False)[:400]}\n"
                    f"服务：{pkg['positioning']['name']} - {pkg['positioning']['one_liner']}\n"
                    '输出：{"cover_emoji":"emoji","cover_title":"≤15字","cover_subtitle":"≤15字",'
                    '"title":"笔记标题≤20字带1个emoji","body_md":"正文300-450字markdown短句短段带emoji小标题","theme_hint":"sketch/default/playful-geometric/neo-brutalism/botanical/professional/retro 选一"}')
                promo_dir.mkdir(parents=True, exist_ok=True)
                new_dir = promo_dir / "xhs"
                new_dir.mkdir(exist_ok=True)
                front = ("---\n"
                         f'emoji: "{new_xhs.get("cover_emoji", "🚀")}"\n'
                         f'title: "{new_xhs.get("cover_title", "")}"\n'
                         f'subtitle: "{new_xhs.get("cover_subtitle", "")}"\n---\n\n')
                (new_dir / "content.md").write_text(
                    front + new_xhs.get("body_md", "") + "\n", encoding="utf-8")
                env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
                proc = subprocess.run(  # noqa: S603 本地渲染脚本
                    [settings.py_main, settings.render_xhs,
                     str(new_dir / "content.md"), "-t",
                     new_xhs.get("theme_hint", "sketch"), "-m", "auto-split",
                     "-o", str(new_dir)],
                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                    env=env, timeout=150, stdin=subprocess.DEVNULL)
                new_cards = sorted(list(new_dir.glob("cover*.png")) + list(new_dir.glob("card_*.png")))
                if new_cards:
                    st.write(f"新版 {len(new_cards)} 张卡片已生成")
                    st.session_state["_promo_xhs_dir"] = str(new_dir)
                else:
                    st.error(f"渲染失败：{((proc.stdout or '')+(proc.stderr or ''))[-300:]}")
            except llm_client.LLMError as e:
                st.error(f"生成失败：{e}")

    show_dir = Path(st.session_state.get("_promo_xhs_dir", "")) \
        if st.session_state.get("_promo_xhs_dir") else xhs_dir
    if st.session_state.get("_promo_xhs_dir"):
        st.divider()
        st.markdown("**新版卡片**")
        new_cards = sorted(list(show_dir.glob("cover*.png")) + list(show_dir.glob("card_*.png")))
        cols = st.columns(min(len(new_cards), 4))
        for i, img in enumerate(new_cards[:4]):
            with cols[i]:
                st.image(str(img), use_container_width=True)

    if show_dir.exists() and (show_dir / "content.md").exists():
        img_names = " ".join(p.name for p in sorted(
            list(show_dir.glob("cover*.png")) + list(show_dir.glob("card_*.png")))) or "cover.png"
        cmd = (f'用 xhs-note-creator skill 发布小红书笔记：标题「{pkg["xhs"].get("title","")}」，'
               f'内容用 {show_dir / "content.md"}，配图 {img_names}（目录 {show_dir}），'
               "先仅自己可见预览，我看过效果后再公开发布")
        st.markdown("**发布**（先预览再公开）")
        st.code(cmd, language=None)

# ---------- 公众号 ----------
with tab2:
    article_path = promo_dir / "article.md"
    if st.button("✍️ 生成公众号推广文章", use_container_width=True):
        with st.status("AI 撰写中（约 30 秒）…"):
            try:
                article = llm_client.chat_text(
                    "你是技术博主，写接地气的公众号推广文。风格：口语化、step-by-step、"
                    "有踩坑提示。为下面的服务写一篇 600-800 字的推广文章（markdown）："
                    "开头用场景痛点钩子，中间介绍服务怎么帮到读者（分点），"
                    "结尾引导到闲鱼下单。标题单独一行用 # 开头。",
                    f"服务信息：{json.dumps(pkg['positioning'], ensure_ascii=False)}\n"
                    f"卖点：{json.dumps(pkg['service_card'].get('highlights', []), ensure_ascii=False)}\n"
                    f"定价：{json.dumps(pkg['positioning'].get('tiers', []), ensure_ascii=False)}",
                    temperature=0.7)
                article_path.parent.mkdir(parents=True, exist_ok=True)
                article_path.write_text(article, encoding="utf-8")
                st.session_state["_promo_article"] = article
            except llm_client.LLMError as e:
                st.error(f"生成失败：{e}")

    article = None
    if "_promo_article" in st.session_state:
        article = st.session_state["_promo_article"]
    elif article_path.exists():
        article = article_path.read_text(encoding="utf-8")

    if article:
        st.divider()
        st.markdown("**文章预览**")
        st.markdown(article)
        st.markdown("**发布**：复制下面指令到 Claude Code，用排版 skill 生成公众号格式")
        st.code(f"用 wechat-typesetting skill 把 {article_path} 排版成公众号文章，"
                "我看过效果再发布", language=None)
        st.download_button("⬇️ 下载文章 markdown", article.encode("utf-8"),
                           file_name=f"{svc_name}_公众号推广.md", use_container_width=True)
