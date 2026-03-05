# LinkBuilder - Automated Backlink Builder PRD

## Overview
Self-hosted automated backlink building tool for SEO professionals to find high-quality backlinks without paid subscriptions.

## Original Problem Statement
Build an Automated Backlink Builder application with:
- Guest Post Finder (scrape "write for us" opportunities)
- Broken Link Builder (find 404s on high DA sites)
- Competitor Backlink Scraper
- Directory Submission Manager
- Email Outreach via SendGrid (free tier)
- Single admin user with JWT authentication
- Deployable on TrueNAS Scale (Docker)

## User Choices
- **All 4 core features**: Guest Posts, Broken Links, Competitor Analysis, Directories
- **Auth**: JWT (email/password)
- **Email**: SendGrid (free tier - 100 emails/day)
- **Users**: Single admin only
- **Niche**: General-purpose

## Architecture
- **Frontend**: React 19, Tailwind CSS, Sonner (toasts), Lucide icons
- **Backend**: FastAPI, Motor (async MongoDB), PyJWT, bcrypt
- **Database**: MongoDB
- **Email**: SendGrid API (optional)

## Core Features Implemented

### 1. Dashboard
- Overview stats (guest posts, broken links, competitors, directories, emails sent)
- Recent opportunities table

### 2. Guest Post Finder
- Search "write for us" opportunities by keyword/niche
- Domain Authority (DA) scoring
- Status tracking (found, contacted, replied, accepted, rejected)
- External link to opportunity pages

### 3. Broken Link Builder
- Scan URLs for broken links (404s)
- Find replacement opportunities
- DA scoring for source domains
- Status management

### 4. Competitor Analysis
- Analyze competitor backlink profiles
- View backlink sources with DA scores
- Identify dofollow vs nofollow links

### 5. Directory Manager
- Pre-seeded high-DA directories (Yelp DA:94, Foursquare DA:92, etc.)
- Submission status tracking
- Add custom directories

### 6. Email Outreach
- Pre-built templates (Guest Post, Broken Link, Resource Page)
- Compose and send emails via SendGrid
- Email history tracking

### 7. Settings
- Profile configuration
- SendGrid status display

## API Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user
- `GET /api/dashboard/stats` - Dashboard statistics
- `POST /api/guest-posts/search` - Search guest post opportunities
- `GET /api/guest-posts` - List opportunities
- `POST /api/broken-links/scan` - Scan URL for broken links
- `GET /api/broken-links` - List broken links
- `POST /api/competitors/analyze` - Analyze competitor
- `GET /api/competitors` - List competitor backlinks
- `GET /api/directories` - List directories
- `POST /api/directories/seed` - Seed default directories
- `GET /api/outreach/templates` - Get email templates
- `POST /api/outreach/send` - Send outreach email

## What's Been Implemented (March 5, 2026)
- ✅ Full JWT authentication system
- ✅ Dark mode UI with Manrope/Inter/JetBrains Mono fonts
- ✅ Dashboard with stats overview
- ✅ Guest Post Finder with DuckDuckGo search + proxy rotation
- ✅ Broken Link Scanner with proxy rotation
- ✅ Competitor Analysis
- ✅ Directory Manager with 10 pre-seeded high-DA sites
- ✅ Email Outreach with 3 templates
- ✅ Settings page with SendGrid + Proxy status
- ✅ **FREE Proxy Rotation** from 3 sources (ProxyScrape, Free-Proxy-List, GeoNode)

## Proxy Rotation System
The app includes automatic proxy rotation for web scraping:
- **Sources**: ProxyScrape, Free-Proxy-List, GeoNode (all free)
- **Auto-refresh**: Every 30 minutes
- **Manual refresh**: Via Settings page
- **Health tracking**: Failed proxies are automatically deprioritized
- **Fallback**: Direct requests if no proxies available

## Configuration for TrueNAS Scale Deployment

### Environment Variables (backend/.env)
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=backlink_builder
JWT_SECRET=your-secure-secret-key
SENDGRID_API_KEY=your-sendgrid-key (optional)
SENDER_EMAIL=your-email@domain.com (optional)
```

### Docker Compose (to be created)
For TrueNAS Scale deployment, will need:
- MongoDB container
- Backend container (FastAPI)
- Frontend container (React/nginx)

## Known Limitations
1. **Simulated Data**: Guest post search and competitor analysis return simulated results (real web scraping would require proxy rotation)
2. **SendGrid Optional**: Email outreach requires SendGrid API key
3. **DA Scoring**: Uses hash-based simulation (real DA requires Moz/Ahrefs API)

## Future Enhancements (Backlog)
### P0 - High Priority
- [ ] Docker Compose for TrueNAS Scale
- [ ] Actual web scraping with proxy support
- [ ] Real DA checking via free tools

### P1 - Medium Priority
- [ ] Bulk email sending
- [ ] Export to CSV
- [ ] Advanced filtering
- [ ] Campaign management

### P2 - Nice to Have
- [ ] HARO/Connectively integration
- [ ] Scheduled scans
- [ ] Email tracking (opens/clicks)
- [ ] Chrome extension

## Next Steps
1. Configure SendGrid API key for email outreach
2. Create Docker Compose for TrueNAS deployment
3. Add real web scraping capabilities
