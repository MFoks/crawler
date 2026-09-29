from fastapi import FastAPI, Request, HTTPException, Body, Query, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import logging
import os
from urllib.parse import urlparse
import re
import json
import jwt
from datetime import datetime, timedelta
from passlib.hash import bcrypt
import asyncio
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# JWT Configuration
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 6

# Users configuration (in production, use database)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]
USERS = {
    ADMIN_USERNAME: bcrypt.hash(ADMIN_PASSWORD)
}

# Security
security = HTTPBearer(auto_error=False)

# Crawler Queue Configuration
MAX_CONCURRENT_CRAWLERS = 3
active_crawlers: set = set()
crawler_queue: asyncio.Queue = asyncio.Queue()
queue_lock = asyncio.Lock()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to store crawler status files
STATUS_DIR = "/app/logs"
HISTORY_FILE = "/app/logs/crawler_history.json"

def extract_domain(value: str) -> str:
    parsed = urlparse(value)
    return parsed.netloc or value

def sanitize_filename(domain: str) -> str:
    return re.sub(r"[^a-zA-Z0-9.-]", "_", domain)

# ==================== AUTH ====================

def create_token(username: str) -> str:
    """Create JWT token with 6h expiration"""
    payload = {
        "sub": username,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Dependency to verify auth token and return username"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return payload.get("sub")

# ==================== QUEUE MANAGEMENT ====================

async def process_crawler_queue():
    """Background task to process crawler queue"""
    while True:
        try:
            # Get next item from queue
            domain, payload = await crawler_queue.get()
            
            # Wait for slot to be available
            async with queue_lock:
                while len(active_crawlers) >= MAX_CONCURRENT_CRAWLERS:
                    await asyncio.sleep(1)
                active_crawlers.add(domain)
            
            logger.info(f"🚀 Starting crawler for {domain} ({len(active_crawlers)}/{MAX_CONCURRENT_CRAWLERS} slots used)")
            
            try:
                async with httpx.AsyncClient(timeout=300.0) as client:
                    await client.post("http://crawler:8001/run-crawler", json=payload)
            except httpx.RequestError as e:
                logger.error(f"❌ Crawler failed for {domain}: {e}")
            finally:
                async with queue_lock:
                    active_crawlers.discard(domain)
                logger.info(f"✅ Crawler finished for {domain} ({len(active_crawlers)}/{MAX_CONCURRENT_CRAWLERS} slots used)")
            
            crawler_queue.task_done()
            
        except Exception as e:
            logger.error(f"❌ Queue processing error: {e}")
            await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    """Start background queue processor"""
    asyncio.create_task(process_crawler_queue())
    logger.info(f"🚀 Crawler queue started (max {MAX_CONCURRENT_CRAWLERS} concurrent)")

# ==================== PUBLIC ENDPOINTS ====================

@app.get("/")
async def root():
    return {"status": "ok", "service": "crawler-api"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/login")
async def login(request: Request):
    """Login endpoint - returns JWT token"""
    try:
        body = await request.json()
        username = body.get("username", "").strip()
        password = body.get("password", "")
        
        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password required")
        
        # Check if user exists
        stored_hash = USERS.get(username)
        if not stored_hash:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        if not bcrypt.verify(password, stored_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create token
        token = create_token(username)
        
        return {
            "token": token,
            "expires_in": JWT_EXPIRATION_HOURS * 3600,
            "username": username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.get("/verify-token")
async def verify_token_endpoint(user: str = Depends(get_current_user)):
    """Verify if token is valid"""
    return {"valid": True, "username": user}

# ==================== PROTECTED ENDPOINTS ====================

@app.post("/trigger-crawler")
async def trigger_crawler(request: Request, user: str = Depends(get_current_user)):
    try:
        payload = await request.json()
        homepage = payload.get("homepage")
        article = payload.get("article")

        if not homepage:
            raise HTTPException(status_code=400, detail="Missing homepage.")

        safe_name = sanitize_filename(extract_domain(homepage))
        status_path = os.path.join(STATUS_DIR, f"{safe_name}.status")
        
        # Check if already in queue or running
        async with queue_lock:
            if safe_name in active_crawlers:
                return {"message": f"Crawler already running for: {homepage}", "status": "running"}
        
        with open(status_path, "w") as f:
            f.write("pending")

        # Add to queue instead of direct call
        await crawler_queue.put((safe_name, payload))
        
        queue_size = crawler_queue.qsize()
        active_count = len(active_crawlers)
        
        return {
            "message": f"Crawler queued for: {homepage}",
            "queue_position": queue_size,
            "active_crawlers": active_count,
            "max_concurrent": MAX_CONCURRENT_CRAWLERS
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error("❌ Unexpected error:\n" + traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error.")

@app.get("/crawler-status")
async def crawler_status(domain: str = Query(...), user: str = Depends(get_current_user)):
    safe_name = sanitize_filename(extract_domain(domain))
    path = os.path.join(STATUS_DIR, f"{safe_name}.status")
    
    async with queue_lock:
        is_active = safe_name in active_crawlers
    
    if os.path.exists(path):
        with open(path) as f:
            status = f.read().strip()
        return {
            "status": status,
            "is_active": is_active,
            "queue_size": crawler_queue.qsize(),
            "active_crawlers": len(active_crawlers)
        }
    return {"status": "not_started", "is_active": False}

@app.post("/crawler-finished")
async def crawler_finished(domain: str = Body(...)):
    safe_name = sanitize_filename(extract_domain(domain))
    path = os.path.join(STATUS_DIR, f"{safe_name}.status")
    with open(path, "w") as f:
        f.write("done")
    return {"status": "acknowledged"}

@app.get("/crawler-logs")
async def crawler_logs(domain: str = Query(...), user: str = Depends(get_current_user)):
    safe_name = sanitize_filename(extract_domain(domain))
    log_dir = STATUS_DIR

    matching_files = sorted(
        [f for f in os.listdir(log_dir) if f.startswith(safe_name) and f.endswith(".csv")],
        key=lambda name: os.path.getmtime(os.path.join(log_dir, name)),
        reverse=True
    )

    if not matching_files:
        return {"logs": []}

    latest_log_path = os.path.join(log_dir, matching_files[0])

    with open(latest_log_path, encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    return {"log_file": matching_files[0], "logs": lines}

@app.get("/download-logs")
async def download_logs(domain: str = Query(...), user: str = Depends(get_current_user)):
    safe_name = sanitize_filename(extract_domain(domain))
    log_dir = STATUS_DIR

    matching_files = sorted(
        [f for f in os.listdir(log_dir) if f.startswith(safe_name) and f.endswith(".csv")],
        key=lambda name: os.path.getmtime(os.path.join(log_dir, name)),
        reverse=True
    )

    if not matching_files:
        raise HTTPException(status_code=404, detail="CSV log not found.")

    latest_log_path = os.path.join(log_dir, matching_files[0])

    return FileResponse(
        path=latest_log_path,
        filename=matching_files[0],
        media_type="text/csv"
    )

@app.get("/history")
async def get_history(user: str = Depends(get_current_user)):
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            json.dump([], f)
        return []

    with open(HISTORY_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

@app.post("/history")
async def add_history(entry: dict = Body(...), user: str = Depends(get_current_user)):
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            json.dump([], f)

    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    except json.JSONDecodeError:
        history = []

    history.insert(0, entry)
    history = history[:50]

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

    return {"message": "entry added"}

@app.get("/crawler-feedback")
async def crawler_feedback(domain: str = Query(...), user: str = Depends(get_current_user)):

    safe_name = sanitize_filename(extract_domain(domain))
    log_dir = STATUS_DIR

    matching_files = sorted(
        [f for f in os.listdir(log_dir) if f.startswith(safe_name) and f.endswith(".csv")],
        key=lambda name: os.path.getmtime(os.path.join(log_dir, name)),
        reverse=True
    )

    if not matching_files:
        return {"adsTxtEntries": [], "crawlerFeedback": []}

    latest_log_path = os.path.join(log_dir, matching_files[0])
    ads_txt_issues = []

    with open(latest_log_path, "r", encoding="utf-8") as f:
        for line in f:
            if "❌ ads.txt: Entry" in line and "NOT FOUND" in line:
                match = re.search(r"Entry '(.*)' NOT FOUND", line)
                if match:
                    ads_txt_issues.append(match.group(1))
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"http://crawler:8001/feedback", params={"domain": domain})
            data = response.json()
            crawler_feedback = data.get("crawlerFeedback", {})
    except Exception as e:
        logger.error(f"❌ Failed to get crawler feedback: {e}")
        crawler_feedback = []

    return {
        "adsTxtEntries": ads_txt_issues,
        "crawlerFeedback": crawler_feedback
    }

@app.get("/queue-status")
async def queue_status(user: str = Depends(get_current_user)):
    """Get current queue status"""
    async with queue_lock:
        return {
            "active_crawlers": list(active_crawlers),
            "active_count": len(active_crawlers),
            "queue_size": crawler_queue.qsize(),
            "max_concurrent": MAX_CONCURRENT_CRAWLERS
        }
