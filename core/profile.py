"""用户画像（profile）与商机（leads）的本地 JSON 存取，全工作台共享。"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from config import PROJECT_ROOT

DATA_DIR = PROJECT_ROOT / "data"
PROFILE_PATH = DATA_DIR / "profile.json"
LEADS_PATH = DATA_DIR / "leads.json"

PROFILE_EMPTY = {
    "name": "", "background": "", "strengths": [], "direction": "",
    "services": [], "tone": "", "updated_at": "",
}


def load_profile() -> dict:
    if PROFILE_PATH.exists():
        data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        return {**PROFILE_EMPTY, **data}
    return dict(PROFILE_EMPTY)


def save_profile(profile: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    profile["updated_at"] = time.strftime("%Y-%m-%d %H:%M")
    PROFILE_PATH.write_text(json.dumps(profile, ensure_ascii=False, indent=2),
                            encoding="utf-8")


def profile_filled() -> bool:
    p = load_profile()
    return bool(p["name"] or p["background"] or p["direction"])


def load_leads() -> list[dict]:
    if LEADS_PATH.exists():
        return json.loads(LEADS_PATH.read_text(encoding="utf-8"))
    return []


def save_leads(leads: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LEADS_PATH.write_text(json.dumps(leads, ensure_ascii=False, indent=2),
                          encoding="utf-8")


def merge_profile(patch: dict) -> dict:
    """合并式更新画像：只覆盖给出的字段，其余保留。返回更新后的画像。"""
    profile = load_profile()
    for key in ("name", "background", "direction", "tone"):
        if patch.get(key):
            profile[key] = patch[key]
    for key in ("strengths", "services"):
        if patch.get(key):
            # 接受 list 或逗号分隔字符串
            value = patch[key]
            if isinstance(value, str):
                value = [s.strip() for s in value.replace("，", ",").split(",") if s.strip()]
            profile[key] = value
    save_profile(profile)
    return profile


def main() -> None:
    """CLI：其他 agent 提交/查询用户画像。

    场景：你在其他项目里了解这位用户（背景/擅长/方向），
    可以替他把画像同步给托摆——托摆的定价、文案、名片、
    同行分析、简历初稿都会自动使用这份画像，越填越准。
    """
    import argparse

    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="托摆·用户画像（agent 可提交）")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_set = sub.add_parser("set", help="提交/更新画像（merge 语义，只改给出的字段）")
    p_set.add_argument("--name", help="昵称或代称")
    p_set.add_argument("--background", help="职业背景一句话")
    p_set.add_argument("--strengths", help="擅长点，逗号分隔，如 \"Python,爬虫,AI工作流\"")
    p_set.add_argument("--direction", help="想做的变现方向，如 \"帮小店主做提效工具，定价99\"")
    p_set.add_argument("--services", help="建议先卖的服务，逗号分隔")
    sub.add_parser("get", help="查看当前画像（先查再补，避免覆盖）")
    args = parser.parse_args()

    if args.cmd == "get":
        print(json.dumps(load_profile(), ensure_ascii=False, indent=2))
        return
    patch = {k: getattr(args, k) for k in
             ("name", "background", "strengths", "direction", "services")
             if getattr(args, k)}
    if not patch:
        print("[WARN] 没有给出任何字段。示例：python -m core.profile set --name 俊哥 "
              '--background "10年程序员" --strengths "Python,爬虫"')
        return
    profile = merge_profile(patch)
    print(f"[OK] 画像已更新：{profile['name'] or '(未命名)'}｜方向：{profile['direction'] or '未定'}")
    print("[OK] 托摆的名片/同行分析/定价建议/简历初稿将自动使用这份画像")


if __name__ == "__main__":
    main()
