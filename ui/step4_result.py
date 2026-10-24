"""Step4 成果页：瀑布展示全套装备 + 闲鱼确认上架 + 小红书预览 + 话术包 + ZIP。"""
from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

import streamlit as st


def _load() -> tuple[Path, dict | None]:
    out_dir = Path(st.session_state.out_dir)
    pkg_path = out_dir / "package.json"
    pkg = json.loads(pkg_path.read_text(encoding="utf-8")) if pkg_path.exists() else None
    return out_dir, pkg


def render() -> None:
    out_dir, pkg = _load()
    if pkg is None:
        st.error("没有找到生成结果（package.json 缺失）")
        if st.button("← 回工作台"):
            st.session_state.step = "intake"
            st.switch_page("ui/home.py")
        return

    pos = pkg["positioning"]
    st.markdown(f"## 🎉 {pos['name']} · 开张大吉！")
    st.markdown(f"**{pos['one_liner']}**")
    if st.session_state.demo_mode:
        st.info("📦 这是预生成的示例成果（演示模式）", icon="📦")
    st.caption(f"目标客户：{pos.get('target_customer', '')}")

    tab_labels = ["📦 服务卡"]
    if (out_dir / "xianyu_main.png").exists():
        tab_labels.append("🐟 闲鱼商品")
    if (out_dir / "xhs").exists():
        tab_labels.append("📕 小红书笔记")
    if (out_dir / "话术包.md").exists():
        tab_labels.append("💬 接待话术")
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        _render_service_card(out_dir, pkg)

    ti = 1
    if "🐟 闲鱼商品" in tab_labels:
        with tabs[ti]:
            _render_xianyu(out_dir, pkg)
        ti += 1
    if "📕 小红书笔记" in tab_labels:
        with tabs[ti]:
            _render_xhs(out_dir, pkg)
        ti += 1
    if "💬 接待话术" in tab_labels:
        with tabs[ti]:
            _render_talk(out_dir)

    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⬇️ 下载全套装备 (ZIP)", use_container_width=True):
            zip_path = out_dir.parent / f"{out_dir.name}_开张装备.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for p in out_dir.rglob("*"):
                    if p.is_file() and p.suffix in {".png", ".md", ".json"}:
                        zf.write(p, p.relative_to(out_dir))
            with open(zip_path, "rb") as f:
                st.download_button("确认下载", f, file_name=zip_path.name,
                                   mime="application/zip", use_container_width=True)
    with col2:
        if st.button("🏪 再开一家", use_container_width=True):
            for k in ["role", "skill", "case", "run_id", "out_dir", "demo_mode",
                      "step"]:
                st.session_state.pop(k, None)
            st.session_state.step = "intake"
            st.switch_page("ui/home.py")
    with col3:
        st.caption("闲鱼发布需手动确认 · 小红书发布走 skill")


def _render_service_card(out_dir: Path, pkg: dict) -> None:
    pos, card = pkg["positioning"], pkg["service_card"]
    left, right = st.columns([1, 2])
    with left:
        img = out_dir / "xianyu_main.png"
        if img.exists():
            st.image(str(img), caption="AI 生成主图")
    with right:
        st.markdown("#### 定价三档")
        st.markdown("| 档位 | 价格 | 包含 |\n|---|---|---|")
        for t in pos.get("tiers", []):
            st.markdown(f"| {t['name']} | **¥{t['price']}** | {t['includes']} |")
        st.markdown("#### 卖点")
        for h in card.get("highlights", []):
            st.markdown(f"- {h}")
        st.markdown(f"**交付标准**：{card.get('delivery_standard','')}")
        st.markdown(f"**修改政策**：{card.get('revision_policy','')}")
        with st.expander("常见问题 FAQ"):
            for faq in card.get("faq", []):
                st.markdown(f"**Q：{faq['q']}**\n\n{faq['a']}")


