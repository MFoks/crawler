def check_gdpr(page):
    try:
        # List of CMP-related objects to check in the browser window
        # Extended to support more CMP providers
        cmp_objects = {
            "_sp_": "sourcepoint",
            "__sp__": "sourcepoint", 
            "googlefc": "googlefc",
            "adconsent": "adconsent",
            "Didomi": "didomi",
            "OneTrust": "onetrust",
            "Cookiebot": "cookiebot",
            "__tcfapi": "tcf_generic"
        }

        detected_cmp = None

        # Check for CMP objects in window
        for obj, cmp_name in cmp_objects.items():
            try:
                is_defined = page.evaluate(f"typeof window.{obj} !== 'undefined'")
                if is_defined:
                    print(f"✅ Found CMP object: window.{obj} -> {cmp_name}")
                    detected_cmp = cmp_name
                    break
            except Exception:
                continue

        # If we found a CMP object, try to identify it more specifically
        if detected_cmp:
            page_html = page.content()

            # Sourcepoint specific checks
            if detected_cmp == "sourcepoint" or "sourcepoint" in page_html.lower() or "sp_message" in page_html:
                print("✅ CMP detected: Sourcepoint")
                return "sourcepoint"

            # Snigel specific checks
            if "snigel-cmp-framework" in page_html or detected_cmp == "adconsent":
                print("✅ CMP detected: Snigel (adconsent)")
                return "adconsent"

            # Google Funding Choices
            if "fc-choice-dialog" in page_html or detected_cmp == "googlefc":
                print("✅ CMP detected: Google Funding Choices (googlefc)")
                return "googlefc"

            # OneTrust
            if "onetrust" in page_html.lower() or detected_cmp == "onetrust":
                print("✅ CMP detected: OneTrust")
                return "onetrust"

            # Didomi
            if "didomi" in page_html.lower() or detected_cmp == "didomi":
                print("✅ CMP detected: Didomi")
                return "didomi"

            # Cookiebot
            if "cookiebot" in page_html.lower() or detected_cmp == "cookiebot":
                print("✅ CMP detected: Cookiebot")
                return "cookiebot"

            # If we have TCF API but couldn't identify specific CMP, check HTML
            if detected_cmp == "tcf_generic":
                # Check for Sourcepoint markers in HTML
                if "sourcepoint" in page_html.lower() or "_sp_" in page_html:
                    print("✅ CMP detected: Sourcepoint (via TCF)")
                    return "sourcepoint"
                print("✅ CMP detected: Generic TCF CMP")
                return "tcf_generic"

            return detected_cmp

        # Fallback: Check for CMP elements in DOM (including iframes)
        print("🔍 Checking DOM for CMP elements...")
        
        # Check for Sourcepoint iframe
        sp_iframe = page.query_selector('iframe[id*="sp_message"], iframe[src*="sourcepoint"]')
        if sp_iframe:
            print("✅ CMP detected: Sourcepoint (iframe found)")
            return "sourcepoint"

        cmp_selectors = [
            ("div[class*='sp_veil']", "sourcepoint"),
            (".qc-cmp2-container", "quantcast"),
            ("#onetrust-consent-sdk", "onetrust"),
            ("#didomi-host", "didomi"),
            ("#CybotCookiebotDialog", "cookiebot"),
            ("div[class*='fc-consent']", "googlefc"),
            ("div[id*='consent']", "others"),
            ("div[class*='cmp']", "others"),
        ]

        for selector, cmp_name in cmp_selectors:
            try:
                element = page.query_selector(selector)
                if element:
                    print(f"✅ Found CMP element: {selector}")
                    print(f"✅ CMP detected: {cmp_name}")
                    return cmp_name
            except Exception:
                continue

        print("❌ No CMP banner found.")
        return None

    except Exception as e:
        print(f"❌ Error while checking CMP: {str(e)}")
        return None
