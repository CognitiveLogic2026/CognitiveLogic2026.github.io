#!/usr/bin/env python3
"""Render tools/og-images/qen-homepage-og.html to img/qen-homepage-og.png at 1200x630."""
import pathlib
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
HTML = HERE / "qen-homepage-og.html"
OUT = HERE.parent.parent / "img" / "qen-homepage-og.png"

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    page = browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
    page.goto(HTML.as_uri())
    page.wait_for_timeout(300)
    page.screenshot(path=str(OUT))
    browser.close()

print(f"Wrote {OUT}")
