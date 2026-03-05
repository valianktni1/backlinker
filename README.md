# LinkBuilder - Automated Backlink Builder

A self-hosted SEO tool for finding high-quality backlink opportunities without expensive subscriptions.

## Features

- **Guest Post Finder** - Search for "write for us" opportunities via Google (SerpAPI) or DuckDuckGo
- **Broken Link Builder** - Scan websites for broken links to exploit
- **Competitor Analysis** - Discover where competitors get their backlinks
- **Directory Manager** - Track submissions to high-DA directories
- **Email Outreach** - Send templated outreach emails via SendGrid
- **Proxy Rotation** - 190+ free rotating proxies for web scraping

## Tech Stack

- **Frontend**: React 19, Tailwind CSS
- **Backend**: FastAPI, Python 3.11
- **Database**: MongoDB 7.0
- **Search**: SerpAPI (Google) + DuckDuckGo fallback
- **Email**: SendGrid (optional)

## Quick Start (Docker)

### 1. Clone and Configure

```bash
git clone https://github.com/yourusername/linkbuilder.git
cd linkbuilder
cp .env.example .env
```

### 2. Edit `.env` file

```env
# Required
JWT_SECRET=your-secure-random-string-here
EXTERNAL_URL=http://your-server-ip:8080
PORT=8080

# Optional (but recommended)
SERPAPI_API_KEY=your-serpapi-key    # 100 free Google searches/month
SENDGRID_API_KEY=your-sendgrid-key  # For email outreach
SENDER_EMAIL=your@email.com
```

### 3. Start with Docker Compose

```bash
docker-compose up -d
```

### 4. Access the App

Open `http://your-server-ip:8080` in your browser.

## TrueNAS Scale Deployment

### Option 1: Custom App (Docker Compose)

1. Go to **Apps** → **Discover Apps** → **Custom App**
2. Upload the `docker-compose.yml` or paste its contents
3. Set environment variables in the UI
4. Deploy

### Option 2: Manual Docker

```bash
# Pull and run MongoDB
docker run -d --name linkbuilder-mongo \
  -v linkbuilder-data:/data/db \
  mongo:7.0

# Build and run backend
cd backend
docker build -t linkbuilder-backend .
docker run -d --name linkbuilder-backend \
  --link linkbuilder-mongo:mongodb \
  -e MONGO_URL=mongodb://mongodb:27017 \
  -e DB_NAME=backlink_builder \
  -e JWT_SECRET=your-secret \
  linkbuilder-backend

# Build and run frontend
cd ../frontend
docker build -t linkbuilder-frontend \
  --build-arg REACT_APP_BACKEND_URL=http://your-ip:8080 .
docker run -d --name linkbuilder-frontend \
  --link linkbuilder-backend:backend \
  -p 8080:80 \
  linkbuilder-frontend
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET` | Yes | Secret key for JWT tokens (min 32 chars) |
| `EXTERNAL_URL` | Yes | Public URL of your app |
| `PORT` | No | Port to expose (default: 8080) |
| `SERPAPI_API_KEY` | No | SerpAPI key for Google search |
| `SENDGRID_API_KEY` | No | SendGrid key for email outreach |
| `SENDER_EMAIL` | No | Email address for outreach |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Create account |
| `/api/auth/login` | POST | Login |
| `/api/guest-posts/search` | POST | Search guest post opportunities |
| `/api/broken-links/scan` | POST | Scan URL for broken links |
| `/api/competitors/analyze` | POST | Analyze competitor backlinks |
| `/api/directories` | GET | List directories |
| `/api/outreach/send` | POST | Send outreach email |
| `/api/proxy/stats` | GET | Get proxy pool stats |

## Search Strategy

The app uses a tiered search approach:

1. **SerpAPI** (if configured) - Google results, most reliable
2. **DuckDuckGo + Proxies** - Unlimited free fallback
3. **Known Sites** - Pre-seeded high-DA guest post sites

## Free Tier Limits

- **SerpAPI**: 100 searches/month (then falls back to DuckDuckGo)
- **SendGrid**: 100 emails/day
- **Proxies**: Unlimited (auto-refreshed every 30 min)

## Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn server:app --reload --port 8001

# Frontend
cd frontend
yarn install
yarn start
```

## License

MIT
