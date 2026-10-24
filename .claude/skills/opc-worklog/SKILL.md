---
name: opc-worklog
description: |
  托摆（OPC工作台）的经营日志与记账 CLI。当任何 agent 需要提交「托摆/OPC助手项目」的
  工作日志、查询经营数据、或为一人公司记账时使用。触发词：提交托摆日志、记一笔、
  记账、今天经营得怎么样、上传经营日志。支持本机 agent 与其他机器的 agent 直接调用。
---

# 托摆经营日志与记账 CLI

项目根目录：`D:\归档项目\AI活动\way2agi手搓大会·1024超能coding周末-20261023\OPC助手\kaizhangji`

## 提交工作日志（AI 自动总结 + 上传云端）

```
cd <项目根目录>
.venv\Scripts\python.exe -X utf8 -m core.worklog auto
```

自动汇总今日数据（新开张的服务、商机变动、记账流水）→ AI 写小结 →
上传到 `ubuntu@124.221.77.217:~/worklogs/machines/JUN7799-OPC/`，
与现有双机 worklog 体系互通（网页审阅版可见）。

手动带内容提交：
```
.venv\Scripts\python.exe -X utf8 -m core.worklog submit --content "今天完成了名片模块"
```

## 记账（其他 agent 也可直接记账）

```
.venv\Scripts\python.exe -X utf8 -m core.finance add income 69 "爬虫定制单" --category 服务收入 --source 闲鱼
.venv\Scripts\python.exe -X utf8 -m core.finance add expense 15.9 "生图API费" --category API费用
.venv\Scripts\python.exe -X utf8 -m core.finance summary     # 当月汇总
.venv\Scripts\python.exe -X utf8 -m core.finance list --days 7
```

## 商机录入（其他 agent 录客户线索）

```
.venv\Scripts\python.exe -X utf8 -m core.leads add "宠物店王老板" --source 闲鱼 --need "每月5张海报" --amount 300
.venv\Scripts\python.exe -X utf8 -m core.leads set-stage ba6ed034 已成交
.venv\Scripts\python.exe -X utf8 -m core.leads list
```

成交后顺手记账（商机→账本串起来）。

## 使用约定

- 成交一单后：先记账（finance add income），当天结束时 `worklog auto` 会自动带上这笔
- 日志机器名 `JUN7799-OPC`，与主日志 `JUN7799` 区分，不会互相覆盖
- SSH 不通时：命令不报错，日志落本地 `data/worklogs/`，下次提交时补传思路——直接重跑一次即可
