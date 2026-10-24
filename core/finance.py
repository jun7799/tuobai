"""财务记账：收入/支出流水 + 汇总。CLI-first，供本工作台 UI 与其他 agent 调用。

其他 agent 调用方式（任何机器、任何 agent）：
  python -m core.finance add income 69 "爬虫定制单" --category 服务收入 --source 闲鱼
  python -m core.finance add expense 15.9 "生图API" --category 工具成本
  python -m core.finance summary          # 本月汇总
  python -m core.finance list --days 7    # 近7天流水
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "finance.json"

CATEGORIES_INCOME = ["服务收入", "咨询收入", "课程/知识付费", "其他收入"]
CATEGORIES_EXPENSE = ["工具成本", "API费用", "推广费用", "素材采购", "其他支出"]


def _load() -> list[dict]:
    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return []


def _save(records: list[dict]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2),
                         encoding="utf-8")


def add(entry_type: str, amount: float, note: str = "", *,
        category: str = "", source: str = "", date: str | None = None) -> dict:
    """记一笔。entry_type: income|expense。返回新记录。"""
    if entry_type not in ("income", "expense"):
        raise ValueError("entry_type 必须是 income 或 expense")
    if amount <= 0:
        raise ValueError("金额必须大于 0")
    record = {
        "id": uuid.uuid4().hex[:8],
        "date": date or time.strftime("%Y-%m-%d"),
        "type": entry_type,
        "amount": round(float(amount), 2),
        "category": category or ("其他收入" if entry_type == "income" else "其他支出"),
        "note": note, "source": source,
    }
    records = _load()
    records.append(record)
    _save(records)
    return record


def summary(month: str | None = None) -> dict:
    """月度汇总（默认当月）。返回总收入/总支出/净额/分类明细。"""
    month = month or time.strftime("%Y-%m")
    records = [r for r in _load() if r["date"].startswith(month)]
    income = sum(r["amount"] for r in records if r["type"] == "income")
    expense = sum(r["amount"] for r in records if r["type"] == "expense")
    by_cat: dict[str, float] = {}
    for r in records:
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + \
            (r["amount"] if r["type"] == "income" else -r["amount"])
    return {"month": month, "count": len(records), "income": round(income, 2),
            "expense": round(expense, 2), "net": round(income - expense, 2),
            "by_category": by_cat}


def list_records(days: int = 30) -> list[dict]:
    """近 N 天流水（新在前）。"""
    cutoff = time.strftime("%Y-%m-%d", time.localtime(time.time() - days * 86400))
    records = [r for r in _load() if r["date"] >= cutoff]
    return sorted(records, key=lambda r: (r["date"], r["id"]), reverse=True)


def main() -> None:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="托摆·财务记账")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_add = sub.add_parser("add", help="记一笔")
    p_add.add_argument("type", choices=["income", "expense"])
    p_add.add_argument("amount", type=float)
    p_add.add_argument("note", nargs="?", default="")
    p_add.add_argument("--category", default="")
    p_add.add_argument("--source", default="")
    p_add.add_argument("--date", default=None, help="YYYY-MM-DD，默认今天")
    sub.add_parser("summary", help="当月汇总").add_argument("--month", default=None)
    p_list = sub.add_parser("list", help="近N天流水")
    p_list.add_argument("--days", type=int, default=30)
    args = parser.parse_args()

    if args.cmd == "add":
        rec = add(args.type, args.amount, args.note, category=args.category,
                  source=args.source, date=args.date)
        print(f"[OK] 已记账: {rec['date']} {'收入' if rec['type']=='income' else '支出'} "
              f"¥{rec['amount']} [{rec['category']}] {rec['note']}")
    elif args.cmd == "summary":
        print(json.dumps(summary(args.month), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(list_records(args.days), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
