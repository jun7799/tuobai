"""Step2 勾装备 + 开跑。"""
from __future__ import annotations

import streamlit as st

EQUIPS = [
    ("package", "📦 服务打包卡", "定价三档/卖点/FAQ/交付标准", True, "恒选，你的服务说明书"),
    ("xianyu", "🐟 闲鱼商品", "标题+描述+AI主图，确认后真实上架", None, "约 +30 秒（含画图）"),
    ("xhs", "📕 小红书推广笔记", "笔记文案+封面/正文卡片渲染", None, "约 +20 秒"),
    ("talk", "💬 接待话术包", "开场白/评论区回复/询价/砍价应对", None, "秒出"),
]


def render() -> None:
    st.markdown("## 第 2 步 · 勾选你的开张装备")
    st.caption(f"角色：{st.session_state.role} ｜ 技能：{st.session_state.skill[:40]}…")

    # 默认全勾：在 widget 创建前预设 session_state（避免 value=+key= 反模式）
    for key, _, _, locked, _ in EQUIPS:
        k = f"sel_{key}"
        if k not in st.session_state:
            st.session_state[k] = True

    for key, name, desc, locked, extra in EQUIPS:
        col1, col2 = st.columns([3.5, 2])
        with col1:
            st.checkbox(f"**{name}** — {desc}", key=f"sel_{key}",
                        disabled=bool(locked))
        with col2:
            st.caption(extra)

    st.info("全选约 1.5 分钟。闲鱼上架在生成后需要你手动确认，不会偷偷发货 😉", icon="⏱️")

    col1, col2, _ = st.columns([1, 1.4, 3])
    with col1:
        if st.button("← 上一步", use_container_width=True):
            st.session_state.step = "intake"
            st.rerun()
    with col2:
        if st.button("🔥 开始生成", type="primary", use_container_width=True):
            selected = {
                "xianyu": st.session_state.get("sel_xianyu", False),
                "xhs": st.session_state.get("sel_xhs", False),
                "talk": st.session_state.get("sel_talk", False),
            }
            if not any(selected.values()):
                st.warning("至少勾一件装备")
                st.stop()
            from core.pipeline import GenCtx, make_run_id
            from config import settings
            run_id = make_run_id(st.session_state.skill)
            ctx = GenCtx(run_id=run_id, out_dir=settings.output_dir / run_id,
                         role=st.session_state.role, skill=st.session_state.skill.strip(),
                         case=st.session_state.case.strip(), equip=selected)
            ctx.save_form()
            st.session_state.selected = selected
            st.session_state.run_id = run_id
            st.session_state.out_dir = str(ctx.out_dir)
            st.session_state.step = "generate"
            st.rerun()
