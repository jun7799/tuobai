"""全站回归：所有页面渲染 + 关键交互冒烟（不跑长的生成流程）。"""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent / "e2e_shots"
CHECKS = [
    # (侧边栏页面名, 页面内等待出现的文本, 截图名)
    ("工作台", "把技能摆到路边去", "20_home"),
    ("找方向", "方向顾问", "21_explore"),
    ("看同行", "情报报告", "22_market"),
    ("立人设", "个人名片", "23_brand"),
    ("攒客户", "AI 报价助手", "24_leads"),
    ("上架服务", "第 1 步", "28_launch"),
    ("推广服务", "公众号文章", "29_promote"),
    ("记账", "其他 agent 记", "25_finance"),
    ("工作日志", "经营回顾", "26_worklog"),
    ("关张转职", "关张清算报告", "27_shutdown"),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1100})
    page.goto("http://localhost:8501", timeout=60000)
    page.wait_for_load_state("networkidle")
    failed = []
    for nav_name, wait_text, shot_name in CHECKS:
        try:
            page.get_by_role("link", name=nav_name, exact=True).click()
            page.wait_for_selector(f"text={wait_text}", timeout=30000)
            page.wait_for_timeout(600)
            page.screenshot(path=str(OUT / f"{shot_name}.png"), full_page=True)
            print(f"[PASS] {nav_name}")
        except Exception as e:  # noqa: BLE001
            failed.append(nav_name)
            print(f"[FAIL] {nav_name}: {type(e).__name__} {str(e)[:100]}")
    browser.close()
    print("RESULT:", "ALL PASS" if not failed else f"FAILED: {failed}")
