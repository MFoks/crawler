from playwright.sync_api import Page
from shared.check_title import check_title
from shared.check_script_source import check_script_in_source
from shared.check_request import check_request
from shared.check_gdpr import check_gdpr
from shared.check_adngin_logs import check_adngin_logs
from shared.capture_prebid_logs import capture_prebid_logs
from shared.enable_debug import enable_debug
from shared.accept_gdpr import accept_gdpr
from shared.check_snigelpubconf import check_snigelpubconf
from shared.check_order_in_source import check_order_in_source
from shared.get_tcf_string import get_tcf_string
from shared.logger_csv import log_to_csv
from shared.get_adngin_modules import get_adngin_modules
from shared.check_request_adngin import check_request_adngin

def check_page(page: Page, site_domain: str, timestamp: str, source: str):
    
    # === 0. SETUP CONSOLE LISTENERS (must be first!) ===
    try:
        check_adngin_logs(page, source=source)
        capture_prebid_logs(page, source=source)
    except Exception as e:
        log_to_csv(source, f"⚠️ Console listener error: {str(e)[:50]}")

    # === 1. CHECK TITLE ===
    try:
        log_to_csv(source, "🔍 Checking page title")
        check_title(page)
        title = page.title()[:60] if page.title() else "No title"
        log_to_csv(source, f"✅ Title: {title}")
    except Exception as e:
        log_to_csv(source, f"⚠️ Title error: {str(e)[:50]}")

    # === 2. WAIT FOR PAGE TO SETTLE ===
    try:
        log_to_csv(source, "⏳ Waiting for page to settle...")
        page.wait_for_load_state("networkidle", timeout=15000)
        page.wait_for_timeout(3000)
    except Exception as e:
        log_to_csv(source, f"⚠️ Page settle timeout (continuing)")

    # === 3. DETECT CMP ===
    cmp_name = None
    try:
        log_to_csv(source, "🔍 Detecting CMP")
        cmp_name = check_gdpr(page)
        if not cmp_name:
            log_to_csv(source, "❌ No recognized CMP detected")
        else:
            log_to_csv(source, f"✅ CMP detected: {cmp_name}")
    except Exception as e:
        log_to_csv(source, f"⚠️ CMP detection error: {str(e)[:50]}")

    # === 4. ACCEPT CONSENT (if CMP found) ===
    if cmp_name:
        try:
            log_to_csv(source, "🔍 Accepting GDPR consent")
            if accept_gdpr(page):
                log_to_csv(source, "✅ GDPR consent accepted")
                page.wait_for_timeout(2000)
            else:
                log_to_csv(source, "⚠️ No consent banner or already accepted")
        except Exception as e:
            log_to_csv(source, f"⚠️ Consent error: {str(e)[:50]}")

        # === 5. GET TCF STRING ===
        try:
            log_to_csv(source, "🔍 Retrieving TCF string")
            get_tcf_string(page, cmp_name, source=source)
            log_to_csv(source, "✅ TCF string retrieved")
        except Exception as e:
            log_to_csv(source, f"⚠️ TCF string error: {str(e)[:50]}")

    # === 6. CHECK LOADER.JS SCRIPT ===
    try:
        log_to_csv(source, "🔍 Checking loader.js in source")
        check_script_in_source(page, script_name="loader.js", site_domain=site_domain, source=source)
    except Exception as e:
        log_to_csv(source, f"⚠️ Script check error: {str(e)[:50]}")

    # === 7. CHECK LOADER.JS REQUEST ===
    try:
        log_to_csv(source, "🔍 Checking loader.js request")
        check_request(page, "loader.js", source=source)
    except Exception as e:
        log_to_csv(source, f"⚠️ Request error: {str(e)[:50]}")

    # === 8. CHECK SNIGELPUBCONF ===
    try:
        log_to_csv(source, "🔍 Checking snigelPubConf")
        check_snigelpubconf(page, source=source)
    except Exception as e:
        log_to_csv(source, f"⚠️ snigelPubConf error: {str(e)[:50]}")

    # === 9. CHECK SCRIPT ORDER ===
    try:
        log_to_csv(source, "🔍 Checking script order")
        check_order_in_source(page, source=source)
    except Exception as e:
        log_to_csv(source, f"⚠️ Script order error: {str(e)[:50]}")

    # === 10. CHECK ADNGIN REQUEST ===
    try:
        log_to_csv(source, "🔍 Checking adngin.js request")
        check_request_adngin(page)
    except Exception as e:
        log_to_csv(source, f"⚠️ Adngin request error: {str(e)[:50]}")

    # === 11. GET ADNGIN MODULES ===
    try:
        log_to_csv(source, "🔍 Getting Adngin modules")
        get_adngin_modules(page, site_domain, timestamp)
        log_to_csv(source, "✅ Adngin modules saved")
    except Exception as e:
        log_to_csv(source, f"⚠️ Adngin modules error: {str(e)[:50]}")

    # === 12. ENABLE DEBUG MODE ===
    try:
        log_to_csv(source, "🔍 Enabling debug mode")
        enable_debug(page, source=source)
    except Exception as e:
        log_to_csv(source, f"⚠️ Debug mode error: {str(e)[:50]}")

    log_to_csv(source, "✅ Page check completed")
