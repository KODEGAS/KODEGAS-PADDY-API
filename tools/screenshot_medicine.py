from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8000/static/medicine_info_crud.html"
OUT = "medicine_page.png"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width":1280, "height":900})
    print(f"Opening {URL} ...")
    page.goto(URL, timeout=30000)
    # wait a bit for async JS to run
    page.wait_for_timeout(1200)
    page.screenshot(path=OUT, full_page=True)
    print(f"Saved screenshot to {OUT}")
    browser.close()
