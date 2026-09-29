from shared.logger_csv import log_to_csv

def check_request(page, script_name: str, source: str):
    found_snigel_request = False
    domain = "snigelweb"
    print("🔍 Watching for requests to:", script_name, "from", domain)

    def handle_request(request):
        nonlocal found_snigel_request
        # Only check for snigelweb requests, ignore others completely
        if script_name in request.url and domain in request.url:
            found_snigel_request = True
            message = f"✅ Request to {script_name} from {domain} found: {request.url}"
            print(message)
            log_to_csv(source, message)

    page.on("request", handle_request)
    
    try:
        page.reload(wait_until="networkidle", timeout=30000)
    except Exception as e:
        print(f"⚠️ Reload timeout, continuing anyway: {str(e)[:50]}")

    if not found_snigel_request:
        message = f"❌ NO request found to {script_name} from domain {domain}."
        print(message)
        log_to_csv(source, message)
