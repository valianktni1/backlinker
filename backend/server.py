from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import httpx
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin
import random
from proxy_manager import proxy_manager, fetch_with_proxy, search_duckduckgo

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'backlink-builder-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# SendGrid Configuration
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', '')

app = FastAPI(title="Backlink Builder API")
api_router = APIRouter(prefix="/api")
security = HTTPBearer(auto_error=False)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============= MODELS =============

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class GuestPostOpportunity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    domain: str
    title: str
    niche: str = ""
    da_score: int = 0
    status: str = "found"  # found, contacted, replied, accepted, rejected
    contact_email: str = ""
    found_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: str = ""

class BrokenLink(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_url: str
    source_domain: str
    broken_url: str
    anchor_text: str = ""
    da_score: int = 0
    status: str = "found"  # found, contacted, fixed, rejected
    contact_email: str = ""
    found_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    replacement_url: str = ""

class CompetitorBacklink(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    competitor_domain: str
    backlink_url: str
    backlink_domain: str
    anchor_text: str = ""
    da_score: int = 0
    link_type: str = "dofollow"  # dofollow, nofollow
    found_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "found"  # found, targeted, acquired

class Directory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    url: str
    da_score: int = 0
    category: str = ""
    submission_status: str = "pending"  # pending, submitted, approved, rejected
    submitted_at: str = ""
    notes: str = ""

class OutreachTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    subject: str
    body: str
    template_type: str = "guest_post"  # guest_post, broken_link, general
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class OutreachEmail(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    to_email: str
    subject: str
    body: str
    template_id: str = ""
    opportunity_id: str = ""
    opportunity_type: str = ""  # guest_post, broken_link, directory
    status: str = "draft"  # draft, sent, replied, bounced
    sent_at: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class SearchQuery(BaseModel):
    query: str
    niche: str = ""
    max_results: int = 20

class CompetitorQuery(BaseModel):
    domain: str
    max_results: int = 50

class BrokenLinkQuery(BaseModel):
    url: str
    max_depth: int = 1

class SendEmailRequest(BaseModel):
    to_email: EmailStr
    subject: str
    body: str
    opportunity_id: str = ""
    opportunity_type: str = ""

# ============= AUTH HELPERS =============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============= SCRAPING HELPERS =============

async def fetch_page(url: str, timeout: int = 10, use_proxy: bool = True) -> Optional[str]:
    """Fetch a webpage and return its HTML content"""
    if use_proxy:
        return await fetch_with_proxy(url, timeout=timeout)
    
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return response.text
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
    return None

def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc.replace("www.", "")
    except Exception:
        return ""

async def check_domain_authority(domain: str) -> int:
    """Check DA using free online tools (simulated for now)"""
    # In production, this would call free DA checker APIs
    # For now, return a simulated score based on domain characteristics
    import hashlib
    hash_val = int(hashlib.md5(domain.encode()).hexdigest(), 16)
    return (hash_val % 60) + 20  # Returns 20-80 range

async def find_guest_post_opportunities(query: str, niche: str = "", max_results: int = 20) -> List[dict]:
    """Search for guest post opportunities using DuckDuckGo with proxy rotation"""
    opportunities = []
    
    # Build search queries for guest post opportunities
    search_queries = [
        f'{query} "write for us"',
        f'{query} "guest post"',
        f'{query} "contribute an article"',
        f'{query} "submit a guest post"',
    ]
    
    if niche:
        search_queries.append(f'{niche} "write for us"')
        search_queries.append(f'{niche} "guest post guidelines"')
    
    seen_domains = set()
    
    for search_query in search_queries:
        if len(opportunities) >= max_results:
            break
            
        try:
            # Search using DuckDuckGo with proxy rotation
            results = await search_duckduckgo(search_query, max_results=10)
            
            for result in results:
                url = result.get('url', '')
                domain = extract_domain(url)
                
                # Skip if we've already seen this domain
                if domain in seen_domains or not domain:
                    continue
                
                seen_domains.add(domain)
                
                # Check if it's likely a guest post page
                title = result.get('title', '').lower()
                snippet = result.get('snippet', '').lower()
                
                is_guest_post_page = any(phrase in title or phrase in snippet for phrase in [
                    'write for us', 'guest post', 'contribute', 'submit article',
                    'guest author', 'guest writer', 'submission guidelines'
                ])
                
                if is_guest_post_page or 'write' in url.lower() or 'guest' in url.lower():
                    da = await check_domain_authority(domain)
                    
                    # Try to extract contact email from the page
                    contact_email = ""
                    try:
                        page_html = await fetch_page(url, timeout=10, use_proxy=True)
                        if page_html:
                            # Look for email addresses
                            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                            emails = re.findall(email_pattern, page_html)
                            if emails:
                                contact_email = emails[0]
                    except Exception:
                        pass
                    
                    opportunities.append({
                        "id": str(uuid.uuid4()),
                        "url": url,
                        "domain": domain,
                        "title": result.get('title', 'Guest Post Opportunity'),
                        "niche": niche or query,
                        "da_score": da,
                        "status": "found",
                        "contact_email": contact_email,
                        "found_at": datetime.now(timezone.utc).isoformat(),
                        "notes": f"Found via search: {search_query}"
                    })
                    
                    if len(opportunities) >= max_results:
                        break
                        
        except Exception as e:
            logger.error(f"Error searching for '{search_query}': {e}")
            continue
    
    # If we didn't find real results, add some known guest post sites as fallback
    if len(opportunities) < 3:
        fallback_sites = [
            {"domain": "medium.com", "title": "Write on Medium", "url": "https://medium.com/creators"},
            {"domain": "dev.to", "title": "Dev.to - Write for Us", "url": "https://dev.to/about"},
            {"domain": "hackernoon.com", "title": "HackerNoon - Submit Story", "url": "https://hackernoon.com/signup"},
            {"domain": "dzone.com", "title": "DZone - Contribute", "url": "https://dzone.com/pages/contribute"},
            {"domain": "smashingmagazine.com", "title": "Smashing Magazine - Write for Us", "url": "https://www.smashingmagazine.com/write-for-us/"},
        ]
        
        for site in fallback_sites:
            if site["domain"] not in seen_domains and len(opportunities) < max_results:
                da = await check_domain_authority(site["domain"])
                opportunities.append({
                    "id": str(uuid.uuid4()),
                    "url": site["url"],
                    "domain": site["domain"],
                    "title": site["title"],
                    "niche": niche or "general",
                    "da_score": da,
                    "status": "found",
                    "contact_email": "",
                    "found_at": datetime.now(timezone.utc).isoformat(),
                    "notes": f"Known guest post site for: {query}"
                })
    
    return opportunities

async def find_broken_links(url: str, max_depth: int = 1) -> List[dict]:
    """Find broken links on a webpage using proxy rotation"""
    broken_links = []
    html = await fetch_page(url, use_proxy=True)
    
    if not html:
        # Try without proxy as fallback
        html = await fetch_page(url, use_proxy=False)
    
    if not html:
        return broken_links
    
    soup = BeautifulSoup(html, 'html.parser')
    links = soup.find_all('a', href=True)
    source_domain = extract_domain(url)
    
    # Get a proxy for checking links
    proxy = await proxy_manager.get_proxy()
    proxy_config = {"http://": proxy.url, "https://": proxy.url} if proxy else None
    
    checked = 0
    for link in links:
        if checked >= 30:  # Limit to prevent overload
            break
            
        href = link.get('href', '')
        
        # Skip internal links, anchors, javascript, mailto
        if not href.startswith('http') or href.startswith(f'http://{source_domain}') or href.startswith(f'https://{source_domain}'):
            continue
        if 'javascript:' in href or 'mailto:' in href or '#' == href[0]:
            continue
            
        try:
            async with httpx.AsyncClient(timeout=8, proxies=proxy_config, follow_redirects=True) as client:
                response = await client.head(href)
                checked += 1
                
                if response.status_code >= 400:
                    da = await check_domain_authority(source_domain)
                    broken_links.append({
                        "id": str(uuid.uuid4()),
                        "source_url": url,
                        "source_domain": source_domain,
                        "broken_url": href,
                        "anchor_text": link.get_text(strip=True)[:100],
                        "da_score": da,
                        "status": "found",
                        "found_at": datetime.now(timezone.utc).isoformat(),
                        "http_status": response.status_code
                    })
        except httpx.TimeoutException:
            # Timeout might indicate a broken link
            da = await check_domain_authority(source_domain)
            broken_links.append({
                "id": str(uuid.uuid4()),
                "source_url": url,
                "source_domain": source_domain,
                "broken_url": href,
                "anchor_text": link.get_text(strip=True)[:100],
                "da_score": da,
                "status": "found",
                "found_at": datetime.now(timezone.utc).isoformat(),
                "http_status": "timeout"
            })
            checked += 1
        except Exception:
            checked += 1
            pass
    
    return broken_links

# ============= SENDGRID EMAIL =============

async def send_email_via_sendgrid(to_email: str, subject: str, body: str) -> bool:
    """Send email using SendGrid API"""
    if not SENDGRID_API_KEY or not SENDER_EMAIL:
        logger.warning("SendGrid not configured - email not sent")
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {SENDGRID_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "personalizations": [{"to": [{"email": to_email}]}],
                    "from": {"email": SENDER_EMAIL},
                    "subject": subject,
                    "content": [{"type": "text/html", "value": body}]
                }
            )
            return response.status_code == 202
    except Exception as e:
        logger.error(f"SendGrid error: {e}")
        return False

# ============= AUTH ROUTES =============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "name": user_data.name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user)
    
    token = create_token(user_id)
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user_id, email=user_data.email, name=user_data.name, created_at=user["created_at"])
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"])
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user["id"], email=user["email"], name=user["name"], created_at=user["created_at"])
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(id=user["id"], email=user["email"], name=user["name"], created_at=user["created_at"])

