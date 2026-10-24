"""托摆 · 一人公司全生命周期工作台 — Streamlit 入口（多页导航）。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st  # noqa: E402

st.set_page_config(page_title="托摆 · 把技能摆到路边去", page_icon="🛵",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
:root {
    --bg: #FDFCF9; --bg-alt: #F5F2EA; --surface: #FFFFFF;
    --ink: #231A10; --ink-2: #5A4E40; --ink-3: #A69C8C;
    --accent: #EA580C; --accent-deep: #C2410C; --accent-soft: #FBEED9;
    --seal-red: #C0391A;
    --line: #EAE6DC; --term: #26180D; --term-ink: #D9CFBB;
    --mono: "JetBrains Mono", "Cascadia Code", Consolas, monospace;
    --serif: "Noto Serif SC", "Source Han Serif SC", "SimSun", serif;
}
/* ---------- 县城诗意：三色装订线 + 纸颗粒（伪元素，全站签名） ---------- */
.stApp::before{content:"";position:fixed;top:0;left:0;right:0;height:4px;z-index:999;
    pointer-events:none;
    background:repeating-linear-gradient(90deg,
      #C0391A 0 60px,#FDFCF9 60px 120px,#2C4F8F 120px 180px);opacity:.6}
.stApp::after{content:"";position:fixed;inset:0;z-index:998;pointer-events:none;
    opacity:.14;mix-blend-mode:multiply;
    background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/%3E%3CfeColorMatrix values='0 0 0 0 .55 0 0 0 0 .47 0 0 0 0 .35 0 0 0 .05 0'/%3E%3C/filter%3E%3Crect width='140' height='140' filter='url(%23n)'/%3E%3C/svg%3E")}
/* ---------- 排版（正文黑体保可用性，大标题衬线给哲学感） ---------- */
html, body, .stApp, p, span, div, input { font-family: -apple-system,
    "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans SC", sans-serif; }
h1 { font-size: 2rem !important; font-weight: 700 !important; color: var(--ink) !important;
     line-height: 1.25 !important; letter-spacing: -0.01em;
     font-family: var(--serif) !important; }
h2 { font-size: 1.35rem !important; font-weight: 700 !important; color: var(--ink) !important;
     font-family: var(--serif) !important; }
h3 { font-size: 1.05rem !important; font-weight: 600 !important; color: var(--ink) !important; }
.big-title { font-size: 2.3rem; font-weight: 700; color: var(--ink);
             line-height: 1.2; letter-spacing: .02em; font-family: var(--serif); }
.big-title .stamp { color: var(--seal-red); }
.sub-title { font-size: 1.02rem; color: var(--ink-2); line-height: 1.6; }
/* 印章：红底竖排小方章 */
.seal-stamp{display:inline-flex;align-items:center;justify-content:center;
    background:var(--seal-red);color:#F5EFDF;font-family:var(--serif);
    font-weight:700;font-size:.82rem;letter-spacing:.2em;
    writing-mode:vertical-rl;border-radius:3px;transform:rotate(-4deg);
    padding:.5em .3em;box-shadow:inset 0 0 0 2px rgba(245,239,223,.4)}
/* 盖章语义：红方点 + 砖红字（已成交/已生成类标记） */
.sealed{color:var(--seal-red) !important}
.sealed::before{content:"";width:.5em;height:.5em;background:var(--seal-red);
    display:inline-block;margin-right:.45em;vertical-align:baseline}
code, .stCode { font-family: var(--mono) !important; }
strong { color: var(--ink); }
/* ---------- 侧边栏 ---------- */
[data-testid="stSidebar"] { background: var(--bg-alt); border-right: 1px solid var(--line); }
[data-testid="stSidebar"] .stButton > button { width: 100%; }
/* ---------- 按钮 ---------- */
.stButton > button[kind="primary"] {
    background: var(--accent); border: 1px solid var(--accent); color: #fff;
    border-radius: 8px; font-weight: 600; transition: background .15s, transform .05s; }
.stButton > button[kind="primary"]:hover { background: var(--accent-deep);
    border-color: var(--accent-deep); }
.stButton > button[kind="primary"]:active { transform: scale(0.97); }
.stButton > button[kind="secondary"] {
    background: var(--surface); border: 1px solid var(--line); color: var(--ink);
    border-radius: 8px; font-weight: 500; transition: border-color .15s; }
.stButton > button[kind="secondary"]:hover { border-color: var(--ink-3); }
/* ---------- Tab ---------- */
[data-testid="stTab"] button { color: var(--ink-2) !important; font-weight: 500; }
[data-testid="stTab"] button:hover { color: var(--ink) !important; }
[data-testid="stTab"][aria-selected="true"] button {
    color: var(--accent) !important; font-weight: 600; }
[data-testid="stTab"][aria-selected="true"] { border-bottom-color: var(--accent) !important; }
/* ---------- 指标卡/Metric ---------- */
[data-testid="stMetricValue"] { font-family: var(--mono); font-weight: 700;
    color: var(--ink); }
[data-testid="stMetricLabel"] { font-size: 0.8rem; color: var(--ink-3) !important; }
/* ---------- 卡片与容器 ---------- */
.module-card {
    border: 1px solid var(--line); border-radius: 10px; padding: 0.9rem 1rem;
    background: var(--surface); height: 100%;
    transition: border-color .15s cubic-bezier(0.23,1,0.32,1); }
.module-card:hover { border-color: var(--accent); }
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 10px; border-color: var(--line) !important; }
/* ---------- 终端块（st.code） ---------- */
[data-testid="stCode"] pre, .stCode pre {
    background: var(--term) !important; color: var(--term-ink) !important;
    border-radius: 10px; font-family: var(--mono) !important; font-size: 0.85rem; }
/* ---------- st.status ---------- */
[data-testid="stStatusWidget"] { border-radius: 10px; border-color: var(--line); }
/* ---------- 表格 ---------- */
[data-testid="stTable"] table, .stTable table { border-color: var(--line); }
[data-testid="stTable"] thead, .stTable thead { background: var(--bg-alt); }
/* ---------- 链接/其他 ---------- */
a { color: var(--accent); }
/* st.info 蓝色提示条 → 暖色系（保持信息语义但不破坏配色） */
[data-testid="stAlert"] { border-radius: 10px; }
[data-testid="stAlert"] info, div[data-baseweb="notification"] {
    background-color: var(--accent-soft) !important;
    border-left: 3px solid var(--accent) !important;
    color: var(--ink-2) !important; }
div[data-baseweb="notification"] svg { fill: var(--accent-deep) !important; }
[data-testid="stChatInput"] textarea { border-radius: 8px; border-color: var(--line); }
::selection { background: var(--accent-soft); color: var(--accent-deep); }
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { transition: none !important; } }
</style>
""", unsafe_allow_html=True)

