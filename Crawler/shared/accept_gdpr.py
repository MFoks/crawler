import time

def accept_gdpr(page):
    """
    Detects and clicks the GDPR consent button if it exists on the page.
    Supports multiple CMP providers including Sourcepoint, OneTrust, Quantcast, etc.
    """
    try:
        # First, check if there's a Sourcepoint iframe and handle it
        if handle_sourcepoint_iframe(page):
            return True

        # Selectors for common GDPR accept buttons (ordered by specificity)
        gdpr_selectors = [
            # Sourcepoint (in main document)
            "button[title='Accept']",
            "button[title='Accept All']",
            "button[title='Agree']",
            "button.sp_choice_type_11",  # Sourcepoint accept button class
            "button.sp_choice_type_ACCEPT_ALL",
            
            # Google Funding Choices
            "#accept-choices",
            ".fc-cta-consent",
            ".fc-button-consent",
            "button.fc-cta-consent",
            
            # Snigel/Adconsent
            ".snigel-cmp-framework button[class*='accept']",
            "#adconsent-usp-bn-ok",
            
            # OneTrust
            "#onetrust-accept-btn-handler",
            "button#onetrust-accept-btn-handler",
            ".onetrust-accept-btn",
            
            # Quantcast
            ".qc-cmp2-summary-buttons button[mode='primary']",
            "button.css-47sehv",  # Quantcast accept
            
            # Didomi
            "#didomi-notice-agree-button",
            "button[aria-label='Agree']",
            
            # Cookiebot
            "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
            "#CybotCookiebotDialogBodyButtonAccept",
            
            # Generic selectors (last resort)
            "button[aria-label*='Accept']",
            "button[aria-label*='Agree']",
            "button[aria-label*='Allow']",
            "button:has-text('Accept All')",
            "button:has-text('Accept all')",
            "button:has-text('Accept')",
            "button:has-text('Agree')",
            "button:has-text('Allow All')",
            "button:has-text('Allow all')",
            "button:has-text('OK')",
            "button:has-text('I Agree')",
            "[class*='accept'] button",
            "[class*='consent'] button[class*='accept']",
            "[class*='consent'] button[class*='agree']",
        ]

        # Iterate through possible selectors and click the first match
        for selector in gdpr_selectors:
            try:
                element = page.query_selector(selector)
                if element and element.is_visible():
                    element.click()
                    print(f"✅ Clicked GDPR consent button: {selector}")
                    page.wait_for_timeout(1000)  # Wait for consent to be processed
                    return True
            except Exception as e:
                continue

        print("❌ No GDPR consent button found in main document.")
        return False

    except Exception as e:
        print(f"❌ Error while accepting GDPR consent: {str(e)}")
        return False


def handle_sourcepoint_iframe(page):
    """
    Handle Sourcepoint CMP which uses an iframe for the consent dialog.
    """
    try:
        # Wait a bit for iframe to load
        page.wait_for_timeout(1000)
        
        # Find Sourcepoint iframe
        iframe_selectors = [
            'iframe[id*="sp_message"]',
            'iframe[src*="sourcepoint"]',
            'iframe[title*="SP Consent"]',
            'iframe[id*="sp_iframe"]',
        ]
        
        for iframe_selector in iframe_selectors:
            iframe_element = page.query_selector(iframe_selector)
            if iframe_element:
                print(f"🔍 Found Sourcepoint iframe: {iframe_selector}")
                
                # Get the iframe's content frame
                frame = iframe_element.content_frame()
                if frame:
                    # Try to find and click accept button inside iframe
                    accept_selectors = [
                        "button[title='Accept']",
                        "button[title='Accept All']",
                        "button[title='Agree']",
                        "button.sp_choice_type_11",
                        "button.sp_choice_type_ACCEPT_ALL",
                        "button[aria-label*='Accept']",
                        "button:has-text('Accept')",
                        "button:has-text('Agree')",
                        "button:has-text('OK')",
                    ]
                    
                    for selector in accept_selectors:
                        try:
                            button = frame.query_selector(selector)
                            if button and button.is_visible():
                                button.click()
                                print(f"✅ Clicked Sourcepoint accept button in iframe: {selector}")
                                page.wait_for_timeout(1000)
                                return True
                        except Exception:
                            continue
                    
                    print("⚠️ Found Sourcepoint iframe but couldn't find accept button")
        
        return False
        
    except Exception as e:
        print(f"⚠️ Error handling Sourcepoint iframe: {str(e)}")
        return False
