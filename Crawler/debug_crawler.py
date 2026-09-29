#!/usr/bin/env python3
"""
Debug crawler - uruchamia przeglądarkę w trybie widocznym (nie headless)
Wykonuje pełny flow jak główny crawler, ale z wizualnym podglądem.
Użycie: python debug_crawler.py "https://example.com"
"""
import sys
import json
from playwright.sync_api import sync_playwright

# Import shared modules
sys.path.insert(0, '.')
from shared.check_gdpr import check_gdpr
from shared.accept_gdpr import accept_gdpr
from shared.get_tcf_string import get_tcf_string
from shared.check_title import check_title
from shared.check_script_source import check_script_in_source
from shared.check_snigelpubconf import check_snigelpubconf
from shared.check_order_in_source import check_order_in_source
from shared.enable_debug import enable_debug

def run_debug(url: str):
    print(f"\n{'='*60}")
    print(f"🔍 DEBUG CRAWLER - {url}")
    print(f"{'='*60}\n")

    # Extract domain from URL
    from urllib.parse import urlparse
    parsed = urlparse(url)
    site_domain = parsed.netloc.replace('www.', '')

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False,
            slow_mo=300  # Lekkie spowolnienie żeby widzieć co się dzieje
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/113.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        # Logowanie konsoli przeglądarki
        page.on("console", lambda msg: print(f"  [BROWSER] {msg.type}: {msg.text[:100]}") if "adngin" in msg.text.lower() or "snigel" in msg.text.lower() else None)

        # === 1. LOAD PAGE ===
        print("📄 [1/9] Ładowanie strony...")
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            print(f"  ✅ Strona załadowana")
        except Exception as e:
            print(f"  ❌ Błąd ładowania: {e}")
            return

        # === 2. CHECK TITLE ===
        print("\n📄 [2/9] Sprawdzanie tytułu...")
        try:
            check_title(page)
            print(f"  ✅ Tytuł: {page.title()[:50]}...")
        except Exception as e:
            print(f"  ❌ Błąd: {e}")

        # Wait for CMP to load
        print("\n⏳ Czekam 3 sekundy na załadowanie CMP...")
        page.wait_for_timeout(3000)

        # === 3. DETECT CMP ===
        print("\n🔍 [3/9] Wykrywanie CMP...")
        cmp_name = check_gdpr(page)
        if not cmp_name:
            print("  ❌ Nie wykryto CMP! Sprawdzam ręcznie...")
            
            # Manual TCF check
            try:
                tcf_exists = page.evaluate("typeof __tcfapi !== 'undefined'")
                if tcf_exists:
                    print("  ℹ️ __tcfapi istnieje, próbuję pobrać dane...")
                    tcf_info = page.evaluate("""
                        () => new Promise(resolve => {
                            __tcfapi('getTCData', 2, (data, success) => {
                                resolve({success, cmpId: data?.cmpId, cmpStatus: data?.cmpStatus});
                            });
                        })
                    """)
                    print(f"  TCF Info: {tcf_info}")
                    if tcf_info.get('cmpId'):
                        cmp_name = "tcf_generic"
                        print(f"  ✅ Wykryto CMP przez TCF API (ID: {tcf_info.get('cmpId')})")
            except Exception as e:
                print(f"  ❌ Błąd sprawdzania TCF: {e}")
            
            if not cmp_name:
                print("\n  ⚠️ BRAK CMP - crawler by się tutaj zatrzymał!")
                print("  Kontynuuję debug mimo to...\n")
                cmp_name = "unknown"
        else:
            print(f"  ✅ CMP wykryty: {cmp_name}")

        # === 4. ACCEPT CONSENT ===
        print("\n🖱️ [4/9] Akceptacja consent...")
        consent_accepted = accept_gdpr(page)
        if consent_accepted:
            print("  ✅ Consent zaakceptowany!")
            page.wait_for_timeout(2000)
        else:
            print("  ⚠️ Nie znaleziono przycisku akceptacji (może już zaakceptowany?)")

        # === 5. GET TCF STRING ===
        print("\n🔐 [5/9] Pobieranie TCF string...")
        try:
            get_tcf_string(page, cmp_name, source="debug")
        except Exception as e:
            print(f"  ❌ Błąd: {e}")

        # Dodatkowa weryfikacja TCF
        try:
            tcf_data = page.evaluate("""
                () => new Promise((resolve, reject) => {
                    if (typeof __tcfapi === 'undefined') {
                        resolve({error: 'brak __tcfapi'});
                        return;
                    }
                    __tcfapi('getTCData', 2, (data, success) => {
                        resolve({
                            success,
                            tcString: data?.tcString?.substring(0, 50) + '...',
                            cmpId: data?.cmpId,
                            gdprApplies: data?.gdprApplies,
                            eventStatus: data?.eventStatus
                        });
                    });
                })
            """)
            print(f"  TCF Data: {json.dumps(tcf_data, indent=4)}")
        except Exception as e:
            print(f"  ❌ Błąd pobierania TCF: {e}")

        # === 6. CHECK LOADER.JS ===
        print("\n📜 [6/9] Sprawdzanie loader.js...")
        try:
            check_script_in_source(page, script_name="loader.js", site_domain=site_domain, source="debug")
        except Exception as e:
            print(f"  ❌ Błąd: {e}")

        # === 7. CHECK SNIGELPUBCONF ===
        print("\n⚙️ [7/9] Sprawdzanie window.snigelPubConf...")
        try:
            check_snigelpubconf(page, source="debug")
            
            # Pokaż szczegóły
            pubconf = page.evaluate("window.snigelPubConf")
            if pubconf:
                print(f"  ✅ snigelPubConf znaleziony:")
                print(f"     adengine: {pubconf.get('adengine', 'N/A')}")
                print(f"     site: {pubconf.get('site', 'N/A')}")
            else:
                print("  ❌ window.snigelPubConf nie istnieje")
        except Exception as e:
            print(f"  ❌ Błąd: {e}")

        # === 8. CHECK SCRIPT ORDER ===
        print("\n📋 [8/9] Sprawdzanie kolejności skryptów...")
        try:
            check_order_in_source(page, source="debug")
        except Exception as e:
            print(f"  ❌ Błąd: {e}")

        # === 9. CHECK ADNGIN ===
        print("\n📊 [9/9] Sprawdzanie Adngin...")
        try:
            adngin = page.evaluate("typeof window.adngin !== 'undefined'")
            if adngin:
                print("  ✅ window.adngin istnieje")
                adngin_queue = page.evaluate("window.adngin?.queue?.length || 0")
                print(f"     Queue length: {adngin_queue}")
            else:
                print("  ❌ window.adngin nie istnieje")
        except Exception as e:
            print(f"  ❌ Błąd: {e}")

        # === SUMMARY ===
        print("\n" + "="*60)
        print("📊 PODSUMOWANIE")
        print("="*60)
        print(f"  URL: {url}")
        print(f"  CMP: {cmp_name}")
        print(f"  Consent accepted: {'✅' if consent_accepted else '❌'}")
        
        # Final TCF check
        try:
            final_tcf = page.evaluate("typeof __tcfapi !== 'undefined'")
            print(f"  TCF API available: {'✅' if final_tcf else '❌'}")
        except:
            pass

        try:
            has_loader = page.evaluate("document.querySelector('script[src*=\"loader.js\"]') !== null")
            print(f"  loader.js: {'✅' if has_loader else '❌'}")
        except:
            pass

        try:
            has_pubconf = page.evaluate("typeof window.snigelPubConf !== 'undefined'")
            print(f"  snigelPubConf: {'✅' if has_pubconf else '❌'}")
        except:
            pass

        try:
            has_adngin = page.evaluate("typeof window.adngin !== 'undefined'")
            print(f"  adngin: {'✅' if has_adngin else '❌'}")
        except:
            pass

        print("\n" + "="*60)
        print("⏸️  Przeglądarka pozostaje otwarta do inspekcji.")
        print("    Naciśnij Enter aby zamknąć...")
        print("="*60)
        input()

        browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Użycie: python debug_crawler.py 'https://example.com'")
        print("Przykład: python debug_crawler.py 'https://pcgamesn.com'")
        sys.exit(1)

    url = sys.argv[1]
    if not url.startswith("http"):
        url = f"https://{url}"

    run_debug(url)
