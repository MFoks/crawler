from shared.get_tcf_object import get_tcf_object
from shared.logger_csv import log_to_csv

def get_tcf_string(page, cmp_name: str, source: str):
    tc_string = get_tcf_object(page, cmp_name)
    if tc_string:
        msg = f"✅ Final tcString: {tc_string}"
        print(msg)
        log_to_csv(source, msg)
    else:
        msg = f"❌ Failed to retrieve tcString from {cmp_name}."
        print(msg)
        log_to_csv(source, msg)
