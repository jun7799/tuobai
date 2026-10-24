"""💰 记账：三个入口并列——手动记 / 跟 AI 说 / 其他 agent 调 CLI。"""
from __future__ import annotations

import streamlit as st

from core import finance
from ui.components import chat_assistant, cli_card

st.markdown("## 💰 记账")
st.caption("一人公司也要记账。三种记法：手填、跟 AI 说一句、或者让别的 AI agent 直接调命令。")

s = finance.summary()
c1, c2, c3, c4 = st.columns(4)
c1.metric(f"{s['month']} 收入", f"¥{s['income']:.1f}")
c2.metric(f"{s['month']} 支出", f"¥{s['expense']:.1f}")
c3.metric("净额", f"¥{s['net']:.1f}", delta=None if s["net"] == 0 else f"{s['net']:+.1f}")
c4.metric("记账笔数", s["count"])

st.divider()

tab1, tab2, tab3 = st.tabs(["📝 手动记", "💬 跟阿托说", "🤖 其他 agent 记"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        in_type = st.radio("类型", ["收入", "支出"], horizontal=True, key="fin_type")
        amount = st.number_input("金额（元）", min_value=0.1, max_value=999999.0,
                                 step=0.1, key="fin_amount")
        cats = finance.CATEGORIES_INCOME if in_type == "收入" else finance.CATEGORIES_EXPENSE
        category = st.selectbox("分类", cats, key="fin_cat")
    with col2:
        note = st.text_input("备注", key="fin_note", placeholder="例：爬虫定制单")
        source = st.text_input("来源", key="fin_source", placeholder="例：闲鱼 / 小红书 / 老客复购")
    if st.button("💾 记账", type="primary", use_container_width=True):
        rec = finance.add("income" if in_type == "收入" else "expense", amount, note,
                          category=category, source=source)
        st.toast(f"已记账：{'收入' if rec['type']=='income' else '支出'} ¥{rec['amount']}")
        st.rerun()

with tab2:
    def _preview_fin(d: dict) -> None:
        icon = "🟢 收入" if d.get("type") == "income" else "🔴 支出"
        st.markdown(f"{icon} **¥{d.get('amount', '?')}** · {d.get('category', '')} · "
                    f"{d.get('note', '')}（来源：{d.get('source', '')}）")

    def _save_fin(d: dict) -> None:
        finance.add(d["type"], float(d["amount"]), d.get("note", ""),
                    category=d.get("category", ""), source=d.get("source", ""))

    chat_assistant(
        "finance",
        hint="例：今天闲鱼成交一单爬虫脚本，收了69",
        extract_format=('{"type":"income或expense","amount":数字,"note":"备注",'
                        '"category":"分类（服务收入/咨询收入/课程知识付费/其他收入/工具成本/API费用/推广费用/素材采购/其他支出 选一）",'
                        '"source":"来源平台"}'),
        preview=_preview_fin,
        on_confirm=_save_fin,
    )

with tab3:
    cli_card("给其他 agent 的记账入口", [
        r'.\.venv\Scripts\python.exe -X utf8 -m core.finance add income 69 "爬虫定制单" --category 服务收入 --source 闲鱼',
        r'.\.venv\Scripts\python.exe -X utf8 -m core.finance add expense 15.9 "生图API费" --category API费用',
        r'.\.venv\Scripts\python.exe -X utf8 -m core.finance summary',
    ], note="成单后让 agent 自动记一笔；summary 返回 JSON 可直接被 agent 解析。项目内置 skill：opc-worklog")

st.divider()
st.markdown("### 近 30 天流水")
records = finance.list_records(30)
if records:
    table = ["| 日期 | 类型 | 金额 | 分类 | 备注 | 来源 |", "|---|---|---|---|---|---|"]
    for r in records:
        icon = "🟢 收入" if r["type"] == "income" else "🔴 支出"
        table.append(f"| {r['date']} | {icon} | ¥{r['amount']} | {r['category']} "
                     f"| {r['note']} | {r['source']} |")
    st.markdown("\n".join(table))
else:
    st.caption("还没有流水。开张卖出去第一单，记得回来记账 😉")

if s["by_category"]:
    with st.expander("📊 分类明细"):
        cat_lines = ["| 分类 | 净额 |", "|---|---|"]
        for cat, v in sorted(s["by_category"].items(), key=lambda x: -abs(x[1])):
            cat_lines.append(f"| {cat} | ¥{v:+.1f} |")
        st.markdown("\n".join(cat_lines))
