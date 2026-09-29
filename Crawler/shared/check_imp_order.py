def check_imp_order(page):
    try:
        # Check if 'snigelPubConf' exists
        snigelPubConf_exists = check_snigelpubconf(page)
        
        # Check if 'loader.js' is correctly added
        loader_correct = check_script_in_source(page, script_name="loader.js", site_domain="example.com")

        # If both conditions are met, check the order in the source
        if snigelPubConf_exists and loader_correct:
            print("✅ Both 'snigelPubConf' and 'loader.js' conditions are satisfied. Checking order...")
            check_order_in_source(page)
        else:
            print("❌ Conditions not met. Skipping order check.")
    
    except Exception as e:
        print(f"Error in check_conditions_and_order: {str(e)}")
