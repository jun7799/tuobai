"""发布托摆小红书笔记（默认仅自己可见，确认后加 --public 重发或转公开）。"""
import subprocess

PY = r"C:\Users\44162\AppData\Local\Programs\Python\Python312\python.exe"
PUBLISH = r"C:\Users\44162\.claude\skills\xhs-note-creator\scripts\publish_xhs.py"
K = r"D:\归档项目\AI活动\way2agi手搓大会·1024超能coding周末-20261023\OPC助手\kaizhangji"

TITLE = "县城摩托车师傅，教会我做了一个产品🛵"

DESC = """每个县城都有一个摩托车师傅。

把车开出来，往路边一停，就开张了。
车就是店，脸就是招牌，
路过的人都知道他能干什么。

可到了网上呢？
会写代码的、会做设计的、会写文案的，
技能全锁在聊天记录里——
孤芳自赏最心痛。

所以我做了「托摆」🛵

托：托管给 AI——上架、文案、定价，你不会的它全包
摆：摆摊到路边——把服务亮到人人都看得见的地方

一句话说清你的技能，2 分钟生成全套开张装备：

✅ 定价三档（AI 按同行行情建议）
✅ 闲鱼商品文案 + AI 主图，确认后真实上架
✅ 小红书推广卡片一键渲染
✅ 客户问价？AI 报价助手直接给话术
✅ 成交了，跟 AI 说一句「闲鱼成交一单69」自动记账

最狠的是：记账、商机、日志全部 CLI 化——
你的 AI agent 也能替你经营 🤖

不是玩具，已真实成交：
用托摆上架的第一件服务（¥69 爬虫定制）正在闲鱼在售。

还有个彩蛋 🥚
万一干不下去了？
一键下架 + 经营数据自动写成清算报告 + AI 把经验写进简历——
大不了回去继续服务金主爸爸们，没什么大不了的 😄

这是我参加 WaytoAGI 1024 超能 Coding 周末的作品：
两天，一个人 + AI，从想法到真实成交。

技能不该烂在收藏夹里。
阿托，永远在线。

#一人公司 #AI副业 #技能变现 #WaytoAGI #1024超能Coding周末 #AI切磋大会 #程序员副业 #独立开发"""

cmd = [
    PY, "-X", "utf8", PUBLISH,
    "--title", TITLE,
    "--desc", DESC,
    "--images",
    rf"{K}\assets\poster_xhs.png",
    rf"{K}\assets\xianyu_item.png",
    rf"{K}\e2e_shots\06_result_service.png",
    rf"{K}\assets\poster_a4.png",
    # 话题不单独传（API 查询格式问题），正文里的 # 标签会被小红书自动识别
]
result = subprocess.run(cmd, capture_output=True, text=True,
                        encoding="utf-8", errors="replace",
                        cwd=r"C:\Users\44162\.claude\skills\xhs-note-creator")
print(result.stdout[-2000:] if result.stdout else "")
print(result.stderr[-1000:] if result.stderr else "")
