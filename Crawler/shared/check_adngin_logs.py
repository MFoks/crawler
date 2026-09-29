from shared.logger_csv import log_to_csv

def check_adngin_logs(page, source: str = "system"):
    """
    Captures console logs related to adngin and logs important ones to CSV.
    """
    try:
        def handle_console_message(msg):
            try:
                log_type = msg.type
                log_text = msg.text

                # Only process adngin-related logs
                if "adngin" in log_text.lower() or "snigel" in log_text.lower():
                    
                    # Log errors
                    if log_type == "error":
                        print(f"❌ [adngin] Error: {log_text[:100]}")
                        log_to_csv(source, f"❌ Adngin error: {log_text[:100]}")
                    
                    # Log warnings
                    elif log_type == "warning":
                        print(f"⚠️ [adngin] Warning: {log_text[:100]}")
                        log_to_csv(source, f"⚠️ Adngin warning: {log_text[:100]}")
                    
                    # Log important info (ad loaded, bid won, etc.)
                    elif any(kw in log_text.lower() for kw in ["loaded", "rendered", "bid", "auction", "slot"]):
                        print(f"ℹ️ [adngin]: {log_text[:100]}")

            except Exception as e:
                print(f"Error processing console message: {e}")

        page.on("console", handle_console_message)
        print("✅ Adngin console listener attached")

    except Exception as e:
        print(f"Error setting up adngin log capture: {str(e)}")
