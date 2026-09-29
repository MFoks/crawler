seen_cmp_issues = set()

def check_cmp_issues(log_text):
    if "consentManagement" in log_text and "__uspapi" in log_text:
        issue_message = "No compatible consent management platform API '__uspapi' found."

        if issue_message not in seen_cmp_issues:
            seen_cmp_issues.add(issue_message)
            return issue_message
        else:
            return None

    return None
