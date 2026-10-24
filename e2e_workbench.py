"""工作台冒烟：首页 → 找方向（对话）→ 看同行（真实生成报告）→ 开张开卖入口。"""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent / "e2e_shots"


def shot(page, name: str) -> None:
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
    print(f"[截图] {name}.png")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1100})
    page.goto("http://localhost:8501", timeout=60000)
    page.wait_for_selector("text=一人公司工作台", timeout=60000)
    page.wait_for_timeout(1500)
    shot(page, "11_home_workbench")

    # 找方向页
    page.get_by_role("link", name="找方向").click()
    page.wait_for_selector("text=方向顾问", timeout=30000)
    page.wait_for_timeout(800)
    shot(page, "12_explore_chat")
    # 发一条消息（真实 LLM 回复）
    page.get_by_test_id("stChatInputTextArea").fill("我是程序员，会写Python脚本，想做副业")
    page.keyboard.press("Enter")
    page.wait_for_timeout(15000)
    shot(page, "13_explore_reply")

    # 看同行页（真实生成报告 ~20s）
    page.get_by_role("link", name="看同行").click()
    page.wait_for_selector("text=情报报告", timeout=30000)
    inp = page.get_by_placeholder("例：帮人做PPT美化 / AI老照片修复 / 简历优化")
    inp.click()
    page.keyboard.type("Python脚本代写自动化", delay=25)
    page.wait_for_timeout(800)
    page.keyboard.press("Tab")
    page.wait_for_timeout(800)
    page.get_by_role("button", name="生成情报报告").click()
    print("[等待] 报告生成中…")
    page.wait_for_selector("text=这个方向有市场吗", timeout=120000)
    shot(page, "14_market_report")

    # 开张开卖入口正常
    page.get_by_role("link", name="开张开卖").click()
    page.wait_for_selector("text=第 1 步", timeout=30000)
    shot(page, "15_launch_intake")

    browser.close()
    print("[工作台冒烟全通过]")
