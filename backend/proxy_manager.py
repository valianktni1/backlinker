"""
Proxy Manager for Free Proxy Rotation
Fetches proxies from multiple free sources and rotates them for web scraping
"""

import asyncio
import httpx
import random
import logging
from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class Proxy:
    ip: str
    port: str
    protocol: str = "http"
    country: str = ""
    last_used: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    failures: int = 0
    successes: int = 0
    
    @property
    def url(self) -> str:
        return f"{self.protocol}://{self.ip}:{self.port}"
    
    @property
    def is_healthy(self) -> bool:
        # Proxy is unhealthy if it has more than 3 consecutive failures
        return self.failures < 3
    
    def mark_success(self):
        self.successes += 1
        self.failures = 0
        self.last_used = datetime.now(timezone.utc)
    
    def mark_failure(self):
        self.failures += 1
        self.last_used = datetime.now(timezone.utc)


class ProxyManager:
    """Manages a pool of free proxies with rotation and health checking"""
    
    def __init__(self):
        self.proxies: List[Proxy] = []
        self.last_refresh: Optional[datetime] = None
        self.refresh_interval = timedelta(minutes=30)
        self._lock = asyncio.Lock()
    
    async def refresh_proxies(self, force: bool = False) -> int:
        """Fetch fresh proxies from multiple free sources"""
        async with self._lock:
            # Check if refresh is needed
            if not force and self.last_refresh:
                if datetime.now(timezone.utc) - self.last_refresh < self.refresh_interval:
                    return len(self.proxies)
            
            logger.info("Refreshing proxy list from free sources...")
            new_proxies = []
            
            # Source 1: ProxyScrape API (free)
            try:
                proxies_from_scrape = await self._fetch_from_proxyscrape()
                new_proxies.extend(proxies_from_scrape)
                logger.info(f"Got {len(proxies_from_scrape)} proxies from ProxyScrape")
            except Exception as e:
                logger.error(f"ProxyScrape fetch error: {e}")
            
            # Source 2: Free Proxy List
            try:
                proxies_from_fpl = await self._fetch_from_free_proxy_list()
                new_proxies.extend(proxies_from_fpl)
                logger.info(f"Got {len(proxies_from_fpl)} proxies from Free Proxy List")
            except Exception as e:
                logger.error(f"Free Proxy List fetch error: {e}")
            
            # Source 3: GeoNode Free API
            try:
                proxies_from_geonode = await self._fetch_from_geonode()
                new_proxies.extend(proxies_from_geonode)
                logger.info(f"Got {len(proxies_from_geonode)} proxies from GeoNode")
            except Exception as e:
                logger.error(f"GeoNode fetch error: {e}")
            
            # Remove duplicates based on IP:Port
            seen = set()
            unique_proxies = []
            for p in new_proxies:
                key = f"{p.ip}:{p.port}"
                if key not in seen:
                    seen.add(key)
                    unique_proxies.append(p)
            
            self.proxies = unique_proxies
            self.last_refresh = datetime.now(timezone.utc)
            logger.info(f"Total unique proxies: {len(self.proxies)}")
            
            return len(self.proxies)
    
    async def _fetch_from_proxyscrape(self) -> List[Proxy]:
        """Fetch from ProxyScrape free API"""
        proxies = []
        url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
        
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url)
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if ':' in line:
                        parts = line.split(':')
                        if len(parts) == 2:
                            proxies.append(Proxy(ip=parts[0], port=parts[1]))
        
        return proxies[:100]  # Limit to 100
    
    async def _fetch_from_free_proxy_list(self) -> List[Proxy]:
        """Fetch from free-proxy-list.net"""
        proxies = []
        url = "https://free-proxy-list.net/"
        
        async with httpx.AsyncClient(timeout=15) as client:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                table = soup.find('table')
                
                if table:
                    rows = table.find_all('tr')[1:]  # Skip header
                    for row in rows[:50]:
                        cols = row.find_all('td')
                        if len(cols) >= 7:
                            ip = cols[0].get_text(strip=True)
                            port = cols[1].get_text(strip=True)
                            country = cols[3].get_text(strip=True)
                            https = cols[6].get_text(strip=True).lower() == 'yes'
                            
                            proxies.append(Proxy(
                                ip=ip,
                                port=port,
                                protocol="https" if https else "http",
                                country=country
                            ))
        
        return proxies
    
    async def _fetch_from_geonode(self) -> List[Proxy]:
        """Fetch from GeoNode free API"""
        proxies = []
        url = "https://proxylist.geonode.com/api/proxy-list?limit=50&page=1&sort_by=lastChecked&sort_type=desc"
        
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('data', []):
                    proxies.append(Proxy(
                        ip=item.get('ip', ''),
                        port=str(item.get('port', '')),
                        protocol=item.get('protocols', ['http'])[0] if item.get('protocols') else 'http',
                        country=item.get('country', '')
                    ))
        
        return proxies
    
    async def get_proxy(self) -> Optional[Proxy]:
        """Get a random healthy proxy from the pool"""
        if not self.proxies:
            await self.refresh_proxies()
        
        # Filter healthy proxies
        healthy = [p for p in self.proxies if p.is_healthy]
        
        if not healthy:
            # All proxies failed, force refresh
            await self.refresh_proxies(force=True)
            healthy = [p for p in self.proxies if p.is_healthy]
        
        if healthy:
            return random.choice(healthy)
        
        return None
    
    async def get_working_proxy(self, test_url: str = "https://httpbin.org/ip") -> Optional[Proxy]:
        """Get a proxy that's verified to work"""
        for _ in range(5):  # Try up to 5 proxies
            proxy = await self.get_proxy()
            if proxy:
                if await self._test_proxy(proxy, test_url):
                    return proxy
                proxy.mark_failure()
        return None
    
    async def _test_proxy(self, proxy: Proxy, test_url: str) -> bool:
        """Test if a proxy is working"""
        try:
            async with httpx.AsyncClient(
                proxies={"http://": proxy.url, "https://": proxy.url},
                timeout=10
            ) as client:
                response = await client.get(test_url)
                return response.status_code == 200
        except Exception:
            return False
    
    def get_stats(self) -> Dict:
        """Get proxy pool statistics"""
        total = len(self.proxies)
        healthy = len([p for p in self.proxies if p.is_healthy])
        
        return {
            "total_proxies": total,
            "healthy_proxies": healthy,
            "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None,
            "sources": ["ProxyScrape", "Free-Proxy-List", "GeoNode"]
        }


