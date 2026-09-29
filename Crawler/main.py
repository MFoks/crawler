import sys
import json
import logging
from pathlib import Path
from urllib.parse import urlparse
from typing import Union
from playwright.sync_api import sync_playwright
from utils.page import check_page
from utils.ads_txt import check_ads_txt
from shared.logger_csv import init_log_file, log_to_csv
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")

TEMP_FILE = "/tmp/urls_temp.txt"

def create_urls_file_from_domain(domain: str, article: Union[str, None] = None) -> str:
    parsed = urlparse(domain)
    base = parsed.netloc or domain.split("/")[0]
    homepage_url = f"https://{base}"
    page_url = f"https://{article}" if article and not article.startswith("http") else article
    ads_txt_url = f"https://{base}/ads.txt"
    urls = [homepage_url, page_url or "", ads_txt_url]
    Path(TEMP_FILE).write_text("\n".join(urls))
    return TEMP_FILE

def read_urls_from_file(file_path: str):
    try:
        with open(file_path, 'r') as file:
            lines = [line.strip() for line in file.readlines()]
            if len(lines) < 3 or not lines[0] or not lines[2]:
                raise ValueError("File must contain at least homepage and ads.txt URLs.")
            return lines
    except Exception as e:
        logger.error(f"Failed to read file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Usage: python main.py '<JSON_PAYLOAD>'")
        sys.exit(1)

    try:
        payload = json.loads(sys.argv[1])
        main_domain = payload["homepage"]
        article_url = payload.get("article")
        ads_entries = payload.get("adsEntries", [])
    except Exception as e:
        logger.error("❌ Invalid input format. Expected JSON.")
        sys.exit(1)

    urls_file = create_urls_file_from_domain(main_domain, article_url)
    home_url, page_url, ads_txt_url = read_urls_from_file(urls_file)

    site_domain = urlparse(home_url).netloc.replace("www.", "")
    init_log_file(home_url)

    # Initial system logs - these appear immediately
    log_to_csv("system", "🚀 Crawler started")
    log_to_csv("system", f"🌐 Domain: {site_domain}")
    log_to_csv("system", f"🏠 Homepage: {home_url}")
    if page_url:
        log_to_csv("system", f"📄 Article: {page_url}")
    log_to_csv("system", f"📋 ads.txt: {ads_txt_url}")
    log_to_csv("system", "⏳ Initializing browser...")

    with sync_playwright() as playwright:
        log_to_csv("system", "🌐 Launching Chromium browser...")
        browser = playwright.chromium.launch(headless=True)
        log_to_csv("system", "✅ Browser launched successfully")

        # Desktop User Agent
        desktop_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/113.0.0.0 Safari/537.36"
        
        # Mobile User Agent
        mobile_user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"

        # HOME PAGE - DESKTOP
        log_to_csv("system", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        log_to_csv("homePageDesktop", "🏠 [1/4] HOMEPAGE - Desktop")
        log_to_csv("homePageDesktop", "⏳ Creating browser context...")
        context_home_desktop = browser.new_context(user_agent=desktop_user_agent)
        page_home_desktop = context_home_desktop.new_page()
        log_to_csv("homePageDesktop", f"⏳ Loading {home_url}...")
        page_home_desktop.goto(home_url, wait_until="networkidle", timeout=60000)
        log_to_csv("homePageDesktop", "✅ Page loaded, running checks...")
        check_page(page_home_desktop, site_domain, timestamp, source="homePageDesktop")
        context_home_desktop.close()
        log_to_csv("homePageDesktop", "✅ Desktop homepage scan complete")

        # HOME PAGE - MOBILE
        log_to_csv("system", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        log_to_csv("homePageMobile", "📱 [2/4] HOMEPAGE - Mobile")
        log_to_csv("homePageMobile", "⏳ Creating mobile browser context...")
        context_home_mobile = browser.new_context(
            user_agent=mobile_user_agent,
            viewport={'width': 375, 'height': 667},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True
        )
        page_home_mobile = context_home_mobile.new_page()
        log_to_csv("homePageMobile", f"⏳ Loading {home_url}...")
        page_home_mobile.goto(home_url, wait_until="networkidle", timeout=60000)
        log_to_csv("homePageMobile", "✅ Page loaded, running checks...")
        check_page(page_home_mobile, site_domain, timestamp, source="homePageMobile")
        context_home_mobile.close()
        log_to_csv("homePageMobile", "✅ Mobile homepage scan complete")

        # SUBPAGE - DESKTOP
        if page_url and page_url != home_url:
            log_to_csv("system", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            log_to_csv("subPageDesktop", "📄 [3/4] SUBPAGE - Desktop")
            log_to_csv("subPageDesktop", "⏳ Creating browser context...")
            context_article_desktop = browser.new_context(user_agent=desktop_user_agent)
            page_article_desktop = context_article_desktop.new_page()
            log_to_csv("subPageDesktop", f"⏳ Loading {page_url}...")
            page_article_desktop.goto(page_url, wait_until="networkidle", timeout=60000)
            log_to_csv("subPageDesktop", "✅ Page loaded, running checks...")
            check_page(page_article_desktop, site_domain, timestamp, source="subPageDesktop")
            context_article_desktop.close()
            log_to_csv("subPageDesktop", "✅ Desktop subpage scan complete")

            # SUBPAGE - MOBILE
            log_to_csv("system", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            log_to_csv("subPageMobile", "📱 [4/4] SUBPAGE - Mobile")
            log_to_csv("subPageMobile", "⏳ Creating mobile browser context...")
            context_article_mobile = browser.new_context(
                user_agent=mobile_user_agent,
                viewport={'width': 375, 'height': 667},
                device_scale_factor=2,
                is_mobile=True,
                has_touch=True
            )
            page_article_mobile = context_article_mobile.new_page()
            log_to_csv("subPageMobile", f"⏳ Loading {page_url}...")
            page_article_mobile.goto(page_url, wait_until="networkidle", timeout=60000)
            log_to_csv("subPageMobile", "✅ Page loaded, running checks...")
            check_page(page_article_mobile, site_domain, timestamp, source="subPageMobile")
            context_article_mobile.close()
            log_to_csv("subPageMobile", "✅ Mobile subpage scan complete")
        else:
            log_to_csv("system", "ℹ️ No subpage provided, skipping subpage checks")

        log_to_csv("system", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        log_to_csv("system", "🔒 Closing browser...")
        browser.close()
        log_to_csv("system", "✅ Browser closed")

    # ads.txt check
    log_to_csv("system", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log_to_csv("adsTxt", f"📋 Checking ads.txt: {ads_txt_url}")
    logger.info(f"\n🔍 Checking ads.txt: {ads_txt_url}")
    check_ads_txt(ads_txt_url, ads_entries)
    
    log_to_csv("system", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log_to_csv("system", "🎉 Crawler finished successfully!")
