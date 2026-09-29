import re
from shared.logger_csv import log_to_csv
from urllib.parse import urlparse, parse_qs

def check_request_adngin(page):
    found_request = False
    experiment_detected = False
    experiment_domain_pattern = re.compile(r"^feature\d*-adengine\.snigelweb\.com$")
    print("🔍 Watching for requests to adngin.js")

    def handle_request(request):
        nonlocal found_request, experiment_detected
        url = request.url
        parsed = urlparse(url)

        if "adngin.js" in parsed.path:
            found_request = True
            domain = parsed.netloc
            qs = parse_qs(parsed.query)
            message = f"✅ Request to adngin.js found: {url}"

            if experiment_domain_pattern.match(domain):
                experiment_detected = True
                message += " 🚧 [Experiment domain: featureX-ade.sng.com]"

            if 'exp' in qs:
                experiment_detected = True
                message += f" 🚧 [Experiment param: exp={qs['exp'][0]}]"

            print(message)
            log_to_csv("adngin-request", message)

    page.on("request", handle_request)
    
    try:
        page.reload(wait_until="networkidle", timeout=30000)
    except Exception as e:
        print(f"⚠️ Reload timeout, continuing anyway: {str(e)[:50]}")

    if not found_request:
        message = "❌ NO request found to adngin.js."
        print(message)
        log_to_csv("adngin-request", message)
    elif not experiment_detected:
        message = "ℹ️ Request found, but no experiment indicators (featureX domain or ?exp= param)."
        print(message)
        log_to_csv("adngin-request", message)
