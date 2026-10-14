import React, { useState, useEffect, useCallback } from 'react';
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
  CheckCircle2
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
        return <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-md bg-cyan-500/15 text-cyan-300 border border-cyan-500/30"><CloudRain className="w-3 h-3" /> Weather</span>;
      case 'STRIKE':
        return <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-md bg-amber-500/15 text-amber-300 border border-amber-500/30"><Users className="w-3 h-3" /> Strike</span>;
      case 'AIRPORT':
        return <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-md bg-purple-500/15 text-purple-300 border border-purple-500/30"><Building2 className="w-3 h-3" /> Airport</span>;
      case 'POLICY':
        return <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-md bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"><Scale className="w-3 h-3" /> Policy</span>;
      default:
        return <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-md bg-sky-500/15 text-sky-300 border border-sky-500/30"><Plane className="w-3 h-3" /> Airline</span>;
    }
  };

  return (
    <div className={`space-y-5 ${embeddedMode ? 'p-0' : ''}`}>
      {/* Header & Search Bar */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-lg backdrop-blur">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-sky-500/20 text-sky-400 border border-sky-500/30">
                <Newspaper className="w-4 h-4" />
              </span>
              <h2 className="text-base font-bold text-white tracking-tight">
                Live Travel Disruption News Feed
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Real-time Google News RSS intelligence tracking airport delays, airline disruptions, weather advisories & passenger policy updates.
            </p>
          </div>

          <div className="flex items-center gap-2">
            {metadata && (
              <span className="text-[11px] text-slate-400 bg-slate-800/80 px-2.5 py-1 rounded-lg border border-slate-700/60 flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${metadata.cached ? 'bg-amber-400' : 'bg-emerald-400 animate-pulse'}`} />
                {metadata.cached ? `Cached (${metadata.cacheAge || 0}s ago)` : 'Live RSS'}
              </span>
            )}
            <button
              onClick={() => fetchNews(true)}
              disabled={refreshing || loading}
              className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-200 flex items-center gap-1.5 transition disabled:opacity-50 cursor-pointer"
              title="Force refresh Google News RSS feed"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-sky-400' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Active Journey Personalization Banner */}
        {activeJourneyContext && (
          <div className="mb-4 p-3 rounded-xl bg-sky-950/40 border border-sky-800/60 flex items-center justify-between gap-3 text-xs text-sky-200">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-sky-400 shrink-0" />
              <span>
                <strong>Contextual Filter Active:</strong> Showing disruptions relevant to{' '}
                <span className="underline font-semibold">{activeJourneyContext.airline || 'Journey Flight'}</span>
                {activeJourneyContext.airport && <> &middot; <span className="underline font-semibold">{activeJourneyContext.airport}</span></>}
              </span>
            </div>
            <span className="text-[10px] bg-sky-900/60 px-2 py-0.5 rounded border border-sky-700 text-sky-300">
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
              className="w-full pl-9 pr-4 py-2 bg-slate-950/80 border border-slate-800 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-semibold shadow transition cursor-pointer"
          >
            Search
          </button>
          {searchQuery && (
            <button
              type="button"
              onClick={() => {
                setSearchQuery('');
                setTimeout(() => fetchNews(false), 50);
              }}
              className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-medium border border-slate-700 transition cursor-pointer"
            >
              Clear
            </button>
          )}
        </form>

        {/* Category Filter Chips */}
        <div className="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-slate-800/80">
          <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1 mr-1">
            <Filter className="w-3 h-3" /> Filters:
          </span>
          {CATEGORY_CHIPS.map((chip) => {
            const Icon = chip.icon;
            const isSelected = selectedCategory === chip.id;
            return (
              <button
                key={chip.id}
                onClick={() => setSelectedCategory(chip.id)}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium flex items-center gap-1.5 transition cursor-pointer ${
                  isSelected
                    ? 'bg-sky-600 text-white shadow-sm'
                    : 'bg-slate-950/60 text-slate-400 hover:text-slate-200 border border-slate-800 hover:border-slate-700'
                }`}
              >
                <Icon className="w-3 h-3" />
                <span>{chip.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-800/60 text-rose-300 text-xs flex items-center justify-between">
          <span>Failed to load news: {error}</span>
          <button
            onClick={() => fetchNews(true)}
            className="px-2.5 py-1 bg-rose-900/60 hover:bg-rose-800 text-rose-100 rounded-lg text-xs border border-rose-700 cursor-pointer"
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
              className="p-4 rounded-2xl border border-slate-800/80 bg-slate-900/40 animate-pulse space-y-3"
            >
              <div className="flex items-center justify-between">
                <div className="h-4 w-20 bg-slate-800 rounded" />
                <div className="h-3 w-16 bg-slate-800 rounded" />
              </div>
              <div className="h-5 w-3/4 bg-slate-800 rounded" />
              <div className="h-3 w-full bg-slate-800/60 rounded" />
              <div className="h-3 w-5/6 bg-slate-800/60 rounded" />
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && filteredArticles.length === 0 && (
        <div className="text-center py-12 px-4 rounded-2xl border border-dashed border-slate-800 bg-slate-900/30">
          <Newspaper className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-slate-300">No Disruption News Found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            No live articles matched category &quot;{selectedCategory}&quot; or query &quot;{searchQuery}&quot;. Try resetting filters or searching broader keywords like &quot;flight delay&quot; or &quot;airport&quot;.
          </p>
          <button
            onClick={() => {
              setSelectedCategory('ALL');
              setSearchQuery('');
              setTimeout(() => fetchNews(true), 50);
            }}
            className="mt-4 px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-sky-400 border border-slate-700 transition cursor-pointer"
          >
            Reset All Filters
          </button>
        </div>
      )}

      {/* News Cards Grid */}
      {!loading && filteredArticles.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredArticles.map((article) => (
            <article
              key={article.id}
              className="rounded-2xl border border-slate-800/90 bg-slate-900/60 hover:bg-slate-900 hover:border-slate-700 p-4 shadow-sm hover:shadow-md transition flex flex-col justify-between group"
            >
              <div>
                {/* Header: Category Badge + Source + Time Ago */}
                <div className="flex items-center justify-between gap-2 mb-2.5">
                  <div className="flex items-center gap-2">
                    {getCategoryBadge(article.category)}
                    <span className="text-[11px] font-medium text-slate-400 bg-slate-800/70 px-2 py-0.5 rounded border border-slate-700/60 truncate max-w-[130px]">
                      {article.source}
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-500 flex items-center gap-1 shrink-0">
                    <Clock className="w-3 h-3" />
                    {formatTimeAgo(article.published_time)}
                  </span>
                </div>

                {/* Headline */}
                <h3 className="text-sm font-bold text-white group-hover:text-sky-300 transition line-clamp-2 leading-snug mb-2">
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
                <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed mb-4">
                  {article.snippet}
                </p>
              </div>

              {/* Action: Open Link */}
              <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-xs">
                <span className="text-[11px] text-slate-500">
                  Google News RSS Verified
                </span>
                <a
                  href={article.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 font-semibold text-sky-400 hover:text-sky-300 text-xs transition"
                >
                  <span>Read Article</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </article>
          ))}
        </div>
      )}

      {/* Educational Notice Footer */}
      <div className="text-[11px] text-slate-500 text-center py-2">
        <span>News aggregated via Google News RSS for educational and research disruption monitoring. Review Google terms before commercial redistribution.</span>
      </div>
    </div>
  );
}

export default TravelNewsView;
