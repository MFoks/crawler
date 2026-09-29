from playwright.sync_api import Playwright

def check_home_page(playwright: Playwright, url: str):
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(url)
    
    # Sprawdzenie tytułu strony
    title = page.title()
    if title in page.content():
        print(f"Strona główna: Tytuł '{title}' znajduje się w źródle strony.")
    else:
        print(f"Strona główna: Tytuł '{title}' NIE znajduje się w źródle strony.")
    
    # Sprawdzenie, czy URL do googlegpt.js znajduje się w źródle strony
    page_content = page.content()
    if "gpt.js" in page_content and "google" in page_content:
        print("Strona główna: Znaleziono URL do googlegpt.js w źródle strony.")
    else:
        print("Strona główna: NIE znaleziono URL do googlegpt.js w źródle strony.")
    
    # Sprawdzenie, czy jest request do googlegpt.js
    found_gpt_request = False
    def handle_request(request):
        nonlocal found_gpt_request
        if "gpt.js" in request.url and "google" in request.url:
            found_gpt_request = True

    page.on("request", handle_request)
    page.reload(wait_until="networkidle")

    if found_gpt_request:
        print("Strona główna: Znaleziono request do googlegpt.js.")
    else:
        print("Strona główna: NIE znaleziono requestu do googlegpt.js.")
    
    browser.close()
