"""找方向：AI 对话挖掘技能与定位，沉淀用户画像，可一键带去开张。"""
from __future__ import annotations

import json

import streamlit as st

from core import llm_client, profile as profile_store

SYSTEM = """你是「托摆」的方向顾问，帮用户找到可以变现的技能方向。风格要求：
- 口语化、接地气，像懂行的朋友聊天，每次回复不超过 150 字
- 多问少说教：一次只问一个问题，顺着用户的回答深挖
- 重点挖掘：职业背景、擅长的事、别人找他帮过什么忙、愿意为什么花钱（反向找需求）
- 用户方向模糊时，给 2-3 个具体可卖的方向选项让他挑，每个都带"卖什么/卖给谁/大概定价"
- 方向清晰后，帮他收敛成一句话：「帮【谁】做【什么】，【多久交付】，定价【多少】」
- 不输出 markdown 标题，纯对话"""

st.markdown("## 💬 找方向")
st.caption("和 AI 聊聊你的背景和擅长的事，一起找到能变现的技能方向。聊完点下方按钮沉淀画像。")

p = profile_store.load_profile()
if profile_store.profile_filled():
    with st.expander(f"当前画像：{p['name'] or '已保存'}（点击展开/更新）"):
        st.markdown(f"**背景**：{p['background'] or '—'}\n\n"
                    f"**擅长**：{'、'.join(p['strengths']) or '—'}\n\n"
                    f"**方向**：{p['direction'] or '—'}")

history = st.session_state.chat_history
if not history:
    opener = ("嗨！我是一人公司方向顾问 👋 咱们聊几句，我帮你找到能变现的方向。"
              "先从最简单的开始：你现在是做什么工作的？平时最擅长哪类事？")
    history.append({"role": "assistant", "content": opener})
    st.session_state.chat_history = history

for msg in history:
    with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "🧑"):
        st.markdown(msg["content"])

if prompt := st.chat_input("说说你的背景/擅长/想做点什么…"):
    history.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)
    with st.chat_message("assistant", avatar="🤖"):
        try:
            reply = llm_client.chat_text(
                SYSTEM,
                "\n".join(f"[{m['role']}] {m['content']}" for m in history[-16:]),
                temperature=0.8,
            )
        except llm_client.LLMError as e:
            reply = f"（网络开小差了：{e} 请再发一次）"
        st.markdown(reply)
    history.append({"role": "assistant", "content": reply})
    st.rerun()

# ---------- 底部动作 ----------
st.divider()

# ---------- 技能拆解：画像 → 可上架服务清单 → 一键上架 ----------
st.markdown("### 🎯 拆解我的可上架技能")
st.caption("方向定了以后，AI 帮你拆成几个具体能卖的服务——选一个，直接去上架")

if st.button("🤖 AI 拆解可上架技能", use_container_width=True,
             disabled=not profile_store.profile_filled()):
    with st.status("AI 拆解中…（结合你的画像和擅长）"):
        try:
            ideas = llm_client.chat_json(
                "你是一人公司服务设计师，只输出 JSON，不要围栏。",
                f"用户画像：{json.dumps(p, ensure_ascii=False)}\n\n"
                "基于画像拆解出 4 个适合在闲鱼上架的具体服务。要求："
                "每个都能独立交付、需求明确、一周内能接单。输出："
                '{"ideas":[{"name":"服务名2-6字","one_liner":"帮谁做什么+交付周期，≤20字",'
                '"price_low":39,"price_high":99,"role":"技术开发/设计创意/文案写作/咨询服务/手艺定制 选一",'
                '"why":"为什么适合他，≤20字"}]}')
            st.session_state["_skill_ideas"] = ideas.get("ideas", [])
        except llm_client.LLMError as e:
            st.error(f"拆解失败：{e}")

if "_skill_ideas" in st.session_state and st.session_state["_skill_ideas"]:
    for i, idea in enumerate(st.session_state["_skill_ideas"][:4]):
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{idea.get('name', '未命名')}** · "
                            f"¥{idea.get('price_low', '?')}-{idea.get('price_high', '?')}")
                st.caption(f"{idea.get('one_liner', '')}｜{idea.get('why', '')}")
            with col2:
                if st.button("🐟 去上架", key=f"idea_{i}", use_container_width=True):
                    st.session_state.role = idea.get("role") or "技术开发"
                    st.session_state.skill = (f"{idea.get('one_liner', '')}"
                                              f"，定价参考 ¥{idea.get('price_low', '')}")
                    # 同时写 widget key，保证表单预填一定生效
                    st.session_state.w_skill = st.session_state.skill
                    st.session_state.step = "intake"
                    st.switch_page("ui/launch.py")

st.divider()
c1, c2 = st.columns(2)
with c1:
    if st.button("📝 把这轮聊天沉淀成我的画像", use_container_width=True,
                 disabled=len([m for m in history if m["role"] == "user"]) < 2):
        with st.spinner("AI 正在提炼你的画像…"):
            try:
                profile = llm_client.chat_json(
                    "你从对话中提炼用户画像，只输出 JSON，不要围栏。",
                    "对话记录：\n" + "\n".join(
                        f"[{m['role']}] {m['content']}" for m in history
                    ) + "\n\n输出格式："
                    '{"name":"昵称或代称","background":"职业背景一句话",'
                    '"strengths":["擅长点3-5个"],"direction":"最适合的变现方向一句话（帮谁做什么/定价多少）",'
                    '"services":["建议先卖的服务2-3个"]}',
                )
                profile_store.save_profile(profile)
                st.success("画像已保存！名片/同行分析/简历都会用它")
                st.rerun()
            except llm_client.LLMError as e:
                st.error(f"提炼失败：{e}")
with c2:
    if st.button("🐟 带着方向去开张", type="primary", use_container_width=True,
                 disabled=not p.get("direction")):
        st.session_state.skill = p["direction"]
        st.session_state.step = "intake"
        st.switch_page("ui/launch.py")
