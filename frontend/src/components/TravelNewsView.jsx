import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Newspaper,
  Search,
  ExternalLink,
  RefreshCw,
  Clock,
  Filter,
  AlertTriangle,
  CloudRain,
  Building2,
  Plane,
  Scale,
  Users,
  CheckCircle2,
  Radio
} from 'lucide-react';
import { api } from '../services/api';

const CATEGORY_CHIPS = [
  { id: 'ALL', label: 'All News', icon: Newspaper },
  { id: 'AIRLINE', label: 'Airline Operations', icon: Plane },
  { id: 'AIRPORT', label: 'Airport & ATC', icon: Building2 },
  { id: 'WEATHER', label: 'Weather Alerts', icon: CloudRain },
  { id: 'POLICY', label: 'Passenger Rights', icon: Scale },
  { id: 'STRIKE', label: 'Strikes & Protests', icon: Users },
];

function formatTimeAgo(isoString) {
  if (!isoString) return 'Recent';
  try {
    const pub = new Date(isoString);
    const now = new Date();
    const diffMs = now - pub;
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return 'Just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHours = Math.floor(diffMin / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return 'Yesterday';
    return `${diffDays}d ago`;
  } catch {
    return 'Recent';
  }
}

export function TravelNewsView({
  activeJourneyContext = null,
  embeddedMode = false
}) {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [metadata, setMetadata] = useState(null);

  const fetchNews = useCallback(async (forceRefresh = false) => {
    if (forceRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const params = {
        limit: 20,
        force_refresh: forceRefresh,
      };

      if (searchQuery.trim()) {
        params.q = searchQuery.trim();
      }

      if (activeJourneyContext) {
        if (activeJourneyContext.airline) params.airline = activeJourneyContext.airline;
        if (activeJourneyContext.airport) params.airport = activeJourneyContext.airport;
      }

      const res = await api.getNews(params);
      setArticles(res.articles || []);
      setMetadata({
        cached: res.cached,
        cacheAge: res.cache_age_seconds,
        status: res.status,
        provider: res.provider,
        warning: res.warning,
      });
    } catch (err) {
      console.error('Error fetching travel news:', err);
      setError(err?.response?.data?.detail || err?.message || 'Could not load news feed');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [searchQuery, activeJourneyContext]);

  useEffect(() => {
    fetchNews();
  }, [fetchNews]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchNews(false);
  };

  const filteredArticles = articles.filter((art) => {
    if (selectedCategory === 'ALL') return true;
    return art.category === selectedCategory;
  });

  const getCategoryBadge = (cat) => {
    switch (cat) {
      case 'WEATHER':
        return <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 font-sans"><CloudRain className="w-3 h-3" /> Weather</span>;
      case 'STRIKE':
        return <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30 font-sans"><Users className="w-3 h-3" /> Strike</span>;
      case 'AIRPORT':
        return <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-purple-500/15 text-purple-300 border border-purple-500/30 font-sans"><Building2 className="w-3 h-3" /> Airport</span>;
      case 'POLICY':
        return <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-sans"><Scale className="w-3 h-3" /> Policy</span>;
      default:
        return <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-sky-500/15 text-sky-300 border border-sky-500/30 font-sans"><Plane className="w-3 h-3" /> Airline</span>;
    }
  };

  return (
    <div className={`space-y-6 ${embeddedMode ? 'p-0' : ''}`}>
      {/* Header & Search Bar */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="rounded-3xl border border-white/[0.08] bg-[#070b16]/80 p-6 shadow-glass-card backdrop-blur-2xl relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-80 h-80 bg-sky-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4 relative z-10">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="p-2 rounded-xl bg-sky-500/20 text-sky-400 border border-sky-500/30 shadow-[0_0_10px_rgba(56,189,248,0.2)]">
                <Radio className="w-4 h-4 animate-pulse" />
              </span>
              <h2 className="text-xl font-bold text-white tracking-tight font-display">
                Live Travel Disruption News Feed
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1 font-sans">
              Real-time Google News RSS intelligence tracking airport delays, airline disruptions, weather advisories &amp; passenger policy updates.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            {metadata && (
              <span className="text-[11px] text-slate-400 bg-[#04060d] px-3 py-1.5 rounded-xl border border-white/[0.08] flex items-center gap-2 font-mono">
                <span className={`w-2 h-2 rounded-full ${metadata.cached ? 'bg-amber-400' : 'bg-emerald-400 animate-pulse'}`} />
                {metadata.cached ? `Cached (${metadata.cacheAge || 0}s ago)` : 'Live RSS Connected'}
              </span>
            )}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => fetchNews(true)}
              disabled={refreshing || loading}
              className="px-3.5 py-2 rounded-xl bg-[#0d1527] hover:bg-[#131f38] border border-white/[0.1] text-xs font-semibold text-slate-200 flex items-center gap-2 transition disabled:opacity-50 cursor-pointer shadow-sm"
              title="Force refresh Google News RSS feed"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-sky-400 ${refreshing ? 'animate-spin' : ''}`} />
              <span className="font-sans">Refresh</span>
            </motion.button>
          </div>
        </div>

        {/* Active Journey Personalization Banner */}
        {activeJourneyContext && (
          <div className="mb-4 p-3.5 rounded-2xl bg-sky-950/30 border border-sky-500/30 flex items-center justify-between gap-3 text-xs text-sky-200">
            <div className="flex items-center gap-2.5">
              <AlertTriangle className="w-4 h-4 text-sky-400 shrink-0" />
              <span className="font-sans">
                <strong className="font-semibold text-white">Contextual Filter Active:</strong> Showing disruptions relevant to{' '}
                <span className="text-sky-300 font-bold">{activeJourneyContext.airline || 'Journey Flight'}</span>
                {activeJourneyContext.airport && <> &middot; <span className="text-sky-300 font-bold">{activeJourneyContext.airport}</span></>}
              </span>
            </div>
            <span className="text-[10px] font-mono bg-sky-500/20 px-2.5 py-0.5 rounded-full border border-sky-500/40 text-sky-300">
              Auto-Matched
            </span>
          </div>
        )}

        {/* Search Input */}
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search disruption keywords (e.g. IndiGo delay, fog Delhi airport, baggage policy)..."
              className="w-full pl-9 pr-4 py-2 bg-[#04060d] border border-white/[0.1] rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition font-sans"
            />
          </div>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            className="px-4 py-2 bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white rounded-xl text-xs font-semibold shadow-[0_0_15px_rgba(56,189,248,0.25)] transition cursor-pointer font-display"
          >
            Search
          </motion.button>
          {searchQuery && (
            <button
              type="button"
              onClick={() => {
                setSearchQuery('');
                setTimeout(() => fetchNews(false), 50);
              }}
              className="px-3.5 py-2 bg-[#0d1527] hover:bg-[#152038] text-slate-300 rounded-xl text-xs font-medium border border-white/[0.1] transition cursor-pointer font-sans"
            >
              Clear
            </button>
          )}
        </form>

        {/* Category Filter Chips */}
        <div className="flex flex-wrap items-center gap-2 mt-4 pt-4 border-t border-white/[0.08]">
          <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1.5 mr-1 font-mono">
            <Filter className="w-3.5 h-3.5 text-sky-400" /> Filters:
          </span>
          {CATEGORY_CHIPS.map((chip) => {
            const Icon = chip.icon;
            const isSelected = selectedCategory === chip.id;
            return (
              <motion.button
                whileTap={{ scale: 0.96 }}
                key={chip.id}
                onClick={() => setSelectedCategory(chip.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer font-display ${
                  isSelected
                    ? 'bg-sky-600 text-white shadow-[0_0_12px_rgba(56,189,248,0.3)] border border-sky-400/40'
                    : 'bg-[#04060d] text-slate-400 hover:text-slate-200 border border-white/[0.08] hover:border-white/[0.2]'
                }`}
              >
                <Icon className="w-3 h-3" />
                <span>{chip.label}</span>
              </motion.button>
            );
          })}
        </div>
      </motion.div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-2xl bg-rose-950/30 border border-rose-500/40 text-rose-300 text-xs flex items-center justify-between">
          <span>Failed to load news: {error}</span>
          <button
            onClick={() => fetchNews(true)}
            className="px-3 py-1.5 bg-rose-900/60 hover:bg-rose-800 text-rose-100 rounded-xl text-xs border border-rose-600 cursor-pointer font-semibold"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading Skeletons */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((n) => (
            <div
              key={n}
              className="p-5 rounded-2xl border border-white/[0.08] bg-[#070b16]/60 animate-pulse space-y-3"
            >
              <div className="flex items-center justify-between">
                <div className="h-4 w-24 bg-white/[0.08] rounded-full" />
                <div className="h-3 w-16 bg-white/[0.06] rounded-full" />
              </div>
              <div className="h-5 w-3/4 bg-white/[0.1] rounded-lg" />
              <div className="h-3 w-full bg-white/[0.05] rounded" />
              <div className="h-3 w-5/6 bg-white/[0.05] rounded" />
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && filteredArticles.length === 0 && (
        <div className="text-center py-16 px-4 rounded-3xl border border-dashed border-white/[0.1] bg-[#070b16]/50">
          <Newspaper className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-slate-300 font-display">No Disruption News Found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto font-sans">
            No live articles matched category &quot;{selectedCategory}&quot; or query &quot;{searchQuery}&quot;. Try resetting filters or searching broader keywords like &quot;flight delay&quot; or &quot;airport&quot;.
          </p>
          <button
            onClick={() => {
              setSelectedCategory('ALL');
              setSearchQuery('');
              setTimeout(() => fetchNews(true), 50);
            }}
            className="mt-4 px-4 py-2 rounded-xl bg-[#0d1527] hover:bg-[#131f38] text-xs font-semibold text-sky-400 border border-white/[0.1] transition cursor-pointer font-display"
          >
            Reset All Filters
          </button>
        </div>
      )}

      {/* News Cards Grid */}
      {!loading && filteredArticles.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredArticles.map((article, idx) => (
            <motion.article
              key={article.id || idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25, delay: idx * 0.03 }}
              className="rounded-2xl border border-white/[0.08] bg-[#070b16]/80 hover:bg-[#0c1324] hover:border-white/[0.18] p-5 shadow-glass-card hover:shadow-glow-sm transition flex flex-col justify-between group"
            >
              <div>
                {/* Header: Category Badge + Source + Time Ago */}
                <div className="flex items-center justify-between gap-2 mb-3">
                  <div className="flex items-center gap-2">
                    {getCategoryBadge(article.category)}
                    <span className="text-[11px] font-medium text-slate-400 bg-white/[0.06] px-2.5 py-0.5 rounded-full border border-white/[0.08] truncate max-w-[130px] font-mono">
                      {article.source}
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-500 flex items-center gap-1 shrink-0 font-mono">
                    <Clock className="w-3 h-3 text-slate-500" />
                    {formatTimeAgo(article.published_time)}
                  </span>
                </div>

                {/* Headline */}
                <h3 className="text-sm font-bold text-white group-hover:text-sky-300 transition line-clamp-2 leading-snug mb-2 font-display">
                  <a
                    href={article.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="focus:outline-none"
                  >
                    {article.title}
                  </a>
                </h3>

                {/* Snippet */}
                <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed mb-4 font-sans">
                  {article.snippet}
                </p>
              </div>

              {/* Action: Open Link */}
              <div className="pt-3 border-t border-white/[0.08] flex items-center justify-between text-xs">
                <span className="text-[11px] text-slate-500 font-mono">
                  Google News RSS Verified
                </span>
                <a
                  href={article.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 font-semibold text-sky-400 hover:text-sky-300 text-xs transition font-display"
                >
                  <span>Read Article</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </motion.article>
          ))}
        </div>
      )}

      {/* Educational Notice Footer */}
      <div className="text-[11px] text-slate-500 text-center py-2 font-mono">
        <span>News aggregated via Google News RSS for educational and research disruption monitoring.</span>
      </div>
    </div>
  );
}

export default TravelNewsView;
