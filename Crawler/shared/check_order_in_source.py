from shared.logger_csv import log_to_csv

def check_order_in_source(page, source: str):
    try:
        html_content = page.content()
        snigelPubConf_position = html_content.find("snigelPubConf")
        loader_position = html_content.find("loader.js")

        if snigelPubConf_position == -1 or loader_position == -1:
            msg = "❌ One of the elements is missing in the page source."
            print(msg)
            log_to_csv(source, msg)
            return False

        if snigelPubConf_position < loader_position:
            msg = "✅ 'snigelPubConf' is defined before 'loader.js'."
            print(msg)
            log_to_csv(source, msg)
            return True
        else:
            msg = "❌ 'loader.js' appears before 'snigelPubConf'."
            print(msg)
            log_to_csv(source, msg)
            return False

    except Exception as e:
        msg = f"❌ Error checking order in source: {str(e)}"
        print(msg)
        log_to_csv(source, msg)
        return False
