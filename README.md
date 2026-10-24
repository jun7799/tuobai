<p align="center">
  <img src="assets/logo.png" width="180" alt="托摆 logo：摩托车后座驮着招牌"/>
</p>

<h1 align="center">托摆 🛵</h1>

<p align="center">把技能托付给 AI，替你摆到路边去</p>

---

> 每个县城都有一个摩托车师傅——把车开出来，往路边一停，就开张了。车就是店，脸就是招牌，路过的人都知道他能干什么。
> 可是到了网上，一个会写代码、会做设计的人，技能却锁在聊天记录里，没有人看得见。
> **托摆，就是给你的技能修一条"路边"**——2 分钟把技能变成闲鱼在售商品；记账、日志、商机全部 CLI 化，**你的 AI agent 也能替你经营**。

**托**：托管——上架、文案、定价这些不会干的事，托付给 AI。
**摆**：摆摊——把服务亮在公开场所，人人可见，就像摩托车师傅停在路边。

WaytoAGI 1024 超能 Coding 周末 · OPC 赛道作品

## 这是什么

面向**有技能、想变现、卡在“不会卖”这一步的人**的一人公司工作台。核心是一条被验证的链路：

```
一句话技能 → 2 分钟全套装备（定价/文案/主图/话术）→ 确认 → 闲鱼真实在售
```

围绕这条链路，其余模块构成"从开张到关张"的经营闭环：

```
💬找方向 → 🕵️看同行 → 📇立人设 → 🤝攒客户 → 🐟上架服务 → 📣推广 → 💰记账 → 📝日志
                                                                ↓
                                                        🚪干不下去？关张转职
                                                  （下架+清算报告+AI简历+转求职）
```

## Agent 友好（CLI-first）——托摆不只是给你用的

记账、日志、开张全流程都有 CLI 入口，你的 AI agent 可以直接替你经营：

```bash
# 成单后 agent 自动记账
python -m core.finance add income 69 "爬虫定制单" --category 服务收入 --source 闲鱼

# agent 录入客户商机（成交后 set-stage + 记账，商机账本串起来）
python -m core.leads add "宠物店王老板" --source 闲鱼 --need "每月5张海报" --amount 300

# AI 总结今天经营并上传云端（多机多 agent 共享）
python -m core.worklog auto

# 一句话开张（无 UI 也能跑全流程）
python -m core.pipeline --role 技术开发 --skill "帮人写Python爬虫，3天交付"
```

内置 `.claude/skills/opc-worklog/SKILL.md`：任何 Claude agent 进本项目即可按 skill 调用经营能力。

## 八大模块

| 模块 | 能干什么 | 技术 |
|---|---|---|
| 💬 找方向 | 和 AI 聊天挖掘可变现技能，沉淀**用户画像**（贯穿全站） | glm-5.3-flash 对话 + 结构化画像 |
| 🕵️ 看同行 | **真实抓取闲鱼在售同行商品**（价格/热度/卖家）+ AI 点评 + AI 情报报告（含每日灵感卡） | goofish search（浏览器路径）+ LLM |
| 📇 立人设 | **跟 AI 聊出人设**或手填 → 生成可分享名片（两套模板），服务列表自动带入已开张服务 | 通用对话提取组件 + HTML 模板 + playwright |
| 🤝 攒客户 | 轻 CRM：**跟 AI 说一句自动录商机**（"宠物店王老板问价"→商机卡）/ 表单 / 阶段流转 + **AI 报价助手** | 本地 JSON + LLM |
| 🐟 上架服务 | 一句话技能 → 2 分钟全套装备；**商品图和文案先给你过目确认再发闲鱼** | 见下方架构 |
| 📣 推广服务 | 为已开张服务生成推广素材：小红书笔记（可换一版）+ 公众号文章，**先预览效果再发** | LLM + render_xhs |
| 💰 记账 | **三入口并列**：手动表单 / 跟 AI 说（"闲鱼成交一单69元"→自动入账）/ 其他 agent 调 CLI | python -m core.finance |
| 📝 工作日志 | 三入口（手动/OPC 助手一键总结/其他 agent CLI）+ **经营回顾**（AI 周报复盘），上传云端多机共享 | python -m core.worklog + SSH |
| 🚪 关张转职 | 一键下架闲鱼商品 → 关张清算报告（经营数据变简历资产）→ AI 简历初稿 + boss skill 求职指引 | goofish delete + LLM |

## 开张开卖（核心链路）架构

```
一句话技能
   ├─ 📦 服务打包卡   定价三档/卖点/FAQ/交付标准      ← glm-5.3-flash 一次 JSON 生成
   ├─ 🐟 闲鱼商品     标题+描述+AI主图，确认后真实上架  ← goofish-cli（自动类目/传图）
   ├─ 📕 小红书笔记   文案+封面/正文卡片渲染           ← render_xhs.py（playwright）
   ├─ 💬 接待话术包   开场白/评论回复/询价/砍价应对
   └─ 🖼️ AI 主图      扁平插画风                      ← gpt-image-2
```

工程要点：
- **每步产物落盘**（output/<run_id>/），刷新不丢、失败单步重试
- **发布强制人工确认**：风控词预检（广告法绝对化词/站外引流词）+ 自动修正 + 双确认
- **演示兜底**：examples/ 内置 3 个预生成全套成品，API 挂了照样演示

## 怎么跑

```bash
# 1. 复制 .env.example 为 .env，填 API Key 和本机路径（goofish/渲染脚本/系统Python）
# 2. 双击 run.bat，或：
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\streamlit run app.py
# 3. 打开 http://localhost:8501
```

## 服务谁 · 怎么收费

**目标客户**：有技能、想变现、卡在“不会卖”这一步的人——副业程序员/设计师/写手/自由职业者，以及在用 Claude Code 等 AI agent 的 tech-savvy 副业者（CLI/skill 接入）。

| 档位 | 价格 | 内容 |
|---|---|---|
| 单次开张 | ¥29.9 | 一句话 → 全套装备 + 确认后上架 |
| 全装备开张 | ¥99 | 全套装备 + 代上架 + 名片 + 推广素材包 |
| Agent 版订阅 | ¥199/月 | 全模块 + CLI/skill 多 agent 接入 + 经营回顾周报 |

**真实成交证据**：闲鱼已真实上架（¥69 爬虫定制服务）：
https://www.goofish.com/item?id=1095687996473

## 致谢与开源说明

- [goofish-cli](https://github.com/fancyboi999/goofish-cli)（Apache-2.0）：闲鱼自动化 CLI
- xhs-note-creator 的 render_xhs.py（本地 skill）：小红书卡片渲染
- boss-job-hunter（本地 skill）：关张转职的求职指引
- 文本/生图模型：OpenDev 算力（比赛提供）