from config import settings  # noqa: E402
from core import llm_client  # noqa: E402

DEFAULT_STATE = {
    "step": "intake",            # 开张流程内部状态机：intake | select | generate | result
    "role": None, "skill": "", "case": "",
    "selected": {"xianyu": True, "xhs": True, "talk": True},
    "run_id": None, "out_dir": None,
    "demo_mode": False,
    "api_ok": None, "api_msg": "",
    "chat_history": [],          # 找方向对话
}


def ensure_state() -> None:
    for k, v in DEFAULT_STATE.items():
        st.session_state.setdefault(k, v)


def main() -> None:
    ensure_state()

    # 侧边栏顶部：品牌 logo（自定义内容先写，渲染在导航列表上方）
    with st.sidebar:
        _c1, _c2 = st.columns([1, 2.4], vertical_alignment="center")
        with _c1:
            st.image(str(Path(__file__).parent / "assets" / "logo.png"), width=44)
        with _c2:
            st.markdown("**托摆** 把技能摆到路边去")

    # 健康检查（一次会话只测一次）
    if st.session_state.api_ok is None:
        ok, msg = llm_client.healthcheck()
        st.session_state.api_ok, st.session_state.api_msg = ok, msg
    if not st.session_state.api_ok:
        with st.sidebar:
            st.error(st.session_state.api_msg, icon="⚠️")
            st.caption("现场演示可打开示例：工作台首页 → 示例角色卡片")

    pages = {
        "开始": [
            st.Page("ui/home.py", title="工作台", default=True, icon="🏠"),
            st.Page("ui/explore.py", title="找方向", icon="💬"),
            st.Page("ui/market.py", title="看同行", icon="🕵️"),
        ],
        "经营": [
            st.Page("ui/brand.py", title="立人设", icon="📇"),
            st.Page("ui/leads.py", title="攒客户", icon="🤝"),
            st.Page("ui/launch.py", title="上架服务", icon="🐟"),
            st.Page("ui/promote.py", title="推广服务", icon="📣"),
            st.Page("ui/finance.py", title="记账", icon="💰"),
            st.Page("ui/worklog.py", title="工作日志", icon="📝"),
        ],
        "其他": [
            st.Page("ui/shutdown.py", title="关张转职", icon="🚪"),
        ],
    }
    pg = st.navigation(pages)
    pg.run()

    with st.sidebar:
        st.divider()
        st.caption("🛵 托摆 · WaytoAGI 1024 OPC 赛道")
        problems = settings.validate()
        for p in problems:
            st.caption(f"⚙️ {p}")


if __name__ == "__main__":
    main()
