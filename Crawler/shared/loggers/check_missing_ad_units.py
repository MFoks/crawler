import re
from shared.logger_csv import log_to_csv

def check_missing_ad_units(log_text, source: str):
    match = re.search(r"lot \((adngin-[^:]+):([^)\s]+)\)", log_text)
    if match:
        container_id = match.group(1)
        ad_unit_name = match.group(2)
        
        log_message = f'🚨 Missing Ad Container: couldn\'t find the container "{container_id}" for the Ad Unit "{ad_unit_name}"'
        log_to_csv(source, log_message)
        
        return log_message
    
    return None
