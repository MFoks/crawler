import requests
from shared.logger_csv import log_to_csv

def check_ads_txt(url: str, entries: list[str]):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/113.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            content = response.text
            if not entries:
                log_to_csv("adsTxt", "ℹ️ No entries provided for ads.txt check.")
                return

            for entry in entries:
                if entry.strip() in content:
                    msg = f"✅ ads.txt: Entry '{entry.strip()}' FOUND at {url}"
                else:
                    msg = f"❌ ads.txt: Entry '{entry.strip()}' NOT FOUND at {url}"
                print(msg)
                log_to_csv("adsTxt", msg)
        else:
            msg = f"❌ ads.txt: HTTP {response.status_code} — file unavailable at {url}"
            print(msg)
            log_to_csv("adsTxt", msg)
    except Exception as e:
        msg = f"❌ ads.txt: Error at {url} — {str(e)}"
        print(msg)
        log_to_csv("adsTxt", msg)