# ============= DASHBOARD ROUTES =============

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    guest_posts = await db.guest_posts.count_documents({})
    broken_links = await db.broken_links.count_documents({})
    competitors = await db.competitor_backlinks.count_documents({})
    directories = await db.directories.count_documents({})
    emails_sent = await db.outreach_emails.count_documents({"status": "sent"})
    
    # Get recent activity
    recent_opportunities = await db.guest_posts.find({}, {"_id": 0}).sort("found_at", -1).limit(5).to_list(5)
    
    return {
        "total_guest_posts": guest_posts,
        "total_broken_links": broken_links,
        "total_competitor_backlinks": competitors,
        "total_directories": directories,
        "emails_sent": emails_sent,
        "recent_opportunities": recent_opportunities
    }

# ============= GUEST POST ROUTES =============

@api_router.post("/guest-posts/search")
async def search_guest_posts(query: SearchQuery, user: dict = Depends(get_current_user)):
    opportunities = await find_guest_post_opportunities(query.query, query.niche, query.max_results)
    # Save to database
    if opportunities:
        await db.guest_posts.insert_many(opportunities)
    # Return clean data without MongoDB _id fields
    clean_opportunities = [{k: v for k, v in opp.items() if k != "_id"} for opp in opportunities]
    return {"results": clean_opportunities, "count": len(clean_opportunities)}

