from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import httpx
import json
import logging
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import re

from shared.feedback.generate_feedback import generate_feedback_from_logfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_domain(value: str) -> str:
    parsed = urlparse(value)
    return parsed.netloc or value


def sanitize_filename(domain: str) -> str:
    return re.sub(r"[^a-zA-Z0-9.-]", "_", domain)


def build_log_path(homepage: str) -> Path:
    domain = sanitize_filename(extract_domain(homepage))
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    candidates = sorted(
        logs_dir.glob(f"{domain}_{now}*.csv"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    if not candidates:
        fallback = sorted(
            logs_dir.glob(f"{domain}_*.csv"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        if fallback:
            logger.warning(f"⚠️ No exact timestamp match. Using fallback: {fallback[0]}")
            return fallback[0]

        raise RuntimeError(f"No log file found for domain: {domain}")

    return candidates[0]


@app.get("/")
async def root():
    return {"status": "ok", "service": "crawler"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/run-crawler")
async def run_crawler(payload: dict = Body(...)):
    homepage = payload.get("homepage")
    logger.info("🚀 Received crawler payload")

    if not homepage:
        raise HTTPException(status_code=400, detail="Missing homepage URL.")

    try:
        logger.info(f"⚙️ Running main.py for: {homepage}")
        command = ["python3", "main.py", json.dumps(payload)]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )

        logger.info("✅ main.py completed")
        log_file_path = build_log_path(homepage)
        logger.info(f"📄 Using log file: {log_file_path}")

        feedback = generate_feedback_from_logfile(log_file_path)
        logger.info(f"🧠 Feedback generated with {len(feedback)} entries")

        return {
            "message": "Crawler executed successfully",
            "command": " ".join(command),
            "output": result.stdout,
            "feedback": feedback
        }

    except subprocess.CalledProcessError as e:
        logger.error("❌ main.py failed:")
        logger.error("STDOUT:\n" + str(e.stdout))
        logger.error("STDERR:\n" + str(e.stderr))
        raise HTTPException(status_code=500, detail="main.py failed. Check logs for details.")

    except Exception as general_error:
        logger.error(f"❌ General error: {general_error}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(general_error)}")

    finally:
        try:
            logger.info("📡 Notifying API about completion...")
            async with httpx.AsyncClient(timeout=30.0) as client:
                await client.post("http://crawler-api:8000/crawler-finished", json=homepage)
        except Exception as notify_error:
            logger.error(f"❌ Failed to send confirmation to API: {notify_error}")


@app.get("/feedback")
async def get_feedback(domain: str = Query(...)):
    try:
        log_file_path = build_log_path(domain)
        result = generate_feedback_from_logfile(log_file_path)
        return result
    except Exception as e:
        logger.error(f"❌ Failed to generate feedback: {e}")
        return {
            "crawlerFeedback": {
                "logsFeedback": [f"❌ Error: {e}"],
                "adnginModules": {},
                "diagnostics": {}
            }
        }
