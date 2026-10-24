"""预生成 3 个示例角色成品到 examples/（演示兜底 + Step0 角色卡数据源）。

用法：python -X utf8 scripts_pregen.py [slug ...]   # 不带参数跑全部
已有成品且 --force 未指定时跳过。
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import settings  # noqa: E402
from core import pipeline  # noqa: E402

EXAMPLES = {
    "crawler_engineer": ("技术开发", "帮人写 Python 爬虫脚本，数据采集自动化，3 天交付",
                         "曾帮电商客户采集 10 万条竞品数据"),
    "ppt_designer": ("设计创意", "帮人把丑 PPT 做成高级感汇报页，职场汇报/竞标路演都接",
                     "做过 40+ 份汇报 PPT，含 3 场竞标路演"),
    "resume_coach": ("文案写作", "帮求职者改简历，24 小时出稿，猎头视角逐句打磨",
                     "改过 60+ 份简历，多人拿到大厂面试"),
}


def pregen(slug: str, force: bool = False) -> None:
    role, skill, case = EXAMPLES[slug]
    dest = settings.examples_dir / slug
    if dest.exists() and (dest / "package.json").exists() and not force:
        print(f"[跳过] {slug}（已有成品）")
        return
    run_id = pipeline.make_run_id(skill)
    out_dir = settings.output_dir / run_id
    ctx = pipeline.GenCtx(run_id=run_id, out_dir=out_dir, role=role, skill=skill,
                          case=case, equip={"xianyu": True, "xhs": True, "talk": True})
    ctx.save_form()
    print(f"[开张] {slug} → {run_id}")
    state = pipeline.run_pipeline(ctx, pipeline.active_specs(ctx.equip))
    failed = [k for k, v in state.get("steps", {}).items() if v != "done"]
    if failed:
        print(f"[失败] {slug} 未完成步骤: {failed}，不复制到 examples/")
        return
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(out_dir, dest)
    # 标记为演示数据（Step4 隐藏闲鱼发布按钮）
    state_path = dest / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["demo"] = True
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[完成] {slug} → examples/{slug}/")


def main() -> None:
    force = "--force" in sys.argv
    slugs = [a for a in sys.argv[1:] if not a.startswith("--")] or list(EXAMPLES)
    for slug in slugs:
        pregen(slug, force=force)
    print("全部完成")


if __name__ == "__main__":
    main()
