"""E2E：四步向导全流程（欢迎→表单→勾装备→生成→成果页）。需 8501 端口已运行面板。"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent / "e2e_shots"
OUT.mkdir(exist_ok=True)


def shot(page, name: str) -> None:
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
    print(f"[截图] {name}.png")


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.goto("http://localhost:8501", timeout=60000)
        page.wait_for_load_state("networkidle")
        # Streamlit 首帧
        page.wait_for_selector("text=一个人，也是一家公司", timeout=60000)
        shot(page, "01_welcome")

        # Step1
        page.get_by_role("button", name="用我自己的技能开张").click()
        page.wait_for_selector("text=第 1 步", timeout=30000)
        page.locator("button", has_text="技术开发").click()
        page.wait_for_timeout(1200)
        ta = page.get_by_placeholder("例：帮人写爬虫脚本，数据采集自动化，3 天交付")
        ta.click()
        page.keyboard.type("帮宠物店做AI萌宠海报，照片转插画风格，48小时出图", delay=25)
        page.wait_for_timeout(1000)  # 等 debounce 同步
        page.keyboard.press("Tab")   # blur 触发提交
        page.wait_for_timeout(600)
        # 确认值已同步：textarea 值应为输入文本
        assert "帮宠物店" in ta.input_value(), "text_area 值未保留"
        shot(page, "02_intake")
        page.get_by_role("button", name="下一步").click()

        # Step2
        page.wait_for_selector("text=第 2 步", timeout=30000)
        shot(page, "03_select")
        page.get_by_role("button", name="开始生成").click()

        # Step3：等待全部生成完成（打包35s+图25s+渲染15s，裕量240s）
        page.wait_for_selector("text=开张流水线", timeout=30000)
        shot(page, "04_pipeline_running")
        print("[等待] 生成中（最长 240s）…")
        page.wait_for_selector("text=查看成果", timeout=240000)
        shot(page, "05_pipeline_done")
        page.get_by_role("button", name="查看成果").click()

        # Step4
        page.wait_for_selector("text=开张大吉", timeout=30000)
        page.wait_for_timeout(1500)
        shot(page, "06_result_service")
        page.get_by_role("tab", name="闲鱼商品").click()
        page.wait_for_timeout(800)
        shot(page, "07_result_xianyu")
        page.get_by_role("tab", name="小红书笔记").click()
        page.wait_for_timeout(800)
        shot(page, "08_result_xhs")
        browser.close()
        print("[E2E 全流程通过]")
        return 0


if __name__ == "__main__":
    sys.exit(main())
