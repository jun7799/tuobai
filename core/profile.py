"""用户画像（profile）与商机（leads）的本地 JSON 存取，全工作台共享。"""
from __future__ import annotations

import json
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
