from shared.logger_csv import log_to_csv

def capture_prebid_logs(page, source: str = "system"):
    """
    Captures console logs related to Prebid.js and logs important ones to CSV.
    """
    try:
        def handle_prebid_logs(msg):
            try:
                log_type = msg.type
                log_text = msg.text
                
                # Only process Prebid-related logs
                if "prebid" in log_text.lower() or "pbjs" in log_text.lower():
                    
                    # Log errors
                    if log_type == "error":
                        print(f"❌ [Prebid] Error: {log_text[:100]}")
                        log_to_csv(source, f"❌ Prebid error: {log_text[:100]}")
                    
                    # Log warnings
                    elif log_type == "warning":
                        print(f"⚠️ [Prebid] Warning: {log_text[:100]}")
                        log_to_csv(source, f"⚠️ Prebid warning: {log_text[:100]}")
                    
                    # Log important info (bid responses, auctions)
                    elif any(kw in log_text.lower() for kw in ["bid", "auction", "won", "timeout", "no bid"]):
                        print(f"💰 [Prebid]: {log_text[:100]}")
                        if "no bid" in log_text.lower() or "timeout" in log_text.lower():
                            log_to_csv(source, f"⚠️ Prebid: {log_text[:80]}")

            except Exception as e:
                print(f"Error processing Prebid log: {e}")

        page.on("console", handle_prebid_logs)
        print("✅ Prebid console listener attached")

    except Exception as e:
        print(f"Error setting up Prebid log capture: {str(e)}")
