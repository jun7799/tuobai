# 开张机 · 进度记录（Day 1 深夜更新）

## 产品定位（已升级）

「开张机」= 一人公司全生命周期工作台
找方向 → 看同行 → 立人设 → 攒客户 → 开张开卖 →（万一不行）体面关张

## 模块状态

| 模块 | 状态 | 说明 |
|---|---|---|
| 🏠 工作台首页 | ✅ 完成 | 画像卡+数据指标+模块导航+已开张服务卡片（冒烟通过） |
| 💬 找方向 | ✅ 完成 | AI 对话（glm-5.3-flash 真实回复验证）+ 画像沉淀 + 带方向去开张 |
| 🕵️ 看同行 | ✅ 完成 | 《同行都在做什么》情报报告（真实生成验证，落盘 data/） |
| 📇 立人设 | 🛠️ 占位 | 明天做：HTML 模板+playwright 截图名片 |
| 🤝 攒客户 | 🛠️ 占位 | 明天做：st.data_editor 商机表+指标卡+AI 报价助手 |
| 🐟 开张开卖 | ✅ 完成 | 原 E2E 全流程通过，闲鱼真实上架验证 |
| 🚪 关张转职 | 🛠️ 占位 | 明天做：下架+清算报告+简历初稿+求职指引 |

## 明天作战顺序（封板 15:00）

1. 09:00 立人设（名片）——HTML 模板 2 套 + 截图 + 首页"名片已生成"联动
2. 10:30 攒客户（CRM）——MVP：录入表+阶段统计+AI 报价
3. 11:30 关张转职——下架命令验证（goofish item delist?）+ 清算报告 LLM + 简历初稿
4. 12:30 全站回归冒烟（e2e_workbench + e2e_flow）+ 修 bug
5. 13:30 功能冻结；录完整演示屏；更新 README/DEMO.md（新故事线）
6. 14:30 封板检查（run.bat 从零跑）→ 15:00 封板 → 提交

## 今日硬证据

- 闲鱼真实商品：https://www.goofish.com/item?id=1095687996473
- 3 个示例角色全套成品（examples/）
- E2E 截图 15 张（e2e_shots/）
- 首页指标：已开张 5 家 / 在线商品 1 件

## 踩坑记录（复盘素材）

1. Streamlit widget key 生命周期：widget 消失 → session_state[key] 被清；widget 用独立 key，流转时复制
2. Streamlit 程序化填值（Playwright fill）不同步 → 用 keyboard.type + Tab blur
3. Windows 残留进程：with_server.py 杀不干净 streamlit → 下轮连旧进程旧代码
4. subprocess 继承 stdin 挂死 → stdin=DEVNULL
5. 三引号字符串结尾与内容引号撞车（""""）→ SyntaxError
