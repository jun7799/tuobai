"""共享组件：页面 AI 助手条（自然语言 → AI 提取结构化 → 确认入库）+ CLI 入口卡。"""
from __future__ import annotations

from typing import Callable

import streamlit as st

from core import llm_client


def chat_assistant(page_key: str, hint: str, extract_format: str,
                   preview: Callable[[dict], None],
                   on_confirm: Callable[[dict], None],
                   *, system: str = "你是信息提取助手，只输出 JSON，不要围栏。"):
    """页面底部 AI 助手条：说人话 → AI 提取 → 预览确认 → 入库。

    page_key:       用于 widget key 隔离
    hint:           输入框提示
    extract_format: 提取的 JSON 格式说明（嵌入 prompt）
    preview:        渲染提取结果预览（st.xxx）
    on_confirm:     用户点确认后回调（写入存储），抛异常则显示错误
    """
    st.markdown("**💬 跟阿托说，我来帮你填**")
    if prompt := st.chat_input(hint, key=f"assist_{page_key}"):
        with st.spinner("AI 提取中…"):
            try:
                data = llm_client.chat_json(
                    system,
                    f"用户输入：{prompt}\n\n提取为 JSON：{extract_format}",
                )
                st.session_state[f"_extract_{page_key}"] = data
            except llm_client.LLMError as e:
                st.error(f"AI 提取失败：{e}")
                st.session_state.pop(f"_extract_{page_key}", None)

    key = f"_extract_{page_key}"
    if key in st.session_state:
        data = st.session_state[key]
        with st.container(border=True):
            st.markdown("🔎 **AI 帮你填好了，确认一下**")
            preview(data)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ 确认保存", key=f"ok_{page_key}", type="primary",
                             use_container_width=True):
                    try:
                        on_confirm(data)
                        st.session_state.pop(key, None)
                        st.toast("已保存")
                        st.rerun()
                    except Exception as e:  # noqa: BLE001
                        st.error(f"保存失败：{e}")
            with c2:
                if st.button("✏️ 不对，重说", key=f"no_{page_key}",
                             use_container_width=True):
                    st.session_state.pop(key, None)
                    st.rerun()


def cli_card(title: str, commands: list[str], note: str = ""):
    """「其他 agent 调用」入口卡：显眼展示可复制命令。"""
    with st.container(border=True):
        st.markdown(f"**🤖 {title}**（其他 AI agent / 机器可直接调用）")
        for cmd in commands:
            st.code(cmd, language="bash")
        if note:
            st.caption(note)
