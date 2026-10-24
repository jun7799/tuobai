"""工作日志：总结当天经营数据生成日志 → 上传腾讯云 worklogs（多机/多 agent 共享）。

CLI-first，供本工作台 UI 与其他 agent 调用：
  python -m core.worklog auto                      # 自动总结今天并上传
  python -m core.worklog submit --content "..."    # 提交指定内容
  python -m core.worklog local                     # 只生成本地不上传

服务器目录：ubuntu@124.221.77.217:~/worklogs/machines/JUN7799-OPC/
（与用户现有 worklog 体系同仓不同机器名，双机互相可见）
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from config import PROJECT_ROOT

LOCAL_DIR = PROJECT_ROOT / "data" / "worklogs"
MACHINE = "JUN7799-OPC"
SERVER = "ubuntu@124.221.77.217"
REMOTE_DIR = f"~/worklogs/machines/{MACHINE}"


def _exe(name: str) -> str:
    """PATH 可能缺 System32（venv 继承问题），给 ssh/scp 加绝对路径兜底。"""
    found = shutil.which(name)
    if found:
        return found
    for cand in (rf"C:\Windows\System32\OpenSSH\{name}.exe",):
        if Path(cand).exists():
            return cand
    return name


def _collect_facts() -> str:
    """汇总今天的经营事实（日志的数据部分）。"""
    from core import finance, profile
    today = time.strftime("%Y-%m-%d")
    lines = []
    fin = finance.list_records(days=1)
    today_fin = [r for r in fin if r["date"] == today]
    if today_fin:
        inc = sum(r["amount"] for r in today_fin if r["type"] == "income")
        exp = sum(r["amount"] for r in today_fin if r["type"] == "expense")
        lines.append(f"- 财务：今日记账 {len(today_fin)} 笔（收入 ¥{inc:.1f} / 支出 ¥{exp:.1f}）")
        for r in today_fin:
            lines.append(f"  - {'收入' if r['type']=='income' else '支出'} ¥{r['amount']} "
                         f"[{r['category']}] {r['note']}（来源:{r['source'] or '手工'}）")
    leads = profile.load_leads()
    today_leads = [l for l in leads if str(l.get("updated_at", "")).startswith(today)]
    if today_leads:
        stages = {}
        for l in today_leads:
            stages[l.get("stage", "线索")] = stages.get(l.get("stage", "线索"), 0) + 1
        lines.append(f"- 商机：今日更新 {len(today_leads)} 条（{'、'.join(f'{k}×{v}' for k, v in stages.items())}）")
    out_dir = PROJECT_ROOT / "output"
    if out_dir.exists():
        today_runs = [d for d in out_dir.iterdir()
                      if d.is_dir() and (d / "package.json").exists()
                      and time.strftime("%Y-%m-%d", time.localtime(d.stat().st_mtime)) == today]
        for d in today_runs:
            try:
                pkg = json.loads((d / "package.json").read_text(encoding="utf-8"))
                state_p = d / "state.json"
                online = ""
                if state_p.exists():
                    st = json.loads(state_p.read_text(encoding="utf-8"))
                    if st.get("xianyu_item_id"):
                        online = f"，已上架闲鱼({st['xianyu_item_id']})"
                lines.append(f"- 开张：新服务「{pkg['positioning']['name']}」"
                             f"（{pkg['positioning']['one_liner']}）{online}")
            except (json.JSONDecodeError, KeyError):
                continue
    return "\n".join(lines) or "- （今日暂无经营数据）"


def build_content(content: str | None = None, *, summarize: bool = False) -> str:
    """生成日志正文：自动模式=数据事实+LLM总结；手动模式=用户内容+数据附录。"""
    facts = _collect_facts()
    date = time.strftime("%Y-%m-%d")
    if summarize:
        from core import llm_client
        ai = llm_client.chat_text(
            "你是一人公司经营日志撰写助手。根据今日经营数据事实，写一段 100 字以内的"
            "「今日小结」，口语化、有温度、突出关键数字。只输出小结正文。",
            f"今日数据事实：\n{facts}", temperature=0.6)
    else:
        ai = ""
    parts = [f"# {date} 托摆经营日志（{MACHINE}）", ""]
    if ai:
        parts += ["## 一、今日小结", "", ai, ""]
    parts += ["## 二、经营数据", "", facts, ""]
    if content:
        parts += ["## 三、补充记录", "", content, ""]
    parts += ["## 四、接下来要做的", "", "- （待补充）", ""]
    return "\n".join(parts)


def submit(content: str | None = None, *, summarize: bool = False,
           upload: bool = True) -> tuple[Path, str]:
    """生成日志文件并（可选）SSH 上传。返回 (本地路径, 上传结果消息)。"""
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    date = time.strftime("%Y-%m-%d")
    body = build_content(content, summarize=summarize)
    local = LOCAL_DIR / f"{date}_{MACHINE}.md"
    local.write_text(body, encoding="utf-8")
    if not upload:
        return local, "仅本地存档（未上传）"
    try:
        subprocess.run(  # noqa: S603 固定服务器配置
            [_exe("ssh"), "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", SERVER,
             f"mkdir -p {REMOTE_DIR}"],
            capture_output=True, timeout=20, check=True)
        result = subprocess.run(  # noqa: S603
            [_exe("scp"), "-o", "ConnectTimeout=10", "-o", "BatchMode=yes",
             str(local), f"{SERVER}:{REMOTE_DIR}/"],
            capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return local, f"已上传 → {SERVER}:{REMOTE_DIR}/"
        return local, f"上传失败：{result.stderr[:200]}"
    except (subprocess.SubprocessError, OSError) as e:
        return local, f"上传失败：{e}"


def main() -> None:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="托摆·工作日志")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auto", help="自动总结今天并上传")
    sub.add_parser("local", help="只生成本地日志")
    p_sub = sub.add_parser("submit", help="提交指定内容")
    p_sub.add_argument("--content", required=True)
    args = parser.parse_args()

    if args.cmd == "auto":
        path, msg = submit(summarize=True)
    elif args.cmd == "local":
        path, msg = submit(summarize=True, upload=False)
    else:
        path, msg = submit(args.content)
    print(f"[OK] 日志: {path}")
    print(f"[{'OK' if '已上传' in msg else 'WARN'}] {msg}")


if __name__ == "__main__":
    main()
