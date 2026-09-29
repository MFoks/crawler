from pathlib import Path
import csv
import json
import re

def generate_feedback_from_logfile(log_file: Path) -> dict:
    logs_feedback = {
        "homePage": {
            "desktop": [],
            "mobile": []
        },
        "subPage": {
            "desktop": [],
            "mobile": []
        }
    }
    adngin_modules = {}
    diagnostics = {
        "cmp": None,
        "tcfStringValid": None,
        "adnginExperimentEnabled": None
    }

    if not log_file.exists():
        return {
            "crawlerFeedback": {
                "logsFeedback": logs_feedback,
                "adnginModules": adngin_modules,
                "diagnostics": diagnostics
            }
        }

    with log_file.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 2:
                continue
            source, line = row
            source = source.strip()
            line = line.strip()

            # Skip comment lines
            if source.startswith("#"):
                continue

            # Map sources to page type and device type
            page_type = None
            device_type = None
            
            if source == "homePageDesktop":
                page_type = "homePage"
                device_type = "desktop"
            elif source == "homePageMobile":
                page_type = "homePage" 
                device_type = "mobile"
            elif source == "subPageDesktop":
                page_type = "subPage"
                device_type = "desktop"
            elif source == "subPageMobile":
                page_type = "subPage"
                device_type = "mobile"
            elif source == "adngin-request":
                if "✅ Request to adngin.js" in line:
                    logs_feedback["homePage"]["desktop"].append("✅ adngin.js loaded")
                elif "❌" in line:
                    logs_feedback["homePage"]["desktop"].append(line)
                continue
            elif source == "system":
                continue
            
            if page_type is None or device_type is None:
                continue

            # === EXTRACT MESSAGES ===
            
            # CMP
            if "CMP detected:" in line:
                match = re.search(r"CMP detected:\s*(\w+)", line)
                if match:
                    diagnostics["cmp"] = match.group(1)
                    logs_feedback[page_type][device_type].append(f"✅ CMP: {diagnostics['cmp']}")

            elif "No recognized CMP" in line or "No CMP" in line:
                diagnostics["cmp"] = None
                logs_feedback[page_type][device_type].append("❌ No CMP detected")

            # Consent
            elif "GDPR consent accepted" in line:
                logs_feedback[page_type][device_type].append("✅ Consent accepted")

            elif "No consent banner" in line:
                logs_feedback[page_type][device_type].append("⚠️ No consent banner")

            # TCF
            elif "TCF string retrieved" in line:
                diagnostics["tcfStringValid"] = True
                logs_feedback[page_type][device_type].append("✅ TCF string OK")

            elif "Final tcString:" in line:
                diagnostics["tcfStringValid"] = True

            elif "TCF string is invalid" in line or "Failed to retrieve TCF" in line:
                diagnostics["tcfStringValid"] = False
                logs_feedback[page_type][device_type].append("❌ TCF string invalid")

            # Loader.js
            elif "Found valid script:" in line and "loader.js" in line:
                logs_feedback[page_type][device_type].append("✅ loader.js found")

            elif "NO request found to loader.js" in line:
                logs_feedback[page_type][device_type].append("❌ No loader.js request")

            elif "Request to loader.js from snigelweb found" in line:
                pass  # Skip duplicate

            # snigelPubConf
            elif "snigelPubConf" in line:
                if "exists" in line:
                    logs_feedback[page_type][device_type].append("✅ snigelPubConf OK")
                elif "does not exist" in line:
                    logs_feedback[page_type][device_type].append("❌ snigelPubConf missing")

            # Script order
            elif "defined before" in line:
                logs_feedback[page_type][device_type].append("✅ Script order OK")
            elif "appears before" in line:
                logs_feedback[page_type][device_type].append("❌ Wrong script order")
            elif "elements is missing" in line:
                logs_feedback[page_type][device_type].append("⚠️ Dynamic script load")

            # Adngin
            elif "Adngin modules saved" in line:
                logs_feedback[page_type][device_type].append("✅ Adngin modules loaded")
            elif "adngin.cmd.enableDebug()" in line and "successfully" in line:
                logs_feedback[page_type][device_type].append("✅ Debug mode enabled")
            elif "adngin or adngin.cmd not available" in line:
                logs_feedback[page_type][device_type].append("❌ Adngin not available")
            elif "Adngin error:" in line:
                logs_feedback[page_type][device_type].append(line[:60])
            elif "Adngin warning:" in line:
                logs_feedback[page_type][device_type].append(line[:60])

            # Prebid
            elif "Prebid error:" in line:
                logs_feedback[page_type][device_type].append(line[:60])
            elif "Prebid warning:" in line:
                logs_feedback[page_type][device_type].append(line[:60])
            elif "Prebid:" in line and ("no bid" in line.lower() or "timeout" in line.lower()):
                logs_feedback[page_type][device_type].append(line[:60])

            # Missing containers
            elif "Missing Ad Container" in line or "Missing container" in line:
                match = re.search(r'container[:\s]+["""]?([^"""]+)["""]?', line)
                if match:
                    logs_feedback[page_type][device_type].append(f"❌ Missing: {match.group(1)[:30]}")

            # Experiment
            elif "Experiment" in line:
                diagnostics["adnginExperimentEnabled"] = True
                logs_feedback[page_type][device_type].append("🚧 Experiment active")

            # USP
            elif "__uspapi" in line:
                logs_feedback[page_type][device_type].append("⚠️ USP API missing")

            # Dev/staging
            elif "development version" in line:
                logs_feedback[page_type][device_type].append("⚠️ DEV version!")
            elif "staging" in line.lower() and "version" in line.lower():
                logs_feedback[page_type][device_type].append("⚠️ STAGING version!")

            # Title
            elif line.startswith("✅ Title:"):
                logs_feedback[page_type][device_type].append(line[:50])

    # Remove duplicates
    for pt in logs_feedback:
        for dt in logs_feedback[pt]:
            seen = set()
            unique = []
            for item in logs_feedback[pt][dt]:
                if item not in seen:
                    seen.add(item)
                    unique.append(item)
            logs_feedback[pt][dt] = unique

    # === LOAD ADNGIN MODULES ===
    try:
        base_name = log_file.stem
        base_name_no_www = base_name.replace("www.", "")
        
        modules_dir = Path("logs/modulesinfo")
        
        for name in [base_name, base_name_no_www]:
            modules_path = modules_dir / f"{name}.json"
            if modules_path.exists():
                with modules_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "error" not in data:
                        adngin_modules = data
                        break
                        
    except Exception as e:
        print(f"❌ Modules load error: {e}")

    return {
        "crawlerFeedback": {
            "logsFeedback": logs_feedback,
            "adnginModules": adngin_modules,
            "diagnostics": diagnostics
        }
    }
