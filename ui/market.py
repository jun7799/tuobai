"""看同行：闲鱼真实搜索同行商品 + AI 情报报告，双引擎。"""
from __future__ import annotations

import re

import streamlit as st

from config import PROJECT_ROOT
from core import llm_client, market_intel, profile as profile_store

SYSTEM = """你是一人公司市场情报分析师。基于你对国内自由职业/副业市场的了解，
生成一份《同行都在做什么》情报报告，markdown 格式。要求：
- 实战视角，别写成学术论文；每个判断给出可操作的建议
- 价格要给具体数字区间（人民币），分低/中/高三档并说明各档都包含什么
- 标题套路要给 3 个可直接套用的示例
- 结论落到：他该怎么切入
"""

TEMPLATE = """分析方向：{skill}

用户画像（可参考）：
- 背景：{background}
- 擅长：{strengths}

生成报告结构（markdown，含 emoji 小标题）：
## 这个方向有市场吗
需求场景、目标客户画像、付费意愿评估（1-2 段）

## 同行定价参考
| 档位 | 价格区间 | 都包含什么 | 谁在买 |
（低/中/高三档，具体数字）

## 同行怎么获客
小红书/闲鱼的主流玩法：内容形式、3 个可直接套用的标题示例

## 差异化切入建议
结合用户画像给 2-3 条具体的差异化打法（别泛泛而谈）

## 今日灵感卡
给 3 条今天就能上手的生意点子（结合方向+画像，每条一句话+定价）

## 避坑提醒
这个方向新手最容易踩的 3 个坑
"""

st.markdown("## 🕵️ 看同行")
st.caption("两路情报：① 真实抓闲鱼在售同行商品（价格/热度）② AI 情报报告。每天来看一眼，灵感不断。")

p = profile_store.load_profile()
default_skill = p.get("direction") or st.session_state.get("skill", "")
skill = st.text_input("想看哪个方向", value=default_skill,
                      placeholder="例：帮人做PPT美化 / AI老照片修复 / 简历优化")

tab1, tab2 = st.tabs(["🛒 闲鱼真实同行", "🤖 AI 情报报告"])

with tab1:
    if st.button("🔍 搜索闲鱼同行在售商品", type="primary", use_container_width=True):
        if len(skill.strip()) < 2:
            st.warning("先在上面输入一个方向（至少 2 个字），比如「PPT 美化」")
            st.stop()
        with st.status("真实抓取闲鱼搜索结果…（约 20 秒，浏览器路径）", expanded=True):
            try:
                items = market_intel.search_xianyu(skill.strip(), limit=10)
                st.session_state["_market_items"] = items
                st.write(f"抓到 {len(items)} 件同行商品")
            except Exception as e:  # noqa: BLE001
                st.error(f"抓取失败：{e}")

    if "_market_items" in st.session_state:
        items = st.session_state["_market_items"]
        if items:
            table = ["| 商品 | 价格 | 热度 | 卖家 |", "|---|---|---|---|"]
            for it in items:
                table.append(f"| [{it['title'][:32]}]({it['url']}) | **{it['price']}** "
                             f"| {it['want']} | {it['seller']} |")
            st.markdown("\n".join(table))
            if st.button("🤖 让 AI 点评这批同行", use_container_width=True):
                with st.status("AI 分析同行打法…"):
                    try:
                        brief = "\n".join(
                            f"- {it['title']} | {it['price']} | {it['want']}"
                            for it in items)
                        insight = llm_client.chat_text(
                            "你是一人公司市场分析师。根据真实闲鱼同行商品数据，"
                            "输出 markdown 分析：价格带分布（低/中/高具体数字）、"
                            "卖得好的商品标题套路（3条规律）、给我的切入建议（2条，具体）。300字内。",
                            f"方向：{skill}\n同行商品：\n{brief}", temperature=0.6)
                        st.session_state["_market_insight"] = insight
                    except llm_client.LLMError as e:
                        st.error(f"AI 分析失败：{e}")
        else:
            st.warning("没有搜到同行商品，换个关键词试试")

    if "_market_insight" in st.session_state:
        st.divider()
        st.markdown("### 🤖 AI 点评")
        st.markdown(st.session_state["_market_insight"])

with tab2:
    if st.button("📄 生成 AI 情报报告", type="primary", use_container_width=True):
        if len(skill.strip()) < 4:
            st.warning("先在上面输入一个方向（至少 4 个字），比如「帮人改简历」")
            st.stop()
        with st.status("🤖 情报分析中（约 20 秒）…", expanded=True) as status:
            st.caption("正在汇总市场情况…")
            try:
                report = llm_client.chat_text(
                    SYSTEM,
                    TEMPLATE.format(
                        skill=skill.strip(),
                        background=p.get("background") or "（未填写）",
                        strengths="、".join(p.get("strengths", [])) or "（未填写）"),
                    temperature=0.6)
                report = re.sub(r"^```\w*\n?|\n?```$", "", report.strip())
                slug = re.sub(r"[^\w一-鿿]+", "-", skill).strip("-")[:16] or "report"
                archive = PROJECT_ROOT / "data" / f"market_{slug}.md"
                archive.parent.mkdir(parents=True, exist_ok=True)
                archive.write_text(f"# 同行情报 · {skill}\n\n{report}", encoding="utf-8")
                status.update(label="报告生成完毕", state="complete")
                st.session_state["_market_report"] = report
            except llm_client.LLMError as e:
                st.error(f"生成失败：{e}")
                st.stop()

    if "_market_report" in st.session_state:
        st.markdown(st.session_state["_market_report"])

st.divider()
if st.button("🐟 就做这个方向，去上架", use_container_width=True):
    st.session_state.skill = skill.strip()
    st.session_state.step = "intake"
    st.switch_page("ui/launch.py")
