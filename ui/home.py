"""工作台首页：画像卡 + 数据概览 + 已开张服务 + 模块导航 + 示例入口。"""
from __future__ import annotations

import json

import streamlit as st

from config import PROJECT_ROOT, settings
from core import profile as profile_store

# Hero：品牌 logo + 主张（logo 是品牌印章，标题是钩子）
_hero_l, _hero_r = st.columns([1, 5], vertical_alignment="center")
with _hero_l:
    st.image(str(PROJECT_ROOT / "assets" / "logo.png"), width=130)
with _hero_r:
    st.markdown(
        '<div style="display:flex;align-items:flex-end;gap:14px">'
        '<p class="big-title" style="margin:0">托摆<span class="stamp"> · </span>'
        '把技能摆到路边去<span class="stamp">。</span></p>'
        '<span class="seal-stamp">开张</span></div>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">把技能托付给 AI，替你摆到路边——2 分钟上架服务到闲鱼，'
                '记账、日志、商机全部 AI 代办，你的 agent 也能替你经营。</p>',
                unsafe_allow_html=True)

# ---------- 画像卡 ----------
p = profile_store.load_profile()
if profile_store.profile_filled():
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"### 👤 {p['name'] or '一位手艺人'}")
        if p["background"]:
            st.markdown(f"**背景**：{p['background']}")
        if p["strengths"]:
            st.markdown("**擅长**：" + "、".join(p["strengths"]))
        if p["direction"]:
            st.markdown(f"**方向**：{p['direction']}")
    with c2:
        st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)
        if st.button("💬 继续聊，更新画像", use_container_width=True):
            st.switch_page("ui/explore.py")
else:
    st.info("👋 先和 AI 聊几句——说说你的职业背景、擅长什么、想往哪个方向做。"
            "聊完后，画像会贯穿整个工作台（名片、同行分析、简历都会用它）", icon="💡")
    if st.button("💬 去聊聊，找到我的方向", type="primary", use_container_width=True):
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
m4.metric("名片", "已生成" if (PROJECT_ROOT / "data" / "brand").exists() else "未生成")

st.divider()

# ---------- 模块导航 ----------
st.markdown("### 开始经营")
mods = st.columns(8)
MODULES = [
    ("ui/explore.py", "💬", "找方向", "聊出技能与定位"),
    ("ui/market.py", "🕵️", "看同行", "真实抓闲鱼同行"),
    ("ui/brand.py", "📇", "立人设", "聊出人设+名片"),
    ("ui/leads.py", "🤝", "攒客户", "商机+AI报价"),
    ("ui/launch.py", "🐟", "上架服务", "一句话真实上架"),
    ("ui/promote.py", "📣", "推广服务", "小红书+公众号"),
    ("ui/finance.py", "💰", "记账", "三入口记账"),
    ("ui/worklog.py", "📝", "工作日志", "总结+回顾上云"),
]
for i, (page, emoji, name, desc) in enumerate(MODULES):
    with mods[i]:
        st.markdown(f"""
        <div class="module-card" style="text-align:center">
          <div style="font-size:1.8rem">{emoji}</div>
          <div style="font-weight:700;margin:.3rem 0">{name}</div>
          <div style="color:#888;font-size:.72rem">{desc}</div>
        </div>""", unsafe_allow_html=True)
        if st.button(name, key=f"nav_{page}", use_container_width=True):
            st.switch_page(page)

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
    cols = st.columns(min(len(all_cards), 3))
    for i, (dirname, pkg, d, demo) in enumerate(all_cards[:6]):
        with cols[i % 3]:
            pos = pkg.get("positioning", {})
            img = d / "xianyu_main.png"
            if img.exists():
                st.image(str(img))
            else:
                st.markdown(
                    '<div style="background:var(--accent-soft,#FFF7ED);border-radius:10px;'
                    'height:120px;display:flex;align-items:center;justify-content:center;'
                    'color:#C2410C;font-weight:600">🏪 开张装备生成中</div>',
                    unsafe_allow_html=True)
            tag = "📦 示例" if demo else "🐟"
            st.markdown(f"**{tag} {pos.get('name', dirname)}**")
            st.caption(pos.get("one_liner", "")[:40])
            if st.button("查看成果", key=f"run_{dirname}", use_container_width=True):
                st.session_state.out_dir = str(d)
                st.session_state.demo_mode = demo
                st.session_state.step = "result"
                st.switch_page("ui/launch.py")