@api_router.get("/guest-posts")
async def get_guest_posts(user: dict = Depends(get_current_user), skip: int = 0, limit: int = 50):
    posts = await db.guest_posts.find({}, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.guest_posts.count_documents({})
    return {"items": posts, "total": total}

@api_router.put("/guest-posts/{post_id}")
async def update_guest_post(post_id: str, updates: dict, user: dict = Depends(get_current_user)):
    updates.pop("id", None)
    updates.pop("_id", None)
    result = await db.guest_posts.update_one({"id": post_id}, {"$set": updates})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"success": True}

@api_router.delete("/guest-posts/{post_id}")
async def delete_guest_post(post_id: str, user: dict = Depends(get_current_user)):
    result = await db.guest_posts.delete_one({"id": post_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"success": True}

# ============= BROKEN LINK ROUTES =============

@api_router.post("/broken-links/scan")
async def scan_broken_links(query: BrokenLinkQuery, user: dict = Depends(get_current_user)):
    broken = await find_broken_links(query.url, query.max_depth)
    if broken:
        await db.broken_links.insert_many(broken)
    return {"results": broken, "count": len(broken)}

@api_router.get("/broken-links")
async def get_broken_links(user: dict = Depends(get_current_user), skip: int = 0, limit: int = 50):
    links = await db.broken_links.find({}, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.broken_links.count_documents({})
    return {"items": links, "total": total}

@api_router.put("/broken-links/{link_id}")
async def update_broken_link(link_id: str, updates: dict, user: dict = Depends(get_current_user)):
    updates.pop("id", None)
    updates.pop("_id", None)
    result = await db.broken_links.update_one({"id": link_id}, {"$set": updates})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Link not found")
    return {"success": True}

@api_router.delete("/broken-links/{link_id}")
async def delete_broken_link(link_id: str, user: dict = Depends(get_current_user)):
    result = await db.broken_links.delete_one({"id": link_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Link not found")
    return {"success": True}

# ============= COMPETITOR ROUTES =============

@api_router.post("/competitors/analyze")
async def analyze_competitor(query: CompetitorQuery, user: dict = Depends(get_current_user)):
    # Simulated competitor backlink analysis
    # In production, this would scrape competitor backlinks from free tools
    backlinks = []
    sample_domains = ["blog.example.com", "news.example.com", "resource.example.com", "guide.example.com"]
    
    for i, domain in enumerate(sample_domains[:query.max_results]):
        da = await check_domain_authority(domain)
        backlinks.append({
            "id": str(uuid.uuid4()),
            "competitor_domain": query.domain,
            "backlink_url": f"https://{domain}/article-{i+1}",
            "backlink_domain": domain,
            "anchor_text": f"Link to {query.domain}",
            "da_score": da,
            "link_type": "dofollow" if i % 2 == 0 else "nofollow",
            "found_at": datetime.now(timezone.utc).isoformat(),
            "status": "found"
        })
    
    if backlinks:
        await db.competitor_backlinks.insert_many(backlinks)
    # Return clean data without MongoDB _id fields
    clean_backlinks = [{k: v for k, v in bl.items() if k != "_id"} for bl in backlinks]
    return {"results": clean_backlinks, "count": len(clean_backlinks)}

@api_router.get("/competitors")
async def get_competitor_backlinks(user: dict = Depends(get_current_user), skip: int = 0, limit: int = 50):
    backlinks = await db.competitor_backlinks.find({}, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.competitor_backlinks.count_documents({})
    return {"items": backlinks, "total": total}

@api_router.delete("/competitors/{backlink_id}")
async def delete_competitor_backlink(backlink_id: str, user: dict = Depends(get_current_user)):
    result = await db.competitor_backlinks.delete_one({"id": backlink_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Backlink not found")
    return {"success": True}

# ============= DIRECTORY ROUTES =============

@api_router.get("/directories")
async def get_directories(user: dict = Depends(get_current_user), skip: int = 0, limit: int = 50):
    dirs = await db.directories.find({}, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.directories.count_documents({})
    return {"items": dirs, "total": total}

@api_router.post("/directories")
async def add_directory(directory: Directory, user: dict = Depends(get_current_user)):
    dir_dict = directory.model_dump()
    await db.directories.insert_one(dir_dict)
    # Return clean dict without MongoDB _id field
    return {k: v for k, v in dir_dict.items() if k != "_id"}

@api_router.put("/directories/{dir_id}")
async def update_directory(dir_id: str, updates: dict, user: dict = Depends(get_current_user)):
    updates.pop("id", None)
    updates.pop("_id", None)
    result = await db.directories.update_one({"id": dir_id}, {"$set": updates})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Directory not found")
    return {"success": True}

@api_router.delete("/directories/{dir_id}")
async def delete_directory(dir_id: str, user: dict = Depends(get_current_user)):
    result = await db.directories.delete_one({"id": dir_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Directory not found")
    return {"success": True}

@api_router.post("/directories/seed")
async def seed_directories(user: dict = Depends(get_current_user)):
    """Seed database with high DA directories"""
    directories = [
        {"name": "DMOZ", "url": "https://dmoz-odp.org", "da_score": 85, "category": "General"},
        {"name": "Best of the Web", "url": "https://botw.org", "da_score": 72, "category": "General"},
        {"name": "Jasmine Directory", "url": "https://jasminedirectory.com", "da_score": 58, "category": "General"},
        {"name": "Spoke", "url": "https://spoke.com", "da_score": 65, "category": "Business"},
        {"name": "Manta", "url": "https://manta.com", "da_score": 68, "category": "Business"},
        {"name": "Hotfrog", "url": "https://hotfrog.com", "da_score": 55, "category": "Business"},
        {"name": "Yelp", "url": "https://yelp.com", "da_score": 94, "category": "Local"},
        {"name": "Yellow Pages", "url": "https://yellowpages.com", "da_score": 88, "category": "Local"},
        {"name": "Foursquare", "url": "https://foursquare.com", "da_score": 92, "category": "Local"},
        {"name": "Crunchbase", "url": "https://crunchbase.com", "da_score": 91, "category": "Startups"},
    ]
    
    for d in directories:
        d["id"] = str(uuid.uuid4())
        d["submission_status"] = "pending"
        d["submitted_at"] = ""
        d["notes"] = ""
    
    await db.directories.delete_many({})
    await db.directories.insert_many(directories)
    return {"seeded": len(directories)}

# ============= OUTREACH ROUTES =============

@api_router.get("/outreach/templates")
async def get_templates(user: dict = Depends(get_current_user)):
    templates = await db.outreach_templates.find({}, {"_id": 0}).to_list(100)
    return {"items": templates}

@api_router.post("/outreach/templates")
async def create_template(template: OutreachTemplate, user: dict = Depends(get_current_user)):
    template_dict = template.model_dump()
    await db.outreach_templates.insert_one(template_dict)
    return template_dict

@api_router.delete("/outreach/templates/{template_id}")
async def delete_template(template_id: str, user: dict = Depends(get_current_user)):
    result = await db.outreach_templates.delete_one({"id": template_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"success": True}

@api_router.post("/outreach/templates/seed")
async def seed_templates(user: dict = Depends(get_current_user)):
    """Seed default outreach templates"""
    templates = [
        {
            "id": str(uuid.uuid4()),
            "name": "Guest Post Request",
            "subject": "Guest Post Opportunity - {site_name}",
            "body": """<p>Hi {name},</p>
<p>I've been a regular reader of {site_name} and I love the content you publish about {niche}.</p>
<p>I'm reaching out because I'd love to contribute a guest post to your site. I have some unique insights about {topic} that I think your audience would find valuable.</p>
<p>Here are a few topic ideas I had in mind:</p>
<ul>
<li>Topic idea 1</li>
<li>Topic idea 2</li>
<li>Topic idea 3</li>
</ul>
<p>Would you be open to a guest contribution? I'd be happy to follow your editorial guidelines.</p>
<p>Looking forward to hearing from you!</p>
<p>Best regards,<br>{your_name}</p>""",
            "template_type": "guest_post",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Broken Link Outreach",
            "subject": "Found a broken link on {site_name}",
            "body": """<p>Hi {name},</p>
<p>I was reading your article at {page_url} and noticed that one of the links is broken:</p>
<p><strong>Broken link:</strong> {broken_url}</p>
<p>I actually have a similar resource that covers the same topic: {replacement_url}</p>
<p>Would you consider updating the link? It would help your readers find the information they're looking for.</p>
<p>Thanks for your time!</p>
<p>Best,<br>{your_name}</p>""",
            "template_type": "broken_link",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Resource Page Outreach",
            "subject": "Resource suggestion for {site_name}",
            "body": """<p>Hi {name},</p>
<p>I came across your excellent resource page at {page_url} and found it really helpful.</p>
<p>I've recently published a comprehensive guide on {topic} that I think would be a great addition to your list: {your_url}</p>
<p>It covers:</p>
<ul>
<li>Key point 1</li>
<li>Key point 2</li>
<li>Key point 3</li>
</ul>
<p>Would you consider adding it to your resources?</p>
<p>Thank you!</p>
<p>Best regards,<br>{your_name}</p>""",
            "template_type": "general",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.outreach_templates.delete_many({})
    await db.outreach_templates.insert_many(templates)
    return {"seeded": len(templates)}

@api_router.get("/outreach/emails")
async def get_outreach_emails(user: dict = Depends(get_current_user), skip: int = 0, limit: int = 50):
    emails = await db.outreach_emails.find({}, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.outreach_emails.count_documents({})
    return {"items": emails, "total": total}

@api_router.post("/outreach/send")
async def send_outreach_email(
    request: SendEmailRequest, 
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    email_record = {
        "id": str(uuid.uuid4()),
        "to_email": request.to_email,
        "subject": request.subject,
        "body": request.body,
        "opportunity_id": request.opportunity_id,
        "opportunity_type": request.opportunity_type,
        "status": "pending",
        "sent_at": "",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Send email in background
    success = await send_email_via_sendgrid(request.to_email, request.subject, request.body)
    
    if success:
        email_record["status"] = "sent"
        email_record["sent_at"] = datetime.now(timezone.utc).isoformat()
    else:
        email_record["status"] = "failed"
    
    await db.outreach_emails.insert_one(email_record)
    
    return {"success": success, "email": {k: v for k, v in email_record.items() if k != "_id"}}

# ============= SETTINGS ROUTES =============

@api_router.get("/settings")
async def get_settings(user: dict = Depends(get_current_user)):
    settings = await db.settings.find_one({"user_id": user["id"]}, {"_id": 0})
    if not settings:
        settings = {
            "user_id": user["id"],
            "sendgrid_configured": bool(SENDGRID_API_KEY),
            "sender_email": SENDER_EMAIL,
            "your_name": user["name"],
            "your_website": "",
            "default_niche": ""
        }
    return settings

@api_router.put("/settings")
async def update_settings(updates: dict, user: dict = Depends(get_current_user)):
    updates["user_id"] = user["id"]
    await db.settings.update_one(
        {"user_id": user["id"]},
        {"$set": updates},
        upsert=True
    )
    return {"success": True}

# ============= ROOT =============

@api_router.get("/")
async def root():
    return {"message": "Backlink Builder API", "version": "1.0.0"}

# ============= PROXY ROUTES =============

@api_router.get("/proxy/stats")
async def get_proxy_stats(user: dict = Depends(get_current_user)):
    """Get proxy pool statistics"""
    stats = proxy_manager.get_stats()
    return stats

@api_router.post("/proxy/refresh")
async def refresh_proxies(user: dict = Depends(get_current_user)):
    """Force refresh the proxy pool"""
    count = await proxy_manager.refresh_proxies(force=True)
    return {"success": True, "proxy_count": count}

# Include router and middleware
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
