"""立人设：个人名片生成（HTML 模板 + playwright 截图）。"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import streamlit as st

from config import PROJECT_ROOT, settings
from core import card_tpl, llm_client, profile as profile_store
from ui.components import chat_assistant

st.markdown("## 📇 立人设")
st.caption("生成一张可分享的个人名片：发朋友圈、贴社群、当微信头图。服务列表自动带入你已开张的服务。")

p = profile_store.load_profile()

# ---------- 跟 AI 聊出人设（自动填表单） ----------
def _preview_brand(d: dict) -> None:
    st.markdown(f"{d.get('emoji','🛠️')} **{d.get('name','?')}**")
    st.markdown(f"「{d.get('tagline','')}」")
    st.caption("擅长：" + "、".join(d.get("strengths", [])))

def _save_brand(d: dict) -> None:
    st.session_state.bd_name = d.get("name", "")
    st.session_state.bd_emoji = d.get("emoji", "🛠️")
    st.session_state.bd_tagline = d.get("tagline", "")
    st.session_state.bd_str = "、".join(d.get("strengths", []))
    # 同步进画像
    profile = dict(p)
    profile.setdefault("strengths", [])
    if d.get("name"):
        profile["name"] = d["name"]
    if d.get("tagline"):
        profile["direction"] = d["tagline"]
    profile_store.save_profile(profile)

chat_assistant(
    "brand",
    hint="例：我叫俊哥，程序员出身，最擅长Python自动化和爬虫，想帮小店主做提效工具",
    extract_format=('{"name":"昵称","emoji":"一个代表emoji","tagline":"一句话介绍≤24字有记忆点",'
                    '"strengths":["擅长标签2-5个，每个≤6字"]}'),
    preview=_preview_brand,
    on_confirm=_save_brand,
)
st.divider()

# 服务候选：已开张的服务自动带入
services_pool: list[dict] = []
out_dir_root = settings.output_dir
if out_dir_root.exists():
    for d in sorted(out_dir_root.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        pkg_p = d / "package.json"
        if pkg_p.exists() and len(services_pool) < 4:
            try:
                pkg = json.loads(pkg_p.read_text(encoding="utf-8"))
                pos = pkg["positioning"]
                services_pool.append({"name": pos.get("name", ""),
                                      "desc": pos.get("one_liner", ""),
                                      "price": next((t.get("price") for t in pos.get("tiers", [])), "")})
            except (json.JSONDecodeError, KeyError):
                continue
for s in p.get("services", []):
    if isinstance(s, str) and len(services_pool) < 4:
        services_pool.append({"name": s, "desc": "", "price": ""})

# 表单（预填）
left, right = st.columns([2, 1], gap="large")
with left:
    name = st.text_input("昵称/署名", value=p.get("name", "") or "", key="bd_name",
                         placeholder="例：俊哥")
    emoji = st.text_input("代表 emoji", value="🛠️", key="bd_emoji", max_chars=4)
    tagline = st.text_area("一句话介绍", value=p.get("direction", "") or "", key="bd_tagline",
                           height=70, placeholder="例：帮小店主用AI提效的技术搭子")
    strengths_raw = st.text_input("擅长标签（逗号分隔）",
                                  value="、".join(p.get("strengths", [])[:5]), key="bd_str",
                                  placeholder="Python自动化, 爬虫, AI工作流")
    contacts = st.text_area("联系方式（每行一条，注意隐私）", key="bd_contact", height=90,
                            placeholder="💬 闲鱼搜：xxx\n📧 you@mail.com")
with right:
    _TPL_LABELS = {"warm": "🌅 暖色手作风", "dark": "🌌 暗色科技风"}
    tpl_name = st.radio("名片风格", ["warm", "dark"],
                        format_func=lambda x: _TPL_LABELS[x],
                        key="bd_tpl")
    st.caption("暖色适合朋友圈与社群，暗色适合技术向头图。")
    if st.button("✨ AI 帮我写介绍", use_container_width=True):
        with st.spinner("AI 起草中…"):
            try:
                r = llm_client.chat_json(
                    "你是个人品牌文案，只输出 JSON。",
                    f"根据画像写名片文案：{json.dumps(p, ensure_ascii=False)}。输出："
                    '{"tagline":"一句话介绍，≤24字，有记忆点",'
                    '"strengths":["标签3-5个，每个≤6字"],"emoji":"一个代表emoji"}')
                st.session_state.bd_tagline = r.get("tagline", "")
                st.session_state.bd_str = "、".join(r.get("strengths", [])) or st.session_state.bd_str
                st.session_state.bd_emoji = r.get("emoji", "") or st.session_state.bd_emoji
                st.rerun()
            except llm_client.LLMError as e:
                st.error(f"AI 起草失败：{e}")

st.caption("自动带入的服务（来自你的开张记录）："
           + ("；".join(s["name"] for s in services_pool) if services_pool else "暂无，先去「上架服务」开一家"))

if st.button("🎨 生成名片", type="primary",
             disabled=not (name.strip() and tagline.strip())):
    strengths = [s.strip() for s in strengths_raw.replace("，", ",").split(",") if s.strip()]
    contact_rows = [c.strip() for c in contacts.splitlines() if c.strip()] or ["💬 详询请私信"]
    svc_cards = [{"name": s["name"] + (f" ¥{s['price']}起" if s.get("price") else ""),
                  "desc": s["desc"]} for s in services_pool] or \
                 [{"name": "咨询服务", "desc": tagline[:30]}]
    html = card_tpl.fill(card_tpl.TEMPLATES[tpl_name], emoji=emoji.strip() or "🛠️",
                         name=name.strip(), tagline=tagline.strip(),
                         strengths=strengths, services=svc_cards, contacts=contact_rows)
    brand_dir = PROJECT_ROOT / "data" / "brand"
    brand_dir.mkdir(parents=True, exist_ok=True)
    html_path = brand_dir / "card.html"
    png_path = brand_dir / "card.png"
    html_path.write_text(html, encoding="utf-8")
    with st.status("渲染名片中（约 5 秒）…"):
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        proc = subprocess.run(  # noqa: S603 本地脚本
            [settings.py_main, str(PROJECT_ROOT / "scripts_render_card.py"),
             str(html_path), str(png_path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env, timeout=60, stdin=subprocess.DEVNULL, cwd=str(brand_dir))
    if png_path.exists():
        st.image(str(png_path), width=420)
        with open(png_path, "rb") as f:
            st.download_button("⬇️ 下载名片 PNG", f, file_name=f"名片_{name}.png",
                               mime="image/png")
        st.toast("名片已生成！首页的「名片」指标已点亮")
    else:
        st.error(f"渲染失败：{((proc.stdout or '')+(proc.stderr or ''))[-300:]}")

# 历史名片
old = PROJECT_ROOT / "data" / "brand" / "card.png"
if old.exists() and "bd_name" in st.session_state and not st.session_state.get("_just_made"):
    st.divider()
    st.markdown("### 当前名片")
    st.image(str(old), width=420)