# Global proxy manager instance
proxy_manager = ProxyManager()


async def fetch_with_proxy(url: str, timeout: int = 15, retries: int = 3) -> Optional[str]:
    """Fetch a URL using proxy rotation with retries"""
    
    headers = {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
    
    for attempt in range(retries):
        proxy = await proxy_manager.get_proxy()
        
        try:
            if proxy:
                async with httpx.AsyncClient(
                    proxies={"http://": proxy.url, "https://": proxy.url},
                    timeout=timeout,
                    follow_redirects=True
                ) as client:
                    response = await client.get(url, headers=headers)
                    if response.status_code == 200:
                        proxy.mark_success()
                        return response.text
                    else:
                        proxy.mark_failure()
            else:
                # Fallback to direct request if no proxies available
                async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                    response = await client.get(url, headers=headers)
                    if response.status_code == 200:
                        return response.text
                        
        except Exception as e:
            logger.warning(f"Fetch attempt {attempt + 1} failed for {url}: {e}")
            if proxy:
                proxy.mark_failure()
    
    return None


async def search_duckduckgo(query: str, max_results: int = 20) -> List[Dict]:
    """
    Search DuckDuckGo for results (free, no API key needed)
    Returns list of {title, url, snippet}
    """
    results = []
    encoded_query = query.replace(' ', '+')
    search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
    
    html = await fetch_with_proxy(search_url)
    
    if html:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # DuckDuckGo HTML results
        for result in soup.select('.result'):
            title_elem = result.select_one('.result__title a')
            snippet_elem = result.select_one('.result__snippet')
            
            if title_elem:
                href = title_elem.get('href', '')
                # DuckDuckGo wraps URLs, extract actual URL
                if 'uddg=' in href:
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    actual_url = parsed.get('uddg', [''])[0]
                else:
                    actual_url = href
                
                if actual_url and actual_url.startswith('http'):
                    results.append({
                        'title': title_elem.get_text(strip=True),
                        'url': actual_url,
                        'snippet': snippet_elem.get_text(strip=True) if snippet_elem else ''
                    })
            
            if len(results) >= max_results:
                break
    
    return results
