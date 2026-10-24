"""Step3 生成流水线：每次 rerun 执行一步，进度逐格点亮；失败可单步重试。"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from core import pipeline


def _ctx_from_session() -> pipeline.GenCtx:
    out_dir = Path(st.session_state.out_dir)
    form = json.loads((out_dir / "form.json").read_text(encoding="utf-8"))
    return pipeline.GenCtx(
        run_id=form["run_id"], out_dir=out_dir, role=form["role"],
        skill=form["skill"], case=form.get("case", ""),
        equip=form.get("equip", {}), video_on=form.get("video_on", False),
    )


def render() -> None:
    st.markdown("## 第 3 步 · 开张流水线")
    st.caption(f"run_id: {st.session_state.run_id} ｜ 每步产物实时落盘，刷新页面不丢")

    ctx = _ctx_from_session()
    specs = pipeline.active_specs(ctx.equip)
    state = pipeline.load_state(ctx.out_dir)

    # 已完成步骤：折叠绿灯
    for spec in specs:
        cur = state.get("steps", {}).get(spec.key, "pending")
        if cur == "done":
            with st.status(f"✅ {spec.label}", state="complete", expanded=False):
                st.caption("完成")

    # 抢先看：打包一落盘就渲染服务卡摘要（不用等全流程跑完）
    pkg_path = ctx.out_dir / "package.json"
    if pkg_path.exists() and not all(
            state.get("steps", {}).get(s.key) == "done" for s in specs):
        try:
            pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
            pos = pkg["positioning"]
            with st.container(border=True):
                st.markdown(f"### 👀 抢先看 · **{pos['name']}**")
                st.markdown(f"{pos['one_liner']}")
                tiers = st.columns(min(len(pos.get("tiers", [])), 3) or 1)
                for i, t in enumerate(pos.get("tiers", [])[:3]):
                    with tiers[i]:
                        st.markdown(f"**{t['name']}** ¥{t['price']}")
                        st.caption(t.get("includes", "")[:24])
                hl = pkg.get("service_card", {}).get("highlights", [])[:2]
                if hl:
                    st.caption("卖点：" + " / ".join(hl))
        except (json.JSONDecodeError, KeyError):
            pass

    # 找第一个未完成的步骤
    pending = next(
        (s for s in specs if state.get("steps", {}).get(s.key, "pending") != "done"), None)

    if pending is None:
        st.balloons()
        st.success("全套开张装备生成完毕！")
        if st.button("🎉 查看成果", type="primary"):
            st.session_state.step = "result"
            st.rerun()
        return

    # 失败步骤：红灯 + 重试
    cur = state.get("steps", {}).get(pending.key, "pending")
    if cur == "failed":
        err = state.get("errors", {}).get(pending.key, "")
        with st.status(f"❌ {pending.label} 失败", state="error", expanded=True):
            st.error(err)
            if st.button(f"🔄 重试：{pending.label}", key=f"retry_{pending.key}"):
                pipeline.run_single(ctx, pending)
                st.rerun()
            if st.button("⏭️ 跳过这步，看已有成果", key=f"skip_{pending.key}"):
                st.session_state.step = "result"
                st.rerun()
        return

    # 待执行步骤：本次 rerun 就执行它（完成或失败后 rerun 进入下一格）
    with st.status(f"{pending.label} 进行中…", expanded=True) as status:
        # 执行前先 flush 一行提示（Streamlit 会流式推送到前端，有实时感）
        st.caption("调用中，请稍候…（打包约 35 秒，画图约 25 秒，渲染约 15 秒）")
        state = pipeline.run_single(ctx, pending, report=st.write)
        st.rerun()