def _render_xianyu(out_dir: Path, pkg: dict) -> None:
    from core import xianyu
    xy = pkg["xianyu"]

    st.markdown("#### 👀 发布前预览（改到满意再发）")
    img_col, text_col = st.columns([1, 2])
    with img_col:
        img = out_dir / "xianyu_main.png"
        if img.exists():
            st.image(str(img), caption="主图（AI 生成）")
        extra = out_dir / "xhs" / "cover.png"
        if extra.exists():
            st.image(str(extra), caption="第二图（服务展示）")
    with text_col:
        # 预填：widget 创建前先设 key 初始值（避免 value=+key= 反模式）
        for key, default in [("xy_title", xy["title"]),
                             ("xy_desc", xy["desc"]),
                             ("xy_price", float(xy["price"]))]:
            if key not in st.session_state:
                st.session_state[key] = default
        title = st.text_input("标题（≤30字）", key="xy_title")
        desc = st.text_area("描述", key="xy_desc", height=220)
        price = st.number_input("价格（元）", min_value=1.0, max_value=9999.0, key="xy_price")

        hits = xianyu.precheck(title, desc)
        if hits:
            st.warning(f"文案命中风控词：{hits}", icon="🚨")
            if st.button("🧹 一键修正风控词"):
                t2, d2, log = xianyu.sanitize(title, desc)
                st.session_state.xy_title, st.session_state.xy_desc = t2, d2
                st.toast("；".join(log) or "无可修正")
                st.rerun()
        else:
            st.success("风控预检通过", icon="✅")

    st.divider()
    if st.session_state.demo_mode:
        st.info("演示模式：示例商品的闲鱼链接见 README / 现场演示", icon="📦")
        return

    if st.session_state.get("xy_published_item_id"):
        item_id = st.session_state.xy_published_item_id
        st.success(f"已上架！item_id: {item_id}")
        st.link_button("🔗 打开闲鱼商品页",
                       f"https://www.goofish.com/item?id={item_id}", use_container_width=True)
        with st.expander("📋 保号经营贴士（虚拟服务卖家必读）"):
            st.markdown(
                "- 前 24 小时是初始推荐窗口：**不要改标题、不要降价改标**（会丢流量池权重）\n"
                "- 所有沟通留在闲鱼站内：文案和聊天里**不要出现站外联系方式**（风控词预检已挡一道）\n"
                "- 发布节奏控制：闲鱼写操作限流 **1 件/分钟**，慢慢挂不着急\n"
                "- 买家私信尽快回复：响应速度影响商品权重\n"
                "- 代做类虚拟服务，交付前和买家确认清楚需求范围，避免纠纷")
        return

    wait = xianyu.guard_rate_limit()
    if wait > 0:
        st.caption(f"⏳ 限流保护：距下次可发布约 {wait}s（闲鱼 1 件/分钟）")
    st.warning("⚠️ 发布是不可逆写操作：点下方确认 → 商品将真实出现在你的闲鱼账号", icon="⚠️")
    confirm = st.checkbox("我确认将此商品发布到闲鱼")
    if st.button("🚀 确认上架", type="primary", disabled=not confirm or wait > 0,
                 use_container_width=True):
        images = [p for p in [out_dir / "xianyu_main.png", out_dir / "xhs" / "cover.png"]
                  if p.exists()]
        if not images:
            st.error("缺少商品图片（主图未生成）")
            return
        with st.status("闲鱼上架中…（自动识别类目+传图+发布）", expanded=True) as status:
            result = xianyu.publish_item(title, desc, images, price, timeout=240)
        if result.get("ok"):
            item_id = result.get("item_id")
            state = json.loads((out_dir / "state.json").read_text(encoding="utf-8")) \
                if (out_dir / "state.json").exists() else {}
            state["xianyu_item_id"] = item_id
            (out_dir / "state.json").write_text(
                json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            st.session_state.xy_published_item_id = item_id
            st.rerun()
        else:
            st.error(f"发布失败：{result.get('error', '')}")
            with st.expander("原始返回"):
                st.code(str(result.get("raw", ""))[:800])


def _render_xhs(out_dir: Path, pkg: dict) -> None:
    from core import xhs_card
    xhs_dir = out_dir / "xhs"
    st.markdown(f"#### 笔记：{pkg['xhs'].get('title','')}")

    images = sorted(
        list(xhs_dir.glob("cover*.png")) + list(xhs_dir.glob("card_*.png")),
        key=lambda p: (0 if p.name.startswith("cover") else 1, p.name))
    if images:
        cols = st.columns(min(len(images), 4))
        for i, img in enumerate(images[:4]):
            with cols[i]:
                st.image(str(img), use_container_width=True)

    with st.expander("📝 笔记正文"):
        st.markdown(pkg["xhs"].get("body_md", ""))

    st.markdown("#### 发布到小红书")
    st.caption("面板只负责生成素材，发布走 xhs-note-creator skill（先预览后公开），复制下面指令到 Claude Code：")
    cmd = xhs_card.build_publish_command(_fake_ctx(out_dir))
    if st.button("📋 生成发布指令", use_container_width=True):
        st.toast("指令已生成，全选复制即可")
    st.text_area("发布指令（复制到 Claude Code 执行）", value=cmd, height=110)


def _fake_ctx(out_dir: Path):
    from core.pipeline import GenCtx
    return GenCtx(run_id=out_dir.name, out_dir=out_dir,
                  role="", skill="", case="", equip={})


def _render_talk(out_dir: Path) -> None:
    path = out_dir / "话术包.md"
    if path.exists():
        st.markdown(path.read_text(encoding="utf-8"))
