"""名片渲染：HTML → PNG（playwright 截图，文字清晰可控）。

用法：python scripts_render_card.py <card.html> <out.png> [width] [height]
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def render(html_path: str, out_png: str, width: int = 750, height: int = 1334) -> None:
    html = Path(html_path).resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height},
                                device_scale_factor=2)
        page.goto(html)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(400)
        page.screenshot(path=out_png, full_page=False)
        browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python scripts_render_card.py <card.html> <out.png> [w] [h]")
        sys.exit(1)
    w = int(sys.argv[3]) if len(sys.argv) > 3 else 750
    h = int(sys.argv[4]) if len(sys.argv) > 4 else 1334
    render(sys.argv[1], sys.argv[2], w, h)
    print(f"[OK] {sys.argv[2]}")
