"""商机管理 CLI：其他 agent 录入商机的入口。

python -m core.leads add "宠物店王老板" --source 闲鱼 --need "每月5张海报" --amount 300
python -m core.leads add "李姐" --source 小红书 --need "改简历" --stage 已报价 --amount 99
python -m core.leads list
python -m core.leads set-stage <id> 已成交
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid

from core import profile as profile_store

STAGES = ["线索", "沟通中", "已报价", "已成交", "已流失"]


def add(name: str, *, source: str = "其他", need: str = "", amount: float = 0,
        stage: str = "线索") -> dict:
    leads = profile_store.load_leads()
    record = {
        "id": uuid.uuid4().hex[:8],
        "name": name, "source": source, "need": need,
        "stage": stage if stage in STAGES else "线索",
        "amount": round(float(amount), 2),
        "created_at": time.strftime("%Y-%m-%d %H:%M"),
        "updated_at": time.strftime("%Y-%m-%d"),
    }
    leads.append(record)
    profile_store.save_leads(leads)
    return record


def set_stage(lead_id: str, stage: str) -> dict | None:
    leads = profile_store.load_leads()
    for lead in leads:
        if lead["id"] == lead_id:
            lead["stage"] = stage if stage in STAGES else lead["stage"]
            lead["updated_at"] = time.strftime("%Y-%m-%d")
            profile_store.save_leads(leads)
            return lead
    return None


def main() -> None:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="托摆·商机管理")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_add = sub.add_parser("add", help="录入商机")
    p_add.add_argument("name", help="客户称呼")
    p_add.add_argument("--source", default="其他",
                       help="闲鱼/小红书/朋友介绍/名片分享/其他")
    p_add.add_argument("--need", default="", help="需求描述")
    p_add.add_argument("--amount", type=float, default=0, help="意向金额")
    p_add.add_argument("--stage", default="线索",
                       help="线索/沟通中/已报价/已成交/已流失")
    p_list = sub.add_parser("list", help="列出商机")
    p_list.add_argument("--days", type=int, default=30)
    p_stage = sub.add_parser("set-stage", help="更新商机阶段")
    p_stage.add_argument("id")
    p_stage.add_argument("stage", choices=STAGES)
    args = parser.parse_args()

    if args.cmd == "add":
        rec = add(args.name, source=args.source, need=args.need,
                  amount=args.amount, stage=args.stage)
        print(f"[OK] 已录入商机: {rec['name']}（{rec['stage']}，¥{rec['amount']}）id={rec['id']}")
    elif args.cmd == "list":
        print(json.dumps(profile_store.load_leads(), ensure_ascii=False, indent=2))
    else:
        rec = set_stage(args.id, args.stage)
        if rec:
            print(f"[OK] {rec['name']} → {rec['stage']}（成交了记得记账：python -m core.finance add income ...）")
        else:
            print(f"[WARN] 未找到 id={args.id}")


if __name__ == "__main__":
    main()
