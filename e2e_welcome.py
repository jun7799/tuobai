"""快速验证：欢迎页三张示例卡点亮。"""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent / "e2e_shots"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1200})
    page.goto("http://localhost:8501", timeout=60000)
    page.wait_for_selector("text=一个人，也是一家公司", timeout=60000)
    page.wait_for_timeout(1000)
    page.screenshot(path=str(OUT / "09_welcome_final.png"), full_page=True)
    cards = page.locator("text=已生成全套装备").count()
    print(f"[欢迎页] 示例卡点亮数: {cards}")
    # 点一张示例卡看成品
    page.get_by_role("button", name="查看「爬虫工程师」的成果").click()
    page.wait_for_selector("text=开张大吉", timeout=30000)
    page.wait_for_timeout(1500)
    page.screenshot(path=str(OUT / "10_example_result.png"), full_page=True)
    print("[示例卡] 爬虫工程师成果页打开成功")
    browser.close()
