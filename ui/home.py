"""工作台首页：画像卡 + 数据概览 + 已开张服务 + 模块导航 + 示例入口。"""
from __future__ import annotations

import json

import streamlit as st

from config import PROJECT_ROOT, settings
from core import profile as profile_store

# Hero：品牌 logo + 主张（左对齐；logo 是品牌印章，标题是钩子）
_hero_l, _hero_r = st.columns([1, 5], vertical_alignment="center")
with _hero_l:
    st.image(str(PROJECT_ROOT / "assets" / "logo.png"), width=120)
with _hero_r:
    st.markdown(
        '<div style="display:flex;align-items:flex-end;gap:16px;flex-wrap:wrap">'
        '<p class="big-title">托摆<span class="stamp"> · </span>'
        '把技能摆到路边去<span class="stamp">。</span></p>'
        '<span class="seal-stamp">开张</span></div>'
        '<p class="sub-title">把技能托付给 AI，替你摆到路边——2 分钟上架服务到闲鱼，'
        '记账、日志、商机全部 AI 代办，你的 agent 也能替你经营。</p>',
        unsafe_allow_html=True)

# ---------- 画像卡 ----------
p = profile_store.load_profile()
if profile_store.profile_filled():
    c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
    with c1:
        st.markdown(f"### 👤 {p['name'] or '一位手艺人'}")
        if p["background"]:
            st.markdown(f"**背景**：{p['background']}")
        if p["strengths"]:
            st.markdown("**擅长**：" + "、".join(p["strengths"]))
        if p["direction"]:
            st.markdown(f"**方向**：{p['direction']}")
    with c2:
        if st.button("继续聊，更新画像", use_container_width=True):
            st.switch_page("ui/explore.py")
else:
    st.info("先和 AI 聊几句——说说你的职业背景、擅长什么、想往哪个方向做。"
            "聊完后，画像会贯穿整个工作台（名片、同行分析、简历都会用它）", icon="💡")
    if st.button("去聊聊，找到我的方向", type="primary"):
        st.switch_page("ui/explore.py")

st.divider()

# ---------- 数据概览 ----------
def _count_runs() -> tuple[int, int]:
    """(已开张服务数, 在线闲鱼商品数)。"""
    runs, online = 0, 0
    if settings.output_dir.exists():
        for d in settings.output_dir.iterdir():
            if (d / "package.json").exists():
                runs += 1
                sp = d / "state.json"
                if sp.exists():
                    try:
                        if json.loads(sp.read_text(encoding="utf-8")).get("xianyu_item_id"):
                            online += 1
                    except json.JSONDecodeError:
                        pass
    return runs, online


runs, online = _count_runs()
leads = profile_store.load_leads()
m1, m2, m3, m4 = st.columns(4)
m1.metric("已开张服务", runs)
m2.metric("闲鱼在线商品", online)
m3.metric("客户商机", len(leads))
m4.metric("名片", "1 张" if (PROJECT_ROOT / "data" / "brand" / "card.png").exists() else "0 张")

st.divider()

# ---------- 模块导航 ----------
st.markdown("### 开始经营")
MODULES = [
    ("ui/explore.py", "🧭", "找方向", "聊出技能与定位"),
    ("ui/market.py", "🕵️", "看同行", "真实抓闲鱼同行"),
    ("ui/brand.py", "📇", "立人设", "聊出人设与名片"),
    ("ui/leads.py", "🤝", "攒客户", "商机与 AI 报价"),
    ("ui/launch.py", "🐟", "上架服务", "一句话真实上架"),
    ("ui/promote.py", "📣", "推广服务", "小红书与公众号"),
    ("ui/finance.py", "💰", "记账", "三入口记账"),
    ("ui/worklog.py", "📝", "工作日志", "总结与回顾上云"),
]
for row in (MODULES[:4], MODULES[4:]):
    cols = st.columns(4)
    for col, (page, emoji, name, desc) in zip(cols, row):
        with col:
            # 整卡可点：卡内放一个透明按钮铺满容器（见 app.py 的 nav_ 样式）
            with st.container(border=True, key=f"nav_{page.split('/')[-1][:-3]}"):
                st.markdown(
                    f'<div class="nav-card"><div style="font-size:1.6rem;line-height:1">{emoji}</div>'
                    f'<div class="nm" style="margin-top:.5rem">{name}</div>'
                    f'<div class="ds">{desc}</div></div>', unsafe_allow_html=True)
                if st.button(name, key=f"navbtn_{page}"):
                    st.switch_page(page)

st.divider()

# ---------- 我的已开张服务 ----------
def _service_cards(base: Path, demo: bool) -> list[tuple[str, dict, Path, bool]]:
    cards = []
    if not base.exists():
        return cards
    for d in sorted(base.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        pkg_p = d / "package.json"
        if pkg_p.exists():
            try:
                pkg = json.loads(pkg_p.read_text(encoding="utf-8"))
                cards.append((d.name, pkg, d, demo))
            except json.JSONDecodeError:
                continue
    return cards


all_cards = _service_cards(settings.output_dir, False) + \
    _service_cards(settings.examples_dir, True)
if all_cards:
    st.markdown("### 我的已开张服务")
    shown = all_cards[:6]
    for r in range(0, len(shown), 3):
        with st.container(key=f"svcrow_{r}"):
            cols = st.columns(3)
            for j, (dirname, pkg, d, demo) in enumerate(shown[r:r + 3]):
                with cols[j], st.container(key=f"svc_{r + j}"):
                    pos = pkg.get("positioning", {})
                    img = d / "xianyu_main.png"
                    if img.exists():
                        st.image(str(img))
                    else:
                        st.markdown(
                            '<div style="background:var(--accent-soft);border-radius:10px;'
                            'height:120px;display:flex;align-items:center;justify-content:center;'
                            'color:var(--accent-deep);font-weight:600">开张装备生成中</div>',
                            unsafe_allow_html=True)
                    tag = "📦 示例" if demo else "🐟"
                    st.markdown(f"**{tag} {pos.get('name', dirname)}**")
                    st.caption(pos.get("one_liner", "")[:40])
                    if st.button("查看成果", key=f"run_{dirname}", use_container_width=True):
                        st.session_state.out_dir = str(d)
                        st.session_state.demo_mode = demo
                        st.session_state.step = "result"
                        st.switch_page("ui/launch.py")
