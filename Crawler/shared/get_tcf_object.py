def get_tcf_object(page, cmp_name):
    print(f'🔍 Getting TCF string for CMP: {cmp_name}')
    try:
        if cmp_name == "googlefc":
            # Google Funding Choices uses callbackQueue
            tc_string = page.evaluate("""
                () => {
                    return new Promise((resolve, reject) => {
                        const timeout = setTimeout(() => {
                            reject('Timeout waiting for Google FC TCF data');
                        }, 10000);
                        
                        if (typeof window.googlefc !== 'undefined' && window.googlefc.callbackQueue) {
                            window.googlefc.callbackQueue.push({
                                'CONSENT_DATA_READY': () => {
                                    __tcfapi('addEventListener', 2.2, (data, success) => {
                                        clearTimeout(timeout);
                                        if (success) {
                                            resolve(data.tcString);
                                        } else {
                                            reject('Failed to retrieve TCF data from googlefc.');
                                        }
                                    });
                                }
                            });
                        } else {
                            clearTimeout(timeout);
                            reject('googlefc or callbackQueue is not defined on the page.');
                        }
                    });
                }
            """)
            return tc_string

        else:
            # Standard TCF API - works for Sourcepoint, Quantcast, OneTrust, etc.
            tc_string = page.evaluate("""
                () => {
                    return new Promise((resolve, reject) => {
                        const timeout = setTimeout(() => {
                            reject('Timeout waiting for TCF data');
                        }, 10000);

                        if (typeof __tcfapi === 'undefined') {
                            clearTimeout(timeout);
                            reject('__tcfapi is not defined');
                            return;
                        }

                        // Try getTCData first (TCF 2.0/2.2)
                        __tcfapi('getTCData', 2, (tcData, success) => {
                            if (success && tcData && tcData.tcString) {
                                clearTimeout(timeout);
                                console.log('TCF data retrieved successfully:', tcData.cmpId);
                                resolve(tcData.tcString);
                            } else {
                                // Fallback to addEventListener
                                __tcfapi('addEventListener', 2, (data, success2) => {
                                    clearTimeout(timeout);
                                    if (success2 && data && data.tcString) {
                                        console.log('TCF data via addEventListener:', data.cmpId);
                                        resolve(data.tcString);
                                    } else {
                                        reject('Failed to retrieve TCF data.');
                                    }
                                });
                            }
                        });
                    });
                }
            """)
            return tc_string

    except Exception as e:
        print(f"❌ Error retrieving tcString from {cmp_name}: {str(e)}")
        return None
