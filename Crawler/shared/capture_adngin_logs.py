def capture_adngin_logs(page):
    try:
        def handle_adngin_logs(msg):
            try:
                # Capture [adngin] logs based on their type and content
                log_type = msg.type
                log_text = msg.text
                if "【adngin】" in log_text:
                    print(f"💡 [adngin] Log [{log_type}]: {log_text}")

                # Highlight errors and debug logs
                if log_type == "error":
                    print(f"❌ Error in [adngin]: {log_text}")
                elif log_type == "debug":
                    print(f"🔍 Debug in [adngin]: {log_text}")

            except Exception as e:
                print(f"Error processing [adngin] log: {e}")

        # Attach the console event handler
        page.on("console", handle_adngin_logs)
        print("Started capturing [adngin] logs.")
    except Exception as e:
        print(f"Error in capture_adngin_logs: {str(e)}")
