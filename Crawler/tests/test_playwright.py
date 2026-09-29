from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://interia.pl")

    #Get site title
    title = page.title()
    print(f"Site Title: {title}")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)