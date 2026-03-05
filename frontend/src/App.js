import React, { useState, useEffect, createContext, useContext } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";
import {
  Home, Search, Link2, BarChart2, Folder, Mail, Settings, LogOut, Menu, X,
  Plus, Trash2, Edit, Send, RefreshCw, ExternalLink, ChevronRight, TrendingUp
} from "lucide-react";
import "@/App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext(null);

const useAuth = () => useContext(AuthContext);

// API Client with Auth
const apiClient = axios.create({ baseURL: API });

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// ============= COMPONENTS =============

const Button = ({ children, variant = "primary", size = "default", className = "", ...props }) => {
  const variants = {
    primary: "bg-[#22C55E] text-white hover:bg-[#16A34A] shadow-[0_0_10px_rgba(34,197,94,0.2)]",
    secondary: "bg-transparent border border-[#27272A] hover:bg-[#1C1C1E] text-[#FAFAFA]",
    ghost: "hover:bg-[#1C1C1E] text-[#A1A1AA] hover:text-[#FAFAFA]",
    destructive: "bg-red-500/10 text-red-500 hover:bg-red-500/20 border border-red-500/20"
  };
  const sizes = {
    default: "px-4 py-2",
    sm: "px-3 py-1.5 text-sm",
    lg: "px-6 py-3"
  };
  return (
    <button
      className={`rounded-md font-medium transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

const Input = ({ className = "", ...props }) => (
  <input
    className={`bg-[#121214] border border-[#27272A] rounded-md h-10 px-3 text-sm placeholder:text-[#52525B] focus:ring-1 focus:ring-[#22C55E] focus:border-[#22C55E] transition-colors w-full ${className}`}
    {...props}
  />
);

const Card = ({ children, className = "", interactive = false }) => (
  <div className={`bg-[#121214] border border-[#27272A] rounded-lg p-6 ${interactive ? "hover:border-[#22C55E]/50 cursor-pointer transition-colors" : ""} ${className}`}>
    {children}
  </div>
);

const Badge = ({ variant = "outline", children }) => {
  const variants = {
    success: "badge-success",
    warning: "badge-warning",
    error: "badge-error",
    info: "badge-info",
    outline: "badge-outline"
  };
  return <span className={`badge ${variants[variant]}`}>{children}</span>;
};

const StatusDot = ({ status }) => {
  const statusMap = {
    found: "found", contacted: "warning", replied: "info", accepted: "success",
    rejected: "error", live: "live", dead: "dead", pending: "pending",
    submitted: "warning", approved: "approved", sent: "success", failed: "error"
  };
  return <span className={`status-dot ${statusMap[status] || "info"}`} />;
};

// ============= SIDEBAR =============

const Sidebar = ({ collapsed, setCollapsed }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();

  const navItems = [
    { icon: Home, label: "Dashboard", path: "/" },
    { icon: Search, label: "Guest Posts", path: "/guest-posts" },
    { icon: Link2, label: "Broken Links", path: "/broken-links" },
    { icon: BarChart2, label: "Competitors", path: "/competitors" },
    { icon: Folder, label: "Directories", path: "/directories" },
    { icon: Mail, label: "Outreach", path: "/outreach" },
    { icon: Settings, label: "Settings", path: "/settings" }
  ];

  return (
    <aside className={`fixed left-0 top-0 h-screen bg-[#121214]/95 backdrop-blur-xl border-r border-[#27272A] z-50 transition-all duration-300 ${collapsed ? "w-16" : "w-60"}`}>
      <div className="flex flex-col h-full">
        <div className="h-16 flex items-center justify-between px-4 border-b border-[#27272A]">
          {!collapsed && <span className="text-lg font-bold text-[#22C55E]">LinkBuilder</span>}
          <button onClick={() => setCollapsed(!collapsed)} className="p-2 hover:bg-[#1C1C1E] rounded-md transition-colors" data-testid="sidebar-toggle">
            {collapsed ? <Menu size={20} /> : <X size={20} />}
          </button>
        </div>

        <nav className="flex-1 py-4 px-2 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                data-testid={`nav-${item.label.toLowerCase().replace(" ", "-")}`}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md transition-all duration-200 ${
                  isActive ? "bg-[#22C55E]/10 text-[#22C55E] border border-[#22C55E]/20" : "text-[#A1A1AA] hover:bg-[#1C1C1E] hover:text-[#FAFAFA]"
                }`}
              >
                <Icon size={20} />
                {!collapsed && <span className="text-sm font-medium">{item.label}</span>}
              </button>
            );
          })}
        </nav>

        <div className="p-2 border-t border-[#27272A]">
          <button onClick={logout} data-testid="logout-btn" className="w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-red-400 hover:bg-red-500/10 transition-colors">
            <LogOut size={20} />
            {!collapsed && <span className="text-sm font-medium">Logout</span>}
          </button>
        </div>
      </div>
    </aside>
  );
};

// ============= LAYOUT =============

const DashboardLayout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-[#09090B]">
      <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
      <main className={`transition-all duration-300 ${collapsed ? "ml-16" : "ml-60"}`}>
        <div className="p-6 lg:p-8 max-w-[1600px] mx-auto">{children}</div>
      </main>
    </div>
  );
};

// ============= PAGES =============

const LoginPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const endpoint = isLogin ? "/auth/login" : "/auth/register";
      const payload = isLogin ? { email, password } : { email, password, name };
      const { data } = await apiClient.post(endpoint, payload);
      login(data.access_token, data.user);
      toast.success(isLogin ? "Welcome back!" : "Account created!");
      navigate("/");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Authentication failed");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#09090B] flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-[#22C55E] mb-2">LinkBuilder</h1>
          <p className="text-[#A1A1AA]">Automated High-DA Backlink Builder</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <div>
              <label className="block text-sm text-[#A1A1AA] mb-1.5">Name</label>
              <Input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" data-testid="name-input" required={!isLogin} />
            </div>
          )}
          <div>
            <label className="block text-sm text-[#A1A1AA] mb-1.5">Email</label>
            <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email@example.com" data-testid="email-input" required />
          </div>
          <div>
            <label className="block text-sm text-[#A1A1AA] mb-1.5">Password</label>
            <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" data-testid="password-input" required />
          </div>
          <Button type="submit" className="w-full" disabled={loading} data-testid="auth-submit-btn">
            {loading ? <RefreshCw className="animate-spin" size={18} /> : isLogin ? "Sign In" : "Create Account"}
          </Button>
        </form>

        <p className="text-center text-sm text-[#A1A1AA] mt-6">
          {isLogin ? "Don't have an account?" : "Already have an account?"}{" "}
          <button onClick={() => setIsLogin(!isLogin)} className="text-[#22C55E] hover:underline" data-testid="toggle-auth-mode">
            {isLogin ? "Sign Up" : "Sign In"}
          </button>
        </p>
      </Card>
    </div>
  );
};

const DashboardPage = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const { data } = await apiClient.get("/dashboard/stats");
        setStats(data);
      } catch (err) {
        toast.error("Failed to load dashboard");
      }
      setLoading(false);
    };
    fetchStats();
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64"><RefreshCw className="animate-spin text-[#22C55E]" size={32} /></div>;

  const statCards = [
    { label: "Guest Post Opportunities", value: stats?.total_guest_posts || 0, icon: Search, color: "text-[#22C55E]" },
    { label: "Broken Links Found", value: stats?.total_broken_links || 0, icon: Link2, color: "text-[#3B82F6]" },
    { label: "Competitor Backlinks", value: stats?.total_competitor_backlinks || 0, icon: BarChart2, color: "text-[#8B5CF6]" },
    { label: "Directories", value: stats?.total_directories || 0, icon: Folder, color: "text-[#F97316]" },
    { label: "Emails Sent", value: stats?.emails_sent || 0, icon: Mail, color: "text-[#EAB308]" }
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
        <p className="text-[#A1A1AA]">Overview of your backlink building progress</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {statCards.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <Card key={i} className="animate-slide-up" style={{ animationDelay: `${i * 50}ms` }}>
              <div className="flex items-center justify-between mb-4">
                <Icon className={stat.color} size={24} />
                <TrendingUp className="text-[#52525B]" size={16} />
              </div>
              <p className="text-3xl font-bold font-mono">{stat.value}</p>
              <p className="text-sm text-[#A1A1AA] mt-1">{stat.label}</p>
            </Card>
          );
        })}
      </div>

      <Card>
        <h2 className="text-xl font-bold mb-4">Recent Opportunities</h2>
        {stats?.recent_opportunities?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Domain</th>
                  <th>Title</th>
                  <th>DA</th>
                  <th>Status</th>
                  <th>Found</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent_opportunities.map((opp) => (
                  <tr key={opp.id}>
                    <td className="font-mono text-[#22C55E]">{opp.domain}</td>
                    <td>{opp.title}</td>
                    <td><Badge variant={opp.da_score >= 50 ? "success" : "warning"}>{opp.da_score}</Badge></td>
                    <td><StatusDot status={opp.status} />{opp.status}</td>
                    <td className="text-[#A1A1AA]">{new Date(opp.found_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12 text-[#A1A1AA]">
            <Search size={48} className="mx-auto mb-4 opacity-50" />
            <p>No opportunities found yet. Start searching!</p>
          </div>
        )}
      </Card>
    </div>
  );
};

const GuestPostsPage = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [query, setQuery] = useState("");
  const [niche, setNiche] = useState("");

  const fetchPosts = async () => {
    try {
      const { data } = await apiClient.get("/guest-posts");
      setPosts(data.items || []);
    } catch (err) {
      toast.error("Failed to load guest posts");
    }
    setLoading(false);
  };

  useEffect(() => { fetchPosts(); }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    try {
      const { data } = await apiClient.post("/guest-posts/search", { query, niche, max_results: 20 });
      toast.success(`Found ${data.count} opportunities!`);
      fetchPosts();
    } catch (err) {
      toast.error("Search failed");
    }
    setSearching(false);
  };

  const handleDelete = async (id) => {
    try {
      await apiClient.delete(`/guest-posts/${id}`);
      toast.success("Deleted");
      fetchPosts();
    } catch (err) {
      toast.error("Delete failed");
    }
  };

  const handleStatusChange = async (id, status) => {
    try {
      await apiClient.put(`/guest-posts/${id}`, { status });
      toast.success("Status updated");
      fetchPosts();
    } catch (err) {
      toast.error("Update failed");
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Guest Post Finder</h1>
          <p className="text-[#A1A1AA]">Find "write for us" opportunities</p>
        </div>
      </div>

      <Card>
        <form onSubmit={handleSearch} className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search keyword (e.g., 'digital marketing')" data-testid="guest-post-search-input" />
          </div>
          <div className="w-48">
            <Input value={niche} onChange={(e) => setNiche(e.target.value)} placeholder="Niche (optional)" data-testid="guest-post-niche-input" />
          </div>
          <Button type="submit" disabled={searching} data-testid="guest-post-search-btn">
            {searching ? <RefreshCw className="animate-spin" size={18} /> : <Search size={18} />}
            Search
          </Button>
        </form>
      </Card>

      <Card>
        {loading ? (
          <div className="flex justify-center py-12"><RefreshCw className="animate-spin text-[#22C55E]" size={32} /></div>
        ) : posts.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Domain</th>
                  <th>Title</th>
                  <th>Niche</th>
                  <th>DA</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {posts.map((post) => (
                  <tr key={post.id}>
                    <td>
                      <a href={post.url} target="_blank" rel="noopener noreferrer" className="font-mono text-[#22C55E] hover:underline flex items-center gap-1">
                        {post.domain} <ExternalLink size={12} />
                      </a>
                    </td>
                    <td className="max-w-[200px] truncate">{post.title}</td>
                    <td>{post.niche || "-"}</td>
                    <td><Badge variant={post.da_score >= 50 ? "success" : post.da_score >= 30 ? "warning" : "error"}>{post.da_score}</Badge></td>
                    <td>
                      <select
                        value={post.status}
                        onChange={(e) => handleStatusChange(post.id, e.target.value)}
                        className="bg-[#1C1C1E] border border-[#27272A] rounded px-2 py-1 text-sm"
                        data-testid={`status-select-${post.id}`}
                      >
                        <option value="found">Found</option>
                        <option value="contacted">Contacted</option>
                        <option value="replied">Replied</option>
                        <option value="accepted">Accepted</option>
                        <option value="rejected">Rejected</option>
                      </select>
                    </td>
                    <td>
                      <button onClick={() => handleDelete(post.id)} className="p-1.5 hover:bg-red-500/10 rounded text-red-400" data-testid={`delete-post-${post.id}`}>
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12 text-[#A1A1AA]">
            <Search size={48} className="mx-auto mb-4 opacity-50" />
            <p>No guest post opportunities yet. Start searching above!</p>
          </div>
        )}
      </Card>
    </div>
  );
};

const BrokenLinksPage = () => {
  const [links, setLinks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [url, setUrl] = useState("");

  const fetchLinks = async () => {
    try {
      const { data } = await apiClient.get("/broken-links");
      setLinks(data.items || []);
    } catch (err) {
      toast.error("Failed to load broken links");
    }
    setLoading(false);
  };

  useEffect(() => { fetchLinks(); }, []);

  const handleScan = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;
    setScanning(true);
    try {
      const { data } = await apiClient.post("/broken-links/scan", { url, max_depth: 1 });
      toast.success(`Found ${data.count} broken links!`);
      fetchLinks();
    } catch (err) {
      toast.error("Scan failed");
    }
    setScanning(false);
  };

  const handleDelete = async (id) => {
    try {
      await apiClient.delete(`/broken-links/${id}`);
      toast.success("Deleted");
      fetchLinks();
    } catch (err) {
      toast.error("Delete failed");
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold mb-2">Broken Link Builder</h1>
        <p className="text-[#A1A1AA]">Find broken links on high DA sites</p>
      </div>

      <Card>
        <form onSubmit={handleScan} className="flex gap-4">
          <div className="flex-1">
            <Input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="Enter URL to scan (e.g., https://example.com/resources)" data-testid="broken-link-url-input" />
          </div>
          <Button type="submit" disabled={scanning} data-testid="broken-link-scan-btn">
            {scanning ? <RefreshCw className="animate-spin" size={18} /> : <Link2 size={18} />}
            Scan
          </Button>
        </form>
      </Card>

      <Card>
        {loading ? (
          <div className="flex justify-center py-12"><RefreshCw className="animate-spin text-[#22C55E]" size={32} /></div>
        ) : links.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Source Domain</th>
                  <th>Broken URL</th>
                  <th>Anchor</th>
                  <th>DA</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {links.map((link) => (
                  <tr key={link.id}>
                    <td className="font-mono text-[#3B82F6]">{link.source_domain}</td>
                    <td className="font-mono text-red-400 max-w-[200px] truncate">{link.broken_url}</td>
                    <td className="max-w-[150px] truncate">{link.anchor_text || "-"}</td>
                    <td><Badge variant={link.da_score >= 50 ? "success" : "warning"}>{link.da_score}</Badge></td>
                    <td><StatusDot status={link.status} />{link.status}</td>
                    <td>
                      <button onClick={() => handleDelete(link.id)} className="p-1.5 hover:bg-red-500/10 rounded text-red-400" data-testid={`delete-link-${link.id}`}>
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12 text-[#A1A1AA]">
            <Link2 size={48} className="mx-auto mb-4 opacity-50" />
            <p>No broken links found yet. Scan a URL above!</p>
          </div>
        )}
      </Card>
    </div>
  );
};

const CompetitorsPage = () => {
  const [backlinks, setBacklinks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [domain, setDomain] = useState("");

  const fetchBacklinks = async () => {
    try {
      const { data } = await apiClient.get("/competitors");
      setBacklinks(data.items || []);
    } catch (err) {
      toast.error("Failed to load backlinks");
    }
    setLoading(false);
  };

  useEffect(() => { fetchBacklinks(); }, []);

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!domain.trim()) return;
    setAnalyzing(true);
    try {
      const { data } = await apiClient.post("/competitors/analyze", { domain, max_results: 50 });
      toast.success(`Found ${data.count} backlinks!`);
      fetchBacklinks();
    } catch (err) {
      toast.error("Analysis failed");
    }
    setAnalyzing(false);
  };

  const handleDelete = async (id) => {
    try {
      await apiClient.delete(`/competitors/${id}`);
      toast.success("Deleted");
      fetchBacklinks();
    } catch (err) {
      toast.error("Delete failed");
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold mb-2">Competitor Analysis</h1>
        <p className="text-[#A1A1AA]">Discover where competitors get their backlinks</p>
      </div>

      <Card>
        <form onSubmit={handleAnalyze} className="flex gap-4">
          <div className="flex-1">
            <Input value={domain} onChange={(e) => setDomain(e.target.value)} placeholder="Competitor domain (e.g., competitor.com)" data-testid="competitor-domain-input" />
          </div>
          <Button type="submit" disabled={analyzing} data-testid="competitor-analyze-btn">
            {analyzing ? <RefreshCw className="animate-spin" size={18} /> : <BarChart2 size={18} />}
            Analyze
          </Button>
        </form>
      </Card>

      <Card>
        {loading ? (
          <div className="flex justify-center py-12"><RefreshCw className="animate-spin text-[#22C55E]" size={32} /></div>
        ) : backlinks.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Competitor</th>
                  <th>Backlink From</th>
                  <th>Anchor</th>
                  <th>DA</th>
                  <th>Type</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {backlinks.map((bl) => (
                  <tr key={bl.id}>
                    <td className="font-mono text-[#8B5CF6]">{bl.competitor_domain}</td>
                    <td>
                      <a href={bl.backlink_url} target="_blank" rel="noopener noreferrer" className="font-mono text-[#22C55E] hover:underline flex items-center gap-1">
                        {bl.backlink_domain} <ExternalLink size={12} />
                      </a>
                    </td>
                    <td className="max-w-[150px] truncate">{bl.anchor_text || "-"}</td>
                    <td><Badge variant={bl.da_score >= 50 ? "success" : "warning"}>{bl.da_score}</Badge></td>
                    <td><Badge variant={bl.link_type === "dofollow" ? "success" : "outline"}>{bl.link_type}</Badge></td>
                    <td>
                      <button onClick={() => handleDelete(bl.id)} className="p-1.5 hover:bg-red-500/10 rounded text-red-400" data-testid={`delete-backlink-${bl.id}`}>
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12 text-[#A1A1AA]">
            <BarChart2 size={48} className="mx-auto mb-4 opacity-50" />
            <p>No competitor backlinks yet. Enter a competitor domain above!</p>
          </div>
        )}
      </Card>
    </div>
  );
};

const DirectoriesPage = () => {
  const [directories, setDirectories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newDir, setNewDir] = useState({ name: "", url: "", category: "" });

  const fetchDirectories = async () => {
    try {
      const { data } = await apiClient.get("/directories");
      setDirectories(data.items || []);
    } catch (err) {
      toast.error("Failed to load directories");
    }
    setLoading(false);
  };

  useEffect(() => { fetchDirectories(); }, []);

  const handleSeed = async () => {
    try {
      await apiClient.post("/directories/seed");
      toast.success("Directories seeded!");
      fetchDirectories();
    } catch (err) {
      toast.error("Seed failed");
    }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    try {
      await apiClient.post("/directories", newDir);
      toast.success("Directory added!");
      setNewDir({ name: "", url: "", category: "" });
      setShowAdd(false);
      fetchDirectories();
    } catch (err) {
      toast.error("Add failed");
    }
  };

  const handleStatusChange = async (id, status) => {
    try {
      await apiClient.put(`/directories/${id}`, { submission_status: status, submitted_at: status === "submitted" ? new Date().toISOString() : "" });
      toast.success("Status updated");
      fetchDirectories();
    } catch (err) {
      toast.error("Update failed");
    }
  };

  const handleDelete = async (id) => {
    try {
      await apiClient.delete(`/directories/${id}`);
      toast.success("Deleted");
      fetchDirectories();
    } catch (err) {
      toast.error("Delete failed");
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Directory Manager</h1>
          <p className="text-[#A1A1AA]">High DA directories for submission</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={handleSeed} data-testid="seed-directories-btn">
            <RefreshCw size={18} /> Load Defaults
          </Button>
          <Button onClick={() => setShowAdd(true)} data-testid="add-directory-btn">
            <Plus size={18} /> Add Directory
          </Button>
        </div>
      </div>

      {showAdd && (
        <Card>
          <form onSubmit={handleAdd} className="flex flex-wrap gap-4">
            <Input value={newDir.name} onChange={(e) => setNewDir({ ...newDir, name: e.target.value })} placeholder="Directory Name" className="flex-1 min-w-[150px]" required data-testid="new-dir-name" />
            <Input value={newDir.url} onChange={(e) => setNewDir({ ...newDir, url: e.target.value })} placeholder="URL" className="flex-1 min-w-[200px]" required data-testid="new-dir-url" />
            <Input value={newDir.category} onChange={(e) => setNewDir({ ...newDir, category: e.target.value })} placeholder="Category" className="w-32" data-testid="new-dir-category" />
            <Button type="submit" data-testid="save-directory-btn">Save</Button>
            <Button type="button" variant="secondary" onClick={() => setShowAdd(false)}>Cancel</Button>
          </form>
        </Card>
      )}

      <Card>
        {loading ? (
          <div className="flex justify-center py-12"><RefreshCw className="animate-spin text-[#22C55E]" size={32} /></div>
        ) : directories.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>URL</th>
                  <th>Category</th>
                  <th>DA</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {directories.map((dir) => (
                  <tr key={dir.id}>
                    <td className="font-medium">{dir.name}</td>
                    <td>
                      <a href={dir.url} target="_blank" rel="noopener noreferrer" className="font-mono text-[#22C55E] hover:underline flex items-center gap-1">
                        {dir.url.replace(/https?:\/\//, "").slice(0, 25)} <ExternalLink size={12} />
                      </a>
                    </td>
                    <td>{dir.category || "-"}</td>
                    <td><Badge variant={dir.da_score >= 70 ? "success" : dir.da_score >= 50 ? "warning" : "info"}>{dir.da_score}</Badge></td>
                    <td>
                      <select
                        value={dir.submission_status}
                        onChange={(e) => handleStatusChange(dir.id, e.target.value)}
                        className="bg-[#1C1C1E] border border-[#27272A] rounded px-2 py-1 text-sm"
                        data-testid={`dir-status-${dir.id}`}
                      >
                        <option value="pending">Pending</option>
                        <option value="submitted">Submitted</option>
                        <option value="approved">Approved</option>
                        <option value="rejected">Rejected</option>
                      </select>
                    </td>
                    <td>
                      <button onClick={() => handleDelete(dir.id)} className="p-1.5 hover:bg-red-500/10 rounded text-red-400" data-testid={`delete-dir-${dir.id}`}>
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12 text-[#A1A1AA]">
            <Folder size={48} className="mx-auto mb-4 opacity-50" />
            <p>No directories yet. Click "Load Defaults" or add manually!</p>
          </div>
        )}
      </Card>
    </div>
  );
};

const OutreachPage = () => {
  const [templates, setTemplates] = useState([]);
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [emailForm, setEmailForm] = useState({ to_email: "", subject: "", body: "" });
  const [activeTab, setActiveTab] = useState("compose");

  const fetchData = async () => {
    try {
      const [templatesRes, emailsRes] = await Promise.all([
        apiClient.get("/outreach/templates"),
        apiClient.get("/outreach/emails")
      ]);
      setTemplates(templatesRes.data.items || []);
      setEmails(emailsRes.data.items || []);
    } catch (err) {
      toast.error("Failed to load outreach data");
    }
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, []);

  const handleSeedTemplates = async () => {
    try {
      await apiClient.post("/outreach/templates/seed");
      toast.success("Templates loaded!");
      fetchData();
    } catch (err) {
      toast.error("Failed to seed templates");
    }
  };

  const handleSendEmail = async (e) => {
    e.preventDefault();
    setSending(true);
    try {
      const { data } = await apiClient.post("/outreach/send", emailForm);
      if (data.success) {
        toast.success("Email sent!");
        setEmailForm({ to_email: "", subject: "", body: "" });
        fetchData();
      } else {
        toast.error("Email failed - check SendGrid configuration");
      }
    } catch (err) {
      toast.error("Send failed");
    }
    setSending(false);
  };

  const applyTemplate = (template) => {
    setEmailForm({ ...emailForm, subject: template.subject, body: template.body.replace(/<[^>]*>/g, "") });
    setActiveTab("compose");
    toast.success("Template loaded - customize placeholders!");
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Email Outreach</h1>
          <p className="text-[#A1A1AA]">Send outreach emails for link building</p>
        </div>
        <Button variant="secondary" onClick={handleSeedTemplates} data-testid="seed-templates-btn">
          <RefreshCw size={18} /> Load Templates
        </Button>
      </div>

      <div className="flex gap-2 border-b border-[#27272A]">
        {["compose", "templates", "sent"].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === tab ? "border-[#22C55E] text-[#22C55E]" : "border-transparent text-[#A1A1AA] hover:text-[#FAFAFA]"}`}
            data-testid={`tab-${tab}`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><RefreshCw className="animate-spin text-[#22C55E]" size={32} /></div>
      ) : activeTab === "compose" ? (
        <Card>
          <form onSubmit={handleSendEmail} className="space-y-4">
            <div>
              <label className="block text-sm text-[#A1A1AA] mb-1.5">To Email</label>
              <Input type="email" value={emailForm.to_email} onChange={(e) => setEmailForm({ ...emailForm, to_email: e.target.value })} placeholder="recipient@example.com" required data-testid="outreach-to-email" />
            </div>
            <div>
              <label className="block text-sm text-[#A1A1AA] mb-1.5">Subject</label>
              <Input value={emailForm.subject} onChange={(e) => setEmailForm({ ...emailForm, subject: e.target.value })} placeholder="Email subject" required data-testid="outreach-subject" />
            </div>
            <div>
              <label className="block text-sm text-[#A1A1AA] mb-1.5">Body</label>
              <textarea
                value={emailForm.body}
                onChange={(e) => setEmailForm({ ...emailForm, body: e.target.value })}
                className="w-full bg-[#121214] border border-[#27272A] rounded-md p-3 h-48 text-sm placeholder:text-[#52525B] focus:ring-1 focus:ring-[#22C55E] focus:border-[#22C55E]"
                placeholder="Email body..."
                required
                data-testid="outreach-body"
              />
            </div>
            <Button type="submit" disabled={sending} data-testid="send-email-btn">
              {sending ? <RefreshCw className="animate-spin" size={18} /> : <Send size={18} />}
              Send Email
            </Button>
          </form>
        </Card>
      ) : activeTab === "templates" ? (
        <div className="grid gap-4">
          {templates.length > 0 ? templates.map((t) => (
            <Card key={t.id} interactive onClick={() => applyTemplate(t)}>
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-bold">{t.name}</h3>
                <Badge variant="outline">{t.template_type}</Badge>
              </div>
              <p className="text-sm text-[#A1A1AA] mb-2">{t.subject}</p>
              <p className="text-xs text-[#52525B] line-clamp-2">{t.body.replace(/<[^>]*>/g, "").slice(0, 150)}...</p>
            </Card>
          )) : (
            <div className="text-center py-12 text-[#A1A1AA]">
              <Mail size={48} className="mx-auto mb-4 opacity-50" />
              <p>No templates yet. Click "Load Templates" above!</p>
            </div>
          )}
        </div>
      ) : (
        <Card>
          {emails.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>To</th>
                    <th>Subject</th>
                    <th>Status</th>
                    <th>Sent At</th>
                  </tr>
                </thead>
                <tbody>
                  {emails.map((email) => (
                    <tr key={email.id}>
                      <td className="font-mono">{email.to_email}</td>
                      <td className="max-w-[200px] truncate">{email.subject}</td>
                      <td><StatusDot status={email.status} />{email.status}</td>
                      <td className="text-[#A1A1AA]">{email.sent_at ? new Date(email.sent_at).toLocaleString() : "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 text-[#A1A1AA]">
              <Mail size={48} className="mx-auto mb-4 opacity-50" />
              <p>No emails sent yet.</p>
            </div>
          )}
        </Card>
      )}
    </div>
  );
};

const SettingsPage = () => {
  const [settings, setSettings] = useState({});
  const [proxyStats, setProxyStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [refreshingProxies, setRefreshingProxies] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [settingsRes, proxyRes] = await Promise.all([
          apiClient.get("/settings"),
          apiClient.get("/proxy/stats")
        ]);
        setSettings(settingsRes.data);
        setProxyStats(proxyRes.data);
      } catch (err) {
        toast.error("Failed to load settings");
      }
      setLoading(false);
    };
    fetchData();
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await apiClient.put("/settings", settings);
      toast.success("Settings saved!");
    } catch (err) {
      toast.error("Save failed");
    }
    setSaving(false);
  };

  const handleRefreshProxies = async () => {
    setRefreshingProxies(true);
    try {
      const { data } = await apiClient.post("/proxy/refresh");
      toast.success(`Loaded ${data.proxy_count} proxies!`);
      const proxyRes = await apiClient.get("/proxy/stats");
      setProxyStats(proxyRes.data);
    } catch (err) {
      toast.error("Failed to refresh proxies");
    }
    setRefreshingProxies(false);
  };

  if (loading) return <div className="flex items-center justify-center h-64"><RefreshCw className="animate-spin text-[#22C55E]" size={32} /></div>;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold mb-2">Settings</h1>
        <p className="text-[#A1A1AA]">Configure your backlink builder</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="text-xl font-bold mb-4">Profile</h2>
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="block text-sm text-[#A1A1AA] mb-1.5">Your Name</label>
              <Input value={settings.your_name || ""} onChange={(e) => setSettings({ ...settings, your_name: e.target.value })} placeholder="John Doe" data-testid="settings-name" />
            </div>
            <div>
              <label className="block text-sm text-[#A1A1AA] mb-1.5">Your Website</label>
              <Input value={settings.your_website || ""} onChange={(e) => setSettings({ ...settings, your_website: e.target.value })} placeholder="https://yoursite.com" data-testid="settings-website" />
            </div>
            <div>
              <label className="block text-sm text-[#A1A1AA] mb-1.5">Default Niche</label>
              <Input value={settings.default_niche || ""} onChange={(e) => setSettings({ ...settings, default_niche: e.target.value })} placeholder="e.g., Digital Marketing" data-testid="settings-niche" />
            </div>
            <Button type="submit" disabled={saving} data-testid="save-settings-btn">
              {saving ? <RefreshCw className="animate-spin" size={18} /> : null}
              Save Settings
            </Button>
          </form>
        </Card>

        <div className="space-y-6">
          <Card>
            <h2 className="text-xl font-bold mb-4">Proxy Configuration</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-[#1C1C1E] rounded-md">
                <span className="text-sm">Total Proxies</span>
                <Badge variant={proxyStats?.total_proxies > 0 ? "success" : "error"}>
                  {proxyStats?.total_proxies || 0}
                </Badge>
              </div>
              <div className="flex items-center justify-between p-3 bg-[#1C1C1E] rounded-md">
                <span className="text-sm">Healthy Proxies</span>
                <Badge variant={proxyStats?.healthy_proxies > 50 ? "success" : "warning"}>
                  {proxyStats?.healthy_proxies || 0}
                </Badge>
              </div>
              <div className="p-3 bg-[#1C1C1E] rounded-md">
                <span className="text-sm text-[#A1A1AA]">Sources: </span>
                <span className="text-sm font-mono">{proxyStats?.sources?.join(", ") || "None"}</span>
              </div>
              {proxyStats?.last_refresh && (
                <p className="text-xs text-[#52525B]">
                  Last refresh: {new Date(proxyStats.last_refresh).toLocaleString()}
                </p>
              )}
              <Button variant="secondary" onClick={handleRefreshProxies} disabled={refreshingProxies} className="w-full" data-testid="refresh-proxies-btn">
                {refreshingProxies ? <RefreshCw className="animate-spin" size={18} /> : <RefreshCw size={18} />}
                Refresh Proxy Pool
              </Button>
              <p className="text-xs text-[#52525B]">
                Proxies are automatically refreshed every 30 minutes. Use free proxy rotation for web scraping.
              </p>
            </div>
          </Card>

          <Card>
            <h2 className="text-xl font-bold mb-4">Email Configuration</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-[#1C1C1E] rounded-md">
                <span className="text-sm">SendGrid Status</span>
                <Badge variant={settings.sendgrid_configured ? "success" : "error"}>
                  {settings.sendgrid_configured ? "Configured" : "Not Configured"}
                </Badge>
              </div>
              <div>
                <label className="block text-sm text-[#A1A1AA] mb-1.5">Sender Email</label>
                <Input value={settings.sender_email || ""} disabled className="bg-[#1C1C1E]" />
                <p className="text-xs text-[#52525B] mt-1">Set via SENDER_EMAIL environment variable</p>
              </div>
              <div className="p-4 bg-[#22C55E]/10 border border-[#22C55E]/20 rounded-md">
                <p className="text-sm text-[#22C55E]">
                  To enable email outreach, set SENDGRID_API_KEY and SENDER_EMAIL in your backend .env file.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

// ============= PROTECTED ROUTE =============

const ProtectedRoute = ({ children }) => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <DashboardLayout>{children}</DashboardLayout>;
};

// ============= APP =============

function App() {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("user");
    return saved ? JSON.parse(saved) : null;
  });

  const login = (token, userData) => {
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(userData));
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      <BrowserRouter>
        <Toaster position="bottom-right" theme="dark" richColors />
        <Routes>
          <Route path="/login" element={user ? <Navigate to="/" /> : <LoginPage />} />
          <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/guest-posts" element={<ProtectedRoute><GuestPostsPage /></ProtectedRoute>} />
          <Route path="/broken-links" element={<ProtectedRoute><BrokenLinksPage /></ProtectedRoute>} />
          <Route path="/competitors" element={<ProtectedRoute><CompetitorsPage /></ProtectedRoute>} />
          <Route path="/directories" element={<ProtectedRoute><DirectoriesPage /></ProtectedRoute>} />
          <Route path="/outreach" element={<ProtectedRoute><OutreachPage /></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
        </Routes>
      </BrowserRouter>
    </AuthContext.Provider>
  );
}

export default App;
