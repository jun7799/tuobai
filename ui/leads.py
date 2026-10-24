"""攒客户：轻 CRM——商机登记（表单/跟AI说）+ 阶段统计 + AI 报价助手（注入真实行情）。"""
from __future__ import annotations

import time
import uuid
from pathlib import Path

import streamlit as st

from core import llm_client, profile as profile_store
from ui.components import chat_assistant, cli_card

STAGES = ["线索", "沟通中", "已报价", "已成交", "已流失"]

st.markdown("## 🤝 攒客户")
st.caption("把每一个来问价的人都记下来——一人公司的客户资产，从第一条线索开始")

leads = profile_store.load_leads()

# 指标卡
c1, c2, c3, c4 = st.columns(4)
c1.metric("总商机", len(leads))
active = [l for l in leads if l.get("stage") in ("线索", "沟通中", "已报价")]
c2.metric("进行中", len(active))
won = [l for l in leads if l.get("stage") == "已成交"]
c3.metric("已成交", len(won), f"¥{sum(l.get('amount', 0) for l in won):.0f}")
c4.metric("意向金额", f"¥{sum(l.get('amount', 0) for l in active):.0f}")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["📝 手动录", "💬 跟阿托说", "🤖 其他 agent 录",
                                  "💡 AI 报价助手"])

with tab1:
    with st.form("lead_form", border=True):
        st.markdown("**新商机**")
        col1, col2 = st.columns(2)
        with col1:
            l_name = st.text_input("客户/称呼", key="ld_name", placeholder="例：宠物店王老板")
            l_source = st.selectbox("来源", ["闲鱼", "小红书", "朋友介绍", "名片分享", "其他"],
                                    key="ld_source")
        with col2:
            l_amount = st.number_input("意向金额（元）", min_value=0.0, key="ld_amount", step=10.0)
            l_stage = st.selectbox("阶段", STAGES, key="ld_stage",
                                   index=STAGES.index("线索"))
        l_need = st.text_area("需求描述", key="ld_need", height=70,
                              placeholder="例：想要店铺海报，每月 5 张")
        submitted = st.form_submit_button("➕ 登记", type="primary", use_container_width=True)
    if submitted:
        if not l_name.strip():
            st.warning("客户称呼不能为空")
        else:
            leads.append({
                "id": uuid.uuid4().hex[:8],
                "name": l_name.strip(), "source": l_source, "need": l_need.strip(),
                "stage": l_stage, "amount": float(l_amount),
                "created_at": time.strftime("%Y-%m-%d %H:%M"),
                "updated_at": time.strftime("%Y-%m-%d"),
            })
            profile_store.save_leads(leads)
            st.toast(f"已登记：{l_name}（{l_stage}）")
            st.rerun()

    if leads:
        st.markdown("**商机列表**（下拉改阶段，自动保存）")
        for lead in sorted(leads, key=lambda x: x.get("created_at", ""), reverse=True):
            col1, col2, col3 = st.columns([3, 1.2, 1])
            with col1:
                icon = {"已成交": "🟢", "已流失": "⚫"}.get(lead["stage"], "🔵")
                st.markdown(f"{icon} **{lead['name']}** · {lead.get('source', '')} · "
                            f"¥{lead.get('amount', 0):.0f}")
                if lead.get("need"):
                    st.caption(lead["need"][:50])
            with col2:
                new_stage = st.selectbox("阶段", STAGES, index=STAGES.index(lead["stage"]),
                                         key=f"stage_{lead['id']}", label_visibility="collapsed")
                if new_stage != lead["stage"]:
                    lead["stage"] = new_stage
                    lead["updated_at"] = time.strftime("%Y-%m-%d")
                    profile_store.save_leads(leads)
                    st.toast(f"{lead['name']} → {new_stage}" +
                             ("（记得去记账页记一笔！）" if new_stage == "已成交" else ""))
                    st.rerun()
            with col3:
                if st.button("🗑", key=f"del_{lead['id']}", help="删除"):
                    leads = [x for x in leads if x["id"] != lead["id"]]
                    profile_store.save_leads(leads)
                    st.rerun()

