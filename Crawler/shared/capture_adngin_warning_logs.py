from shared.loggers.check_missing_ad_units import check_missing_ad_units
from shared.loggers.check_cmp_issues import check_cmp_issues
from shared.logger_csv import log_to_csv

seen_logs = set()

def normalize_log_key(log_msg: str) -> str:
    return (
        log_msg.lower()
        .replace("🚨", "")
        .replace('"', "")
        .replace("“", "")
        .replace("”", "")
        .replace("'", "")
        .replace("`", "")
        .replace("’", "")
        .replace("‘", "")
        .strip()
    )

def capture_adngin_warning_logs(page, source: str):
    """
    Captures console warning logs related to [adngin] and processes:
    - Missing ad units
    - CMP-related issues
    - Logs all captured warnings into CSV (deduplicated).
    """

    try:
        def handle_adngin_warnings(msg):
            try:
                log_type = msg.type
                log_text = msg.text

                if log_type == "warning":
                    print(f"⚠️ Warning in Console: {log_text}")

                    missing_ad_unit = check_missing_ad_units(log_text, source)
                    if missing_ad_unit:
                        key = normalize_log_key(missing_ad_unit)
                        if key not in seen_logs:
                            seen_logs.add(key)
                            print(f"🚨 {missing_ad_unit}")
                            log_to_csv(source, missing_ad_unit)

                    cmp_issue = check_cmp_issues(log_text)
                    if cmp_issue:
                        key = normalize_log_key(cmp_issue)
                        if key not in seen_logs:
                            seen_logs.add(key)
                            print(f"🚨 CMP Issue: {cmp_issue}")
                            log_to_csv(source, cmp_issue)

            except Exception as e:
                error_message = f"🚨 Error processing log: {str(e)}"
                key = normalize_log_key(error_message)
                if key not in seen_logs:
                    seen_logs.add(key)
                    print(error_message)
                    log_to_csv(source, error_message)

        page.on("console", handle_adngin_warnings)
        print("Started capturing [adngin] warning logs.")

    except Exception as e:
        error_message = f"🚨 Error in capture_adngin_warning_logs: {str(e)}"
        key = normalize_log_key(error_message)
        if key not in seen_logs:
            seen_logs.add(key)
            print(error_message)
            log_to_csv(source, error_message)
