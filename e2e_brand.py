"""立人设页交互验证：radio 修复 + 名片真实生成。"""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent / "e2e_shots"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1200})
    page.goto("http://localhost:8501", timeout=60000)
    page.wait_for_selector("text=把技能摆到路边去", timeout=60000)
    page.get_by_role("link", name="立人设", exact=True).click()
    page.wait_for_selector("text=名片风格", timeout=30000)
    # radio 应正常渲染（不再 KeyError）
    assert page.get_by_text("暗色科技风").count() >= 1, "radio 未渲染"
    # 填表单（text_input 用 fill 后 blur）
    name_input = page.get_by_label("昵称/署名")
    name_input.click(); page.keyboard.type("俊哥", delay=25); page.keyboard.press("Tab")
    page.wait_for_timeout(600)
    tag = page.get_by_label("一句话介绍")
    tag.click(); page.keyboard.type("帮小店主用AI提效的技术搭子", delay=20); page.keyboard.press("Tab")
    page.wait_for_timeout(800)
    page.screenshot(path=str(OUT / "31_brand_filled.png"), full_page=True)
    # 生成名片
    page.get_by_role("button", name="生成名片").click()
    print("[等待] 名片渲染（约10秒）…")
    page.wait_for_selector("text=下载名片", timeout=90000)
    page.wait_for_timeout(800)
    page.screenshot(path=str(OUT / "32_brand_card.png"), full_page=True)
    print("[立人设页交互+名片生成 PASS]")
    browser.close()
