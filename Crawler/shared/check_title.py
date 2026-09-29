def check_title(page):
    title = page.title()
    if title in page.content():
        print(f"Page Title '{title}'")
    else:
        print(f"Page Title  '{title}'")
