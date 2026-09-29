from shared.capture_adngin_logs import capture_adngin_logs
from shared.capture_prebid_logs import capture_prebid_logs
from shared.capture_adngin_warning_logs import capture_adngin_warning_logs
from shared.logger_csv import log_to_csv

def enable_debug(page, source: str):
    try:
        # Wait before enabling debug mode
        page.wait_for_timeout(5000)
        msg = "⏱ Waited for 5 seconds. Now enabling debug mode..."
        print(msg)
        log_to_csv(source, msg)

        # Attach log handlers
        capture_adngin_warning_logs(page, source)

        # Check if adngin.cmd is available
        is_adngin_available = page.evaluate("""
            () => typeof window.adngin !== 'undefined' && typeof window.adngin.cmd !== 'undefined'
        """)

        if not is_adngin_available:
            msg = "⚠️ adngin or adngin.cmd not available on the page. Skipping enableDebug()."
            print(msg)
            log_to_csv(source, msg)
            return

        # Call adngin.cmd.enableDebug()
        page.evaluate("adngin.cmd.enableDebug()")
        msg = "✅ adngin.cmd.enableDebug() executed successfully."
        print(msg)
        log_to_csv(source, msg)

        # Reload the page with timeout handling
        try:
            page.reload(wait_until="networkidle", timeout=30000)
            msg = "🔄 Page reloaded after enabling debug mode."
            print(msg)
            log_to_csv(source, msg)
        except Exception as reload_error:
            msg = f"⚠️ Reload timeout after debug enable (continuing): {str(reload_error)[:50]}"
            print(msg)
            log_to_csv(source, msg)

        # Give logs time to appear
        page.wait_for_timeout(3000)
        msg = "📝 Captured logs from console."
        print(msg)
        log_to_csv(source, msg)

    except Exception as e:
        msg = f"🚨 Error in enable_debug: {str(e)}"
        print(msg)
        log_to_csv(source, msg)
