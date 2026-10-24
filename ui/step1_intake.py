"""Step1 引导表单：角色大类 + 一句话技能（带灵感按钮）+ 可选案例。"""
from __future__ import annotations

import random

import streamlit as st

ROLES = ["技术开发", "设计创意", "文案写作", "咨询服务", "手艺定制"]

ROLE_EMOJI = {"技术开发": "🧑‍💻", "设计创意": "🎨", "文案写作": "✍️",
              "咨询服务": "🧠", "手艺定制": "🛠️"}

# 灵感库：覆盖五类角色，点「来点灵感」随机填入
INSPIRATIONS = [
    "帮人写 Python 爬虫脚本，数据采集自动化，3 天交付",
    "帮留学生改英文简历，24 小时出稿，猎头视角逐句打磨",
    "把丑 PPT 改成高级感汇报页，职场汇报/竞标路演都接",
    "帮小店主做 AI 数字人短视频，一周五条发抖音",
    "代写婚礼誓言/主持稿，泪点拉满不尴尬",
    "帮人搭建家庭 NAS 影音库，远程手把手装好",
    "宠物手绘头像定制，照片转插画 48 小时出图",
    "帮中学生做升学规划咨询，一线教师视角",
    "Excel 表格自动化改造，杂乱台账变一键报表",
    "小红书账号代起步：定位+20篇选题+首月陪跑",
]


def render() -> None:
    st.markdown("## 第 1 步 · 你会什么？")
    st.caption("不用想怎么写得好，大白话说清楚就行，AI 帮你包装")

    # widget 用独立 key（w_ 前缀），流转时复制到手动管理的 key：
    # Streamlit 会在 widget 不再渲染时清掉其 key 对应的 session_state
    if "w_skill" not in st.session_state:
        st.session_state.w_skill = st.session_state.skill
    if "w_case" not in st.session_state:
        st.session_state.w_case = st.session_state.case

    # 角色大类（卡片式单选）
    st.markdown("**先选一个最接近的角色大类**")
    cols = st.columns(5)
    for i, role in enumerate(ROLES):
        with cols[i]:
            if st.button(f"{ROLE_EMOJI[role]}\n{role}", key=f"role_{i}",
                         use_container_width=True,
                         type="primary" if st.session_state.role == role else "secondary"):
                st.session_state.role = role
                st.rerun()
    if st.session_state.role:
        st.markdown(f"已选择：**{ROLE_EMOJI[st.session_state.role]} {st.session_state.role}**")

    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

    # 一句话技能 + 灵感按钮
    skill_col, btn_col = st.columns([4.2, 1])
    with skill_col:
        st.markdown("**用一句话说说你的技能**（卖什么、给谁、多久交付）")
    with btn_col:
        st.markdown("<div style='height:1.1rem'></div>", unsafe_allow_html=True)
        if st.button("🎲 来点灵感", use_container_width=True):
            st.session_state.w_skill = random.choice(INSPIRATIONS)
            st.rerun()
    st.text_area("技能描述", key="w_skill", height=90,
                 placeholder="例：帮人写爬虫脚本，数据采集自动化，3 天交付",
                 label_visibility="collapsed")

    # 可选案例
    with st.expander("➕ 有案例/作品更好（可选）"):
        st.text_area("补充案例", key="w_case", height=70,
                     placeholder="例：曾帮电商客户采集 10 万条竞品数据 / 做过 30+ 份求职简历",
                     label_visibility="collapsed")

    col1, col2, _ = st.columns([1, 1, 3])
    with col1:
        if st.button("← 回工作台", use_container_width=True):
            st.session_state.skill = st.session_state.w_skill.strip()
            st.session_state.case = st.session_state.w_case.strip()
            st.session_state.step = "intake"
            st.switch_page("ui/home.py")
    with col2:
        if st.button("下一步 →", type="primary", use_container_width=True):
            if not st.session_state.role:
                st.warning("先选一个角色大类")
                st.stop()
            if len(st.session_state.w_skill.strip()) < 8:
                st.warning("技能描述太短啦，至少 8 个字，说清卖什么")
                st.stop()
            # 关键：在 widget 消失前把值复制到手动管理的 key
            st.session_state.skill = st.session_state.w_skill.strip()
            st.session_state.case = st.session_state.w_case.strip()
            st.session_state.step = "select"
            st.rerun()
