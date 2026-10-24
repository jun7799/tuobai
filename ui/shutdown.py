"""关张转职：一键下架 → 关张清算报告 → AI 简历 + 求职指引。

设计立场：关张不是失败，是换一条路。清算报告把经营数据变成简历资产。
"""
from __future__ import annotations

import json
import os
import subprocess

import streamlit as st

from config import PROJECT_ROOT, settings
from core import finance, llm_client, profile as profile_store

st.markdown("## 🚪 关张转职")
st.caption("一人公司干不下去了？体面关张：下架商品 → 一份清算报告 → 经验写进简历，换个姿势继续。"
           "**关张不是失败，是换一条路。**")

# ---------- 在售商品 ----------
online: list[tuple[str, str, str]] = []  # (item_id, 服务名, run目录)
if settings.output_dir.exists():
    for d in settings.output_dir.iterdir():
        sp, pp = d / "state.json", d / "package.json"
        if sp.exists() and pp.exists():
            try:
                state = json.loads(sp.read_text(encoding="utf-8"))
                item_id = state.get("xianyu_item_id")
                if item_id:
                    pkg = json.loads(pp.read_text(encoding="utf-8"))
                    online.append((str(item_id), pkg["positioning"]["name"], str(d)))
            except (json.JSONDecodeError, KeyError):
                continue

st.markdown("### 第一步 · 下架在售商品")
if online:
    for item_id, svc, _ in online:
        st.markdown(f"- 🐟 **{svc}**（item_id: {item_id}）")
    confirm = st.checkbox("我确认下架以上全部闲鱼商品（可随时重新开张）")
    if st.button("⬇️ 一键下架", type="primary", disabled=not confirm):
        ok, fail = 0, []
        for item_id, svc, _ in online:
            with st.status(f"下架 {svc}…"):
                env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
                proc = subprocess.run(  # noqa: S603 .env 配置的本地 CLI
                    [settings.goofish_exe, "item", "delete", item_id, "--format", "json"],
                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                    env=env, timeout=120, stdin=subprocess.DEVNULL)
                if proc.returncode == 0:
                    ok += 1
                else:
                    fail.append(f"{svc}: exit={proc.returncode}")
        if ok:
            st.success(f"已下架 {ok} 件商品")
        if fail:
            st.error("下架失败：" + "；".join(fail))
        st.rerun()
else:
    st.caption("当前没有在售的闲鱼商品（或已下架）")

st.divider()

# ---------- 关张清算报告 ----------
st.markdown("### 第二步 · 关张清算报告")

def _report_data() -> str:
    s = finance.summary()
    leads = profile_store.load_leads()
    runs = 0
    if settings.output_dir.exists():
        runs = sum(1 for d in settings.output_dir.iterdir()
                   if (d / "package.json").exists())
    won = [l for l in leads if l.get("stage") == "已成交"]
    return (f"经营期间：开张服务 {runs} 个；商机 {len(leads)} 条（成交 {len(won)} 单）；"
            f"财务：收入 ¥{s['income']} / 支出 ¥{s['expense']} / 净额 ¥{s['net']}；"
            f"分类明细：{json.dumps(s['by_category'], ensure_ascii=False)}")


if st.button("📋 生成清算报告", use_container_width=True):
    p = profile_store.load_profile()
    with st.status("AI 撰写清算报告…"):
        try:
            report = llm_client.chat_text(
                "你是一人公司复盘顾问。根据经营数据写一份《关张清算报告》，markdown 格式。"
                "语气：体面、幽默、有数据、有反思、有收获。包含：经营成果盘点（用数据说话）、"
                "三条做得对的、三条学到的、给下一个项目的建议。400 字以内。",
                f"用户画像：{json.dumps(p, ensure_ascii=False)}\n经营数据：{_report_data()}",
                temperature=0.7)
            path = PROJECT_ROOT / "data" / "关张清算报告.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(report, encoding="utf-8")
            st.session_state["_shutdown_report"] = report
        except llm_client.LLMError as e:
            st.error(f"生成失败：{e}")

if "_shutdown_report" in st.session_state:
    st.markdown(st.session_state["_shutdown_report"])
    path = PROJECT_ROOT / "data" / "关张清算报告.md"
    if path.exists():
        with open(path, "rb") as f:
            st.download_button("⬇️ 下载报告", f, file_name="关张清算报告.md",
                               mime="text/markdown", use_container_width=True)

st.divider()

# ---------- 转职：AI 简历 + 求职指引 ----------
st.markdown("### 第三步 · 带着经验去求职")

c1, c2 = st.columns([2, 1])
with c1:
    if st.button("📄 AI 用我的画像+经营经验生成简历初稿", use_container_width=True):
        p = profile_store.load_profile()
        with st.status("AI 撰写简历初稿…"):
            try:
                resume = llm_client.chat_text(
                    "你是资深猎头。根据用户画像和一人公司经营经历，写一份简历初稿（markdown）。"
                    "重点：把独立经营经历写成简历亮点（项目经验+量化成果），"
                    "结构：个人信息/核心优势/项目经验（把经营当项目写）/技能清单。",
                    f"画像：{json.dumps(p, ensure_ascii=False)}\n经营数据：{_report_data()}",
                    temperature=0.6)
                rpath = PROJECT_ROOT / "data" / "简历初稿.md"
                rpath.parent.mkdir(parents=True, exist_ok=True)
                rpath.write_text(resume, encoding="utf-8")
                st.session_state["_resume"] = resume
            except llm_client.LLMError as e:
                st.error(f"生成失败：{e}")
with c2:
    st.markdown("**开始找工作：**")

if "_resume" in st.session_state:
    with st.expander("📄 简历初稿（点击展开）"):
        st.markdown(st.session_state["_resume"])
    rpath = PROJECT_ROOT / "data" / "简历初稿.md"
    if rpath.exists():
        with open(rpath, "rb") as f:
            st.download_button("⬇️ 下载简历初稿", f, file_name="简历初稿.md",
                               mime="text/markdown", use_container_width=True)

st.code("在 Claude Code 里执行（boss-job-hunter skill 自动搜职位+匹配+打招呼）：\n"
        "帮我用 boss-job-hunter 搜「Python 自动化」相关职位，用我刚生成的简历匹配打分",
        language=None)