with tab2:
    def _preview_lead(d: dict) -> None:
        st.markdown(f"👤 **{d.get('name','?')}** · {d.get('source','')} · "
                    f"{d.get('stage','线索')} · ¥{d.get('amount', 0)}")
        if d.get("need"):
            st.caption(d["need"])

    def _save_lead(d: dict) -> None:
        leads2 = profile_store.load_leads()
        leads2.append({
            "id": uuid.uuid4().hex[:8],
            "name": d.get("name", "未命名"), "source": d.get("source", "其他"),
            "need": d.get("need", ""), "stage": d.get("stage", "线索"),
            "amount": float(d.get("amount", 0) or 0),
            "created_at": time.strftime("%Y-%m-%d %H:%M"),
            "updated_at": time.strftime("%Y-%m-%d"),
        })
        profile_store.save_leads(leads2)

    chat_assistant(
        "leads",
        hint="例：宠物店王老板私信问海报，想要每月5张，预算300左右",
        extract_format=('{"name":"客户称呼","source":"闲鱼/小红书/朋友介绍/名片分享/其他 选一",'
                        '"need":"需求描述一句话","stage":"线索/沟通中/已报价/已成交/已流失 选一",'
                        '"amount":数字意向金额}'),
        preview=_preview_lead,
        on_confirm=_save_lead,
    )

with tab3:
    cli_card("给其他 agent 的商机入口", [
        "# 录入商机（客户来问价就记一条）",
        r'.\.venv\Scripts\python.exe -X utf8 -m core.leads add "宠物店王老板" --source 闲鱼 --need "每月5张海报" --amount 300',
        "",
        "# 成交后更新阶段（id 从 add 返回或 list 查）",
        r'.\.venv\Scripts\python.exe -X utf8 -m core.leads set-stage abc12345 已成交',
        "",
        "# 成交记得顺手记账（商机和账本串起来）",
        r'.\.venv\Scripts\python.exe -X utf8 -m core.finance add income 300 "海报月单" --category 服务收入 --source 闲鱼',
    ], note="add 返回记录 id；list 可查全部商机。")

with tab4:
    st.markdown("**客户问「这个多少钱」，把需求丢给阿托**")
    need_desc = st.text_area("客户需求描述", key="qt_need", height=90,
                             placeholder="例：宠物店想要每月5张海报，长期合作，预算不多")
    if st.button("💡 AI 估价 + 生成应答话术", type="primary", use_container_width=True):
        if len(need_desc.strip()) < 8:
            st.warning("先把客户的需求多写几个字（至少 8 个字），AI 才好估价")
            st.stop()
        with st.status("估价中…"):
            try:
                # 数据飞轮：注入看同行抓到的真实行情（若有）
                market_ctx = ""
                market_dir = Path(__file__).parent.parent / "data"
                reports = sorted(market_dir.glob("market_*.md"),
                                 key=lambda x: x.stat().st_mtime, reverse=True)
                if reports:
                    market_ctx = ("\n\n真实同行情报（来自闲鱼抓取，报价请参考此行情）：\n"
                                  + reports[0].read_text(encoding="utf-8")[:1200])
                r = llm_client.chat_json(
                    "你是一人公司定价顾问，只输出 JSON。报价必须参考提供的真实行情，"
                    "在 suggest 里点出行情依据。",
                    f"客户需求：{need_desc}{market_ctx}\n\n输出："
                    '{"price_low": 0, "price_high": 0, "suggest": "建议报价一句话含数字和理由",'
                    '"reply": "发给客户的应答话术，100字内，先确认需求再报价，留有余地"}')
                st.session_state["_quote"] = r
                st.session_state["_quote_has_market"] = bool(market_ctx)
            except llm_client.LLMError as e:
                st.error(f"估价失败：{e}")
    if "_quote" in st.session_state:
        q = st.session_state["_quote"]
        if st.session_state.get("_quote_has_market"):
            st.caption("📎 本次报价已参考「看同行」抓取的真实闲鱼行情")
        m1, m2 = st.columns(2)
        m1.metric("估价下限", f"¥{q.get('price_low', '?')}")
        m2.metric("估价上限", f"¥{q.get('price_high', '?')}")
        st.markdown(f"**💡 建议**：{q.get('suggest', '')}")
        st.markdown("**💬 应答话术**（复制即发）")
        st.code(q.get("reply", ""), language=None)
