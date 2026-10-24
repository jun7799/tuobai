"""生成流水线：步骤注册表 + 磁盘状态机（state.json）+ 单步重试。

设计原则：每步完成即落盘，session 不持有结果——刷新页面从 state.json 恢复，
重试只重跑失败步骤，Step4 纯读磁盘渲染。

闲鱼真实发布不在 PIPELINE 内：它是 Step4 的用户确认动作（xianyu.publish_item）。

命令行独立运行：python -m core.pipeline --skill "..." --role 技术开发
"""
from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from config import settings

ReportFn = Callable[[str], None]


def _noop_report(text: str) -> None:  # CLI 用 print，UI 传 st.write
    print(f"  {text}")


@dataclass
class GenCtx:
    """一次生成的上下文（进入流水线时落盘 form.json，一切以磁盘为准）。"""
    run_id: str
    out_dir: Path
    role: str
    skill: str
    case: str = ""
    equip: dict = field(default_factory=dict)   # {"package","xianyu","xhs","talk"} -> bool
    video_on: bool = False

    def save_form(self) -> None:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        (self.out_dir / "form.json").write_text(json.dumps({
            "run_id": self.run_id, "role": self.role, "skill": self.skill,
            "case": self.case, "equip": self.equip, "video_on": self.video_on,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    @property
    def pkg(self) -> dict:
        """惰性读 package.json（package 步骤完成后可用）。"""
        path = self.out_dir / "package.json"
        if not path.exists():
            raise FileNotFoundError("package.json 尚未生成（先跑 package 步骤）")
        return json.loads(path.read_text(encoding="utf-8"))


@dataclass
class StepSpec:
    key: str
    label: str
    fn: Callable[[GenCtx, ReportFn], None]   # 抛异常即 failed
    depends: list[str] = field(default_factory=list)


def load_state(out_dir: Path) -> dict:
    path = out_dir / "state.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"steps": {}, "errors": {}}


def save_state(out_dir: Path, state: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _state_of(state: dict, key: str) -> str:
    return state.get("steps", {}).get(key, "pending")


def run_pipeline(ctx: GenCtx, specs: list[StepSpec],
                 report: ReportFn = _noop_report) -> dict:
    """顺序执行；done 跳过；依赖未完成置 blocked；失败写 errors 后停止。"""
    state = load_state(ctx.out_dir)
    for spec in specs:
        cur = _state_of(state, spec.key)
        if cur == "done":
            report(f"[跳过] {spec.label}（已完成）")
            continue
        dep_missing = [d for d in spec.depends if _state_of(state, d) != "done"]
        if dep_missing:
            state["steps"][spec.key] = "blocked"
            save_state(ctx.out_dir, state)
            report(f"[阻塞] {spec.label}（依赖未完成: {dep_missing}）")
            continue
        state["steps"][spec.key] = "running"
        save_state(ctx.out_dir, state)
        report(f"[开始] {spec.label} …")
        try:
            spec.fn(ctx, report)
            state["steps"][spec.key] = "done"
            state.get("errors", {}).pop(spec.key, None)
            report(f"[完成] {spec.label}")
        except Exception as e:  # noqa: BLE001 每步失败不炸整条流水线
            state["steps"][spec.key] = "failed"
            state.setdefault("errors", {})[spec.key] = str(e)[:500]
            save_state(ctx.out_dir, state)
            report(f"[失败] {spec.label}: {e}")
            break
        save_state(ctx.out_dir, state)
    return state


def run_single(ctx: GenCtx, spec: StepSpec, report: ReportFn = _noop_report) -> dict:
    """单步重试入口。"""
    state = load_state(ctx.out_dir)
    state["steps"][spec.key] = "running"
    save_state(ctx.out_dir, state)
    try:
        spec.fn(ctx, report)
        state["steps"][spec.key] = "done"
        state.get("errors", {}).pop(spec.key, None)
    except Exception as e:  # noqa: BLE001
        state["steps"][spec.key] = "failed"
        state.setdefault("errors", {})[spec.key] = str(e)[:500]
    save_state(ctx.out_dir, state)
    return state


# ---------- 各步骤实现（依赖对应模块） ----------

def _step_package(ctx: GenCtx, report: ReportFn) -> None:
    from core import packager
    report("AI 打包全套开张文案（约 35 秒）…")
    pkg = packager.build_package(ctx.role, ctx.skill, ctx.case or None)
    hits = packager.risk_scan(pkg)
    if hits:
        report(f"[提示] 命中风控词 {hits}（发布前会自动修正）")
    packager.save_package(pkg, ctx.out_dir)
    report(f"已保存 package.json（服务名：{pkg['positioning']['name']}）")


def _step_xianyu_img(ctx: GenCtx, report: ReportFn) -> None:
    from core import image_factory
    image_factory.gen_xianyu_main(ctx, report)


def _step_xhs_cards(ctx: GenCtx, report: ReportFn) -> None:
    from core import xhs_card
    xhs_card.run_step(ctx, report)


def _step_talk(ctx: GenCtx, report: ReportFn) -> None:
    from core import talk_track
    talk_track.run_step(ctx, report)


ALL_STEPS = [
    StepSpec("package",     "AI 打包全套文案", _step_package, []),
    StepSpec("xianyu_img",  "画闲鱼主图",      _step_xianyu_img, ["package"]),
    StepSpec("xhs_cards",   "渲染小红书卡片",  _step_xhs_cards, ["package"]),
    StepSpec("talk",        "生成话术包+服务卡", _step_talk, ["package"]),
]


def active_specs(equip: dict) -> list[StepSpec]:
    """按勾选装备过滤步骤（package 恒选；闲鱼图跟随 xianyu；卡片跟随 xhs）。"""
    specs = [ALL_STEPS[0]]
    if equip.get("xianyu"):
        specs.append(ALL_STEPS[1])
    if equip.get("xhs"):
        specs.append(ALL_STEPS[2])
    if equip.get("talk"):
        specs.append(ALL_STEPS[3])
    return specs


def make_run_id(skill: str) -> str:
    slug = re.sub(r"[^\w一-鿿]+", "-", skill).strip("-")[:12] or "run"
    return f"{slug}-{time.strftime('%H%M%S')}"


def main() -> None:
    """命令行入口：python -m core.pipeline --role 技术开发 --skill "..." [--case ...]"""
    parser = argparse.ArgumentParser(description="托摆流水线（命令行版）")
    parser.add_argument("--role", default="技术开发")
    parser.add_argument("--skill", required=True)
    parser.add_argument("--case", default="")
    parser.add_argument("--equip", default="package,xianyu,xhs,talk",
                        help="逗号分隔：package,xianyu,xhs,talk")
    args = parser.parse_args()

    equip = {k: True for k in args.equip.split(",") if k.strip()}
    ctx = GenCtx(
        run_id=make_run_id(args.skill),
        out_dir=settings.output_dir / make_run_id(args.skill),
        role=args.role, skill=args.skill, case=args.case, equip=equip,
    )
    ctx.save_form()
    print(f"[开张] run_id={ctx.run_id}")
    state = run_pipeline(ctx, active_specs(equip))
    print(json.dumps(state, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
