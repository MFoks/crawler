from shared.logger_csv import log_to_csv

def check_snigelpubconf(page, source: str):
    try:
        # Check if 'snigelPubConf' exists in the window object
        in_window = page.evaluate("""
            (function() {
                return typeof window.snigelPubConf !== 'undefined';
            })();
        """)

        # Check if 'snigelPubConf' exists in the page source
        html_content = page.content()
        in_source = "snigelPubConf" in html_content

        # Evaluate the results
        if in_window and in_source:
            msg = "✅ 'snigelPubConf' exists both in the window object and in the page source."
            print(msg)
            log_to_csv(source, msg)
            return True
        elif in_window:
            msg = "✅ 'snigelPubConf' exists in the window object but not in the page source."
            print(msg)
            log_to_csv(source, msg)
            return True
        elif in_source:
            msg = "✅ 'snigelPubConf' exists in the page source but not in the window object."
            print(msg)
            log_to_csv(source, msg)
            return True
        else:
            msg = "❌ 'snigelPubConf' does not exist in either the window object or the page source."
            print(msg)
            log_to_csv(source, msg)
            return False

    except Exception as e:
        msg = f"❌ Error checking 'snigelPubConf': {str(e)}"
        print(msg)
        log_to_csv(source, msg)
        return False
