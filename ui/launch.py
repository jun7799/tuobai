"""上架服务：一句话技能 → 全套装备 → 确认后闲鱼真实上架。整合原四步向导。"""
from __future__ import annotations

import streamlit as st

st.markdown("## 🐟 上架服务")
st.caption("一句话说清技能，2 分钟生成全套开张装备；**商品图和文案都会先给你过目确认，再发闲鱼**")

step = st.session_state.get("step", "intake")

# 成果直达：从工作台/示例卡进来（step 已是 result 且 out_dir 已设）
if step == "result" and not st.session_state.get("out_dir"):
    step = "intake"

if step == "intake":
    from ui import step1_intake
    step1_intake.render()
elif step == "select":
    from ui import step2_select
    step2_select.render()
elif step == "generate":
    from ui import step3_generate
    step3_generate.render()
elif step == "result":
    from ui import step4_result
    step4_result.render()
