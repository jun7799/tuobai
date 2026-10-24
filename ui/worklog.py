"""📝 工作日志：三入口（手动/OPC助手AI总结/其他agent CLI）+ 经营回顾。"""
from __future__ import annotations

import json
import time
from pathlib import Path

import streamlit as st

from config import PROJECT_ROOT
from core import finance, llm_client, profile as profile_store, worklog
from ui.components import chat_assistant, cli_card

st.markdown("## 📝 工作日志")
st.caption("AI 自动总结经营数据写日志，上传腾讯云与双机日志体系互通。回顾区每周给你一份经营复盘。")

tab1, tab2, tab3 = st.tabs(["💬 跟阿托说（补充+自动总结）", "🤖 阿托一键总结", "🤖 其他 agent 记"])

with tab1:
    def _preview_log(d: dict) -> None:
        st.markdown(f"**今日补充**：{d.get('content', '')[:80]}")

    def _save_log(d: dict) -> None:
        path, msg = worklog.submit(d.get("content", ""), summarize=True)
        if "已上传" not in msg:
            raise RuntimeError(msg)

    chat_assistant(
        "worklog",
        hint="例：今天把名片模块做完了，明天准备录演示视频",
        extract_format='{"content":"整理成一段日志式的补充记录，100字内"}',
        preview=_preview_log,
        on_confirm=_save_log,
    )
    st.caption("确认后会：AI 总结今日经营数据 + 你的补充 → 生成日志 → 上传云端")

with tab2:
    if st.button("🤖 AI 总结今天并提交日志（自动模式）", type="primary", use_container_width=True):
        with st.status("生成日志中…（AI 总结 + 经营数据汇总 + 上传）", expanded=True):
            path, msg = worklog.submit(None, summarize=True)
        if "已上传" in msg:
            st.success(f"已提交！{msg}")
        else:
            st.warning(f"本地已保存，云端上传未成功：{msg}")
        st.rerun()

with tab3:
    cli_card("给其他 agent 的日志入口", [
        "# 每日收工：AI 自动总结今天经营并上传云端",
        r'.\.venv\Scripts\python.exe -X utf8 -m core.worklog auto',
        "",
        "# 带内容提交（agent 干完活顺手记一笔）",
        r'.\.venv\Scripts\python.exe -X utf8 -m core.worklog submit --content "今天完成了名片模块"',
    ], note="上传到 ubuntu@124.221.77.217:~/worklogs/machines/JUN7799-OPC/，与双机日志体系互通")

st.divider()

tab_hist, tab_review = st.tabs(["📚 历史日志", "📊 经营回顾"])

with tab_hist:
    log_dir = PROJECT_ROOT / "data" / "worklogs"
    if log_dir.exists():
        logs = sorted(log_dir.glob("*.md"), reverse=True)[:10]
        for log in logs:
            with st.expander(f"📄 {log.name}"):
                st.markdown(log.read_text(encoding="utf-8"))
    else:
        st.caption("还没有提交过日志")

with tab_review:
    st.caption("AI 汇总日志 + 财务 + 商机数据，生成经营复盘")
    if st.button("📊 生成本周经营回顾", type="primary", use_container_width=True):
        with st.status("AI 复盘生成中…"):
            try:
                # 汇总数据
                fin = finance.summary()
                leads = profile_store.load_leads()
                log_dir = PROJECT_ROOT / "data" / "worklogs"
                logs_text = ""
                if log_dir.exists():
                    for log in sorted(log_dir.glob("*.md"), reverse=True)[:7]:
                        logs_text += log.read_text(encoding="utf-8")[:1500] + "\n---\n"
                leads_summary = {}
                for l in leads:
                    leads_summary[l.get("stage", "?")] = leads_summary.get(l.get("stage", "?"), 0) + 1
                review = llm_client.chat_text(
                    "你是一人公司经营复盘顾问。根据本周日志、财务、商机数据，"
                    "生成 markdown 复盘：## 本周数据一览（表格）/ ## 做得好的 / "
                    "## 要改进的 / ## 下周三件事（具体可执行）。语气务实不打鸡血。400字内。",
                    f"财务：{json.dumps(fin, ensure_ascii=False)}\n"
                    f"商机阶段分布：{json.dumps(leads_summary, ensure_ascii=False)}\n"
                    f"本周日志：\n{logs_text or '（无）'}", temperature=0.6)
                st.session_state["_review"] = review
                # 回顾也上云归档
                rv = PROJECT_ROOT / "data" / "worklogs" / f"周报_{time.strftime('%Y-%m-%d')}.md"
                rv.write_text(review, encoding="utf-8")
            except llm_client.LLMError as e:
                st.error(f"生成失败：{e}")
    if "_review" in st.session_state:
        st.markdown(st.session_state["_review"])
