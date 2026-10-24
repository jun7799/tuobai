"""Step0 欢迎页：流程图 + 示例角色卡 + 进入向导。"""
from __future__ import annotations

import json

import streamlit as st

from config import settings

EXAMPLE_ROLES = [
    {"slug": "crawler_engineer", "emoji": "🕷️", "name": "爬虫工程师",
     "skill": "帮人写 Python 爬虫脚本，数据采集自动化，3 天交付",
     "color": "#2563EB"},
    {"slug": "ppt_designer", "emoji": "🎨", "name": "PPT 设计师",
     "skill": "帮人把丑 PPT 做成高级感汇报页，职场汇报/竞标路演都接",
     "color": "#DB2777"},
    {"slug": "resume_coach", "emoji": "📄", "name": "简历优化师",
     "skill": "帮求职者改简历，24 小时出稿，猎头视角逐句打磨",
     "color": "#059669"},
]


def render() -> None:
    st.markdown('<p class="big-title">一个人，也是一家公司</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">有技能却不知道怎么卖？输入一句话，开张机 2 分钟帮你生成全套开张装备，'
                '并且真的挂上闲鱼。</p>', unsafe_allow_html=True)

    # 流程图
    cols = st.columns([1, 0.3, 1, 0.3, 1, 0.3, 1])
    steps = [("💬", "说技能", "一句话说清你会什么"),
             ("📦", "出装备", "服务卡/文案/主图/话术"),
             ("🐟", "挂闲鱼", "真实上架，不是截图"),
             ("📕", "发小红书", "推广卡片一键渲染")]
    for i, (emoji, title, desc) in enumerate(steps):
        with cols[i * 2]:
            st.markdown(f"""
            <div class="role-card" style="text-align:center">
              <div style="font-size:2rem">{emoji}</div>
              <div style="font-weight:700;font-size:1.05rem;margin:.3rem 0">{title}</div>
              <div style="color:#888;font-size:.85rem">{desc}</div>
            </div>""", unsafe_allow_html=True)
        if i < 3:
            with cols[i * 2 + 1]:
                st.markdown('<div style="text-align:center;font-size:1.4rem;color:#FF6B35;'
                            'margin-top:1.6rem">→</div>', unsafe_allow_html=True)

    st.markdown("### 看看别人是怎么开张的")
    st.caption("点击任意角色，直接查看已生成的全套开张装备")

    cards = st.columns(3)
    for i, role in enumerate(EXAMPLE_ROLES):
        with cards[i]:
            example_dir = settings.examples_dir / role["slug"]
            has_output = (example_dir / "package.json").exists()
            st.markdown(f"""
            <div class="role-card">
              <div style="font-size:1.8rem">{role['emoji']}</div>
              <div style="font-weight:700;font-size:1.1rem;margin:.3rem 0">{role['name']}</div>
              <div style="color:#666;font-size:.85rem;line-height:1.5">{role['skill']}</div>
              <div style="margin-top:.6rem;font-size:.78rem;color:{'#059669' if has_output else '#999'}">
                {'✅ 已生成全套装备' if has_output else '⏳ 待预生成'}
              </div>
            </div>""", unsafe_allow_html=True)
            if has_output and st.button(f"查看「{role['name']}」的成果", key=f"ex_{role['slug']}",
                                        use_container_width=True):
                st.session_state.out_dir = str(example_dir)
                st.session_state.demo_mode = True
                st.session_state.step = "result"
                st.rerun()

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    if st.button("🚀 用我自己的技能开张（2 分钟）", type="primary", use_container_width=True):
        st.session_state.step = "intake"
        st.rerun()
