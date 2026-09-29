import re
from shared.logger_csv import log_to_csv

def check_script_in_source(page, script_name, site_domain, source: str):
    """
    Checks if `loader.js` is correctly loaded from `snigelweb.com`.
    Logs valid and incorrect scripts, including warnings for development versions.
    """
    expected_structure = rf"https://cdn\.snigelweb\.com/adengine/{re.escape(site_domain)}/loader\.js"
    print(f"🔍 Expected script structure: {expected_structure}")

    scripts = page.query_selector_all("script")
    found_scripts = []

    for script in scripts:
        script_src = script.get_attribute("src")

        if script_src and "loader.js" in script_src and "snigelweb.com" in script_src:
            print(f"🔍 Found script from snigelweb: {script_src}")

            if "dev.cdn.snigelweb.com" in script_src:
                dev_message = f"⚠️ This is a **development version**, not a production configuration: {script_src}"
                print(dev_message)
                log_to_csv(source, dev_message)

            if "staging-cdn.snigelweb.com" in script_src:
                staging_message = f"⚠️ This is a **staging environment version**, not a production configuration: {script_src}"
                print(staging_message)
                log_to_csv(source, staging_message)

            if "adengine/master/" in script_src:
                master_message = f"⚠️ This is an incorrect production configuration for the website: {script_src}"
                print(master_message)
                log_to_csv(source, master_message)

            if re.match(expected_structure, script_src):
                log_message = f"✅ Found valid script: {script_src}"
                print(log_message)
                log_to_csv(source, log_message)
                found_scripts.append(script_src)
            else:
                log_message = f"❌ Found script with incorrect structure: {script_src}"
                print(log_message)
                log_to_csv(source, log_message)

    if not found_scripts:
        log_message = f"⚠️ No valid scripts matching '{script_name}' from snigelweb.com were found on the page."
        print(log_message)
        log_to_csv(source, log_message)
