"""Browser smoke test for examples/preview.html.

Serves the repository itself and drives the page with Playwright, so it needs
no separate server. Exits non-zero on console errors or a missing widget.
"""

from __future__ import annotations

import functools
import json
import os
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "http://127.0.0.1:8765/examples/preview.html"


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args: object) -> None:
        """Silence the access log."""
        pass


def serve() -> ThreadingHTTPServer:
    handler = functools.partial(_QuietHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 8765), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def main() -> int:
    errors: list[str] = []
    server = serve()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1000, "height": 1400})
        page.on(
            "console",
            lambda msg: errors.append(f"{msg.type}: {msg.text}") if msg.type == "error" else None,
        )
        page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(1500)

        icon_font = page.evaluate(
            """async () => {
              await document.fonts.load('12px layui-icon');
              const face = [...document.fonts].find(
                (font) => font.family.replace(/["']/g, '') === 'layui-icon'
              );
              return face ? face.status : null;
            }"""
        )
        info = page.evaluate(
            """() => {
              const light = document.getElementById('light-host');
              const shadow = document.getElementById('shadow-host').shadowRoot;
              const mount = shadow.querySelector('.law-root');
              const standalone = document.getElementById('standalone-host');
              return {
                lightRoot: light.classList.contains('law-root'),
                formControls: light.querySelectorAll(
                  '.layui-form input, .layui-form select'
                ).length,
                decoratedSelects: light.querySelectorAll('.layui-form-select').length,
                slider: light.querySelectorAll('.layui-slider').length,
                switch: light.querySelectorAll('.layui-form-switch').length,
                colorbox: light.querySelectorAll('.layui-colorpicker').length,
                laydate: light.querySelectorAll('input').length,
                rate: light.querySelectorAll('.layui-rate').length,
                table: light.querySelectorAll('.layui-table-view').length,
                shadowRoot: !!mount,
                shadowStyles: shadow.querySelectorAll('style[data-layui-anywidget="base"]').length,
                docStyles: document.querySelectorAll('style[data-layui-anywidget]').length,
                standaloneDecorated: standalone.querySelectorAll(
                  '.layui-form-select, .layui-form-radio, .layui-form-checkbox'
                ).length,
                standaloneNativeVisible: [
                  ...standalone.querySelectorAll('select, input[type=checkbox], input[type=radio]'),
                ].filter((node) => getComputedStyle(node).display !== 'none').length,
                error: light.querySelector('.law-status-error')?.textContent || null,
                log: document.getElementById('log').textContent.slice(0, 2000),
              };
            }"""
        )
        print(json.dumps(info, ensure_ascii=False, indent=2))
        print("console errors:", json.dumps(errors[:10], ensure_ascii=False, indent=2))
        screenshot = os.environ.get("PREVIEW_SCREENSHOT", "/tmp/preview.png")
        page.screenshot(path=screenshot, full_page=True)
        browser.close()
    server.shutdown()

    checks = {
        "light DOM rendered": info["lightRoot"],
        "form controls rendered": info["formControls"] > 0,
        "select decorated": info["decoratedSelects"] > 0,
        "slider rendered": info["slider"] > 0,
        "table rendered": info["table"] > 0,
        "shadow root rendered": info["shadowRoot"],
        "shadow styles injected": info["shadowStyles"] > 0,
        "icon font loaded": icon_font == "loaded",
        "standalone controls decorated": info["standaloneDecorated"] == 5,
        "standalone native controls hidden": info["standaloneNativeVisible"] == 0,
        "no widget error": info["error"] is None,
        "no console errors": not errors,
    }
    failed = [name for name, ok in checks.items() if not ok]
    for name, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
