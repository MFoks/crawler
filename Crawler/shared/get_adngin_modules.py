import json
from pathlib import Path
from playwright.sync_api import Page

def get_adngin_modules(page: Page, domain: str, timestamp: str):
    try:
        page.wait_for_function("window.adngin && adngin.cmd && adngin.cmd.getConfig", timeout=5000)

        modules = page.evaluate("""
            () => {
                try {
                    const config = adngin.cmd.getConfig();
                    return config && config.modules ? config.modules : null;
                } catch (e) {
                    return { error: e.toString() };
                }
            }
        """)

        filename = f"{domain}_{timestamp}.json"
        modules_dir = Path("logs/modulesinfo")
        modules_dir.mkdir(parents=True, exist_ok=True)
        log_path = modules_dir / filename

        if log_path.exists():
            print(f"[adngin] Skipping module log, already exists: {log_path}")
            return

        if not modules or 'error' in modules:
            error_msg = modules.get('error') if modules else "Modules not available"
            log_path.write_text(json.dumps({"error": error_msg}, indent=2))
        else:
            log_path.write_text(json.dumps(modules, indent=2))

        print(f"[adngin] Modules saved to {log_path}")

    except Exception as e:
        print(f"[adngin] Exception while checking modules: {e}")
