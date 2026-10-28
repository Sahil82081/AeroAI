import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  Mail,
  Network,
  Bell,
  Bot,
  MessageSquare,
  Menu,
  X,
  Activity,
  Layers,
  Cpu,
  RefreshCw,
  User,
  LogIn,
  ChevronRight,
  Plane
} from 'lucide-react';
import { api } from '../services/api';
import { InboxView } from './InboxView';
import { JourneyGraphView } from './JourneyGraphView';
import { SupplierEcosystemView } from './SupplierEcosystemView';
import { ActionExecutionView } from './ActionExecutionView';
import { NotificationInboxView } from './NotificationInboxView';
import { SimpleGuidedStoryMode } from './pages/SimpleGuidedStoryMode';
import { PolicyAssistantChat } from './PolicyAssistantChat';
import { AeroAIFlightIntelligenceView } from './AeroAIFlightIntelligenceView';
import { LoginPage } from './pages/LoginPage';
import {
  ToastViewport,
  ErrorAlertBanner,
  PulseBadge
} from './ui/SaaSPrimitives';

const TOP_TABS = [
  { id: 'intelligence', label: 'Flight Intelligence & Agent', icon: Plane, badge: 'Live AI' },
  { id: 'guided', label: 'My Journey', icon: Sparkles },
  { id: 'inbox', label: 'Email Parser', icon: Mail },
  { id: 'recovery-plan', label: 'AI Optimizer & Graph', icon: Network },
  { id: 'notifications', label: 'Sent Emails & Logs', icon: Bell },
  { id: 'chatbot', label: 'Policy Chatbot', icon: MessageSquare },
];

export function DashboardShell({
  journeys = [],
  inboxEmails = [],
  sampleEmails = [],
  graphData = null,
  onForwardEmail,
  forwardingLoading = false,
  onRefreshGraph,
  onRefresh,
  loading,
  error = null,
  user = null,
  health = null,
}) {
  const [activePage, setActivePage] = useState('intelligence');
  const [toasts, setToasts] = useState([]);
  const [actionHistory, setActionHistory] = useState(null);
  const [runningDemo, setRunningDemo] = useState(false);
  const [optimizerSubTab, setOptimizerSubTab] = useState('graph');
  const [logsSubTab, setLogsSubTab] = useState('emails');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const navBarRef = useRef(null);

  // Dynamically measure navbar height to guarantee main content is never overlapped across zoom / wraps
  useEffect(() => {
    const updateHeaderHeight = () => {
      if (navBarRef.current) {
        const h = navBarRef.current.offsetHeight;
        if (h > 0) {
          document.documentElement.style.setProperty('--header-height', `${h}px`);
        }
      }
    };

    updateHeaderHeight();

    let resizeObserver = null;
    if (typeof ResizeObserver !== 'undefined' && navBarRef.current) {
      resizeObserver = new ResizeObserver(updateHeaderHeight);
      resizeObserver.observe(navBarRef.current);
    }

    window.addEventListener('resize', updateHeaderHeight);
    return () => {
      if (resizeObserver) resizeObserver.disconnect();
      window.removeEventListener('resize', updateHeaderHeight);
    };
  }, []);

  const currentJourney = journeys[0];

  const addToast = useCallback((title, message = '', type = 'success') => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    setToasts((prev) => [...prev.slice(-3), { id, title, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }, []);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const fetchActionHistory = useCallback(async () => {
    try {
      const h = await api.getActionHistory();
      setActionHistory(h);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    fetchActionHistory();
  }, [fetchActionHistory]);

  const handleExecuteRecoveryPlanActions = async () => {
    setRunningDemo(true);
    try {
      const res = await api.executeRecoveryPlan({
        plan_id: `PLAN-${Date.now().toString().slice(-4)}`,
        max_retries: 2,
        timeout_ms: 2500,
      });
      await fetchActionHistory();
      addToast(
        'Recovery Actions Executed',
        `Plan ${res.plan_id} completed with status: ${res.execution_status}`,
        'success'
      );
    } catch (err) {
      addToast('Action Execution Error', err?.message || 'Failed to execute plan', 'error');
    } finally {
      setRunningDemo(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface-container-lowest text-on-surface font-body-md antialiased relative selection:bg-primary-container selection:text-on-primary-container overflow-x-hidden flex flex-col justify-between">
      <ToastViewport toasts={toasts} onDismiss={dismissToast} />

      {/* Ambient Background Glows */}
      <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-primary-container/5 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute top-1/3 right-10 w-[500px] h-[500px] bg-secondary/5 rounded-full blur-[160px] pointer-events-none" />

      {/* Top Navigation Header - Refined Production Enterprise SaaS */}
      <header className="fixed top-0 left-0 right-0 z-40 bg-surface-container-lowest/90 backdrop-blur-xl border-b border-surface-container-high/60 transition-all">
        <div
          ref={navBarRef}
          className="max-w-7xl mx-auto min-h-16 px-3 sm:px-6 lg:px-8 flex items-center justify-between gap-3 sm:gap-6"
        >
          {/* Brand Logo & Tag */}
          <div
            onClick={() => setActivePage('intelligence')}
            className="flex items-center gap-3 shrink-0 cursor-pointer group"
          >
            <div className="w-8.5 h-8.5 rounded-lg bg-gradient-to-br from-surface-container-high to-surface-container flex items-center justify-center text-primary-container border border-primary-container/30 shadow-sm group-hover:scale-105 group-hover:border-primary-container/60 transition-all duration-200">
              <Plane className="w-4 h-4 text-primary-container group-hover:rotate-12 transition-transform duration-200" />
            </div>

            <div className="flex items-center gap-2 sm:gap-2.5">
              <span className="font-headline-md text-base sm:text-lg font-bold tracking-tight text-on-surface">
                AeroAI
              </span>
              <span className="text-outline/30 font-light text-xs hidden sm:inline">|</span>
              <span className="font-label-caps text-[10px] uppercase tracking-wider text-primary px-2 py-0.5 rounded-md bg-surface-container-high/80 border border-primary/20 backdrop-blur-sm hidden md:inline">
                Disruption Recovery
              </span>
            </div>
          </div>

          {/* Center Tabs with Proper Breathing Room */}
          <nav className="hidden xl:flex items-center gap-1.5 p-1 bg-surface-container-low/90 backdrop-blur-md rounded-xl border border-surface-container-high/60 shadow-sm">
            {TOP_TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive =
                activePage === tab.id ||
                (tab.id === 'recovery-plan' && activePage === 'journey-graph') ||
                (tab.id === 'notifications' && activePage === 'action-history');

              return (
                <button
                  key={tab.id}
                  onClick={() => setActivePage(tab.id)}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-lg transition-all text-xs font-semibold cursor-pointer whitespace-nowrap shrink-0 ${
                    isActive
                      ? 'text-on-primary-container bg-primary-container shadow-sm'
                      : 'text-on-surface-variant hover:bg-surface-container-high/70 hover:text-on-surface'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-on-primary-container' : 'text-on-surface-variant'}`} />
                  <span>{tab.label}</span>
                  {tab.badge && (
                    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[9px] uppercase font-bold tracking-wider ml-1 ${
                      isActive
                        ? 'bg-surface-container-lowest text-primary-container'
                        : 'bg-surface-container-high text-primary-fixed-dim'
                    }`}>
                      <span className="w-1.5 h-1.5 rounded-full bg-primary-container animate-pulse" />
                      {tab.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* Right Status Controls with Clear Gaps */}
          <div className="flex items-center gap-2.5 sm:gap-3 shrink-0">
            {/* Quick Traveler Profile Button */}
            <button
              onClick={() => setShowAuthModal(true)}
              className="w-9 h-9 rounded-full bg-gradient-to-tr from-primary to-primary-container flex items-center justify-center shadow-sm p-0.5 ring-1 ring-primary/40 cursor-pointer hover:scale-105 transition-transform"
              title="View Traveler Credentials or Switch Profile"
            >
              <div className="w-full h-full rounded-full bg-surface-container-lowest flex items-center justify-center">
                <User className="w-4 h-4 text-primary" />
              </div>
            </button>

            {/* Refresh Sync Button */}
            {onRefresh && (
              <button
                onClick={onRefresh}
                disabled={loading}
                title="Sync Live Radar & Graph"
                className="w-9 h-9 rounded-lg bg-surface-container-high hover:bg-surface-container-highest text-primary border border-primary/20 hover:border-primary/50 transition flex items-center justify-center cursor-pointer shadow-sm"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-primary-container' : ''}`} />
              </button>
            )}

            {/* Mobile Hamburger Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="xl:hidden w-9 h-9 rounded-lg bg-surface-container-high text-on-surface-variant hover:text-on-surface border border-surface-container-high flex items-center justify-center cursor-pointer"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Mobile Animated Dropdown Drawer */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
              className="xl:hidden border-t border-surface-container-high/50 bg-surface-container-lowest/95 backdrop-blur-2xl overflow-hidden max-h-[calc(100vh-4rem)] overflow-y-auto px-4 py-3 space-y-1.5"
            >
              {TOP_TABS.map((tab) => {
                const Icon = tab.icon;
                const isActive = activePage === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => {
                      setActivePage(tab.id);
                      setMobileMenuOpen(false);
                    }}
                    className={`w-full px-3.5 py-2.5 rounded-xl text-xs font-medium flex items-center justify-between transition cursor-pointer ${
                      isActive
                        ? 'bg-primary-container text-on-primary-container font-semibold shadow-md'
                        : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/50'
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className="w-4 h-4" />
                      <span>{tab.label}</span>
                    </div>
                    {tab.badge && (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-surface-container text-primary-container border border-primary/20">
                        {tab.badge}
                      </span>
                    )}
                  </button>
                );
              })}

              <div className="pt-2 mt-2 border-t border-surface-container-high/40 flex items-center justify-between text-xs text-on-surface-variant px-2">
                <span className="font-mono text-[11px]">User: {user?.email || 'traveler@example.com'}</span>
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    setShowAuthModal(true);
                  }}
                  className="text-primary hover:underline flex items-center gap-1 font-semibold"
                >
                  <LogIn className="w-3.5 h-3.5" /> Sign In Screen
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      {/* Main Content View */}
      <main
        style={{ paddingTop: 'calc(var(--header-height, 64px) + 24px)' }}
        className="flex-1 w-full pb-10 bg-transparent"
      >
        <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 space-y-6 sm:space-y-8">
          <ErrorAlertBanner error={error} onRetry={onRefresh} />

          <AnimatePresence mode="wait">
            <motion.div
              key={activePage}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            >
              {/* PRIMARY TAB: FLIGHT INTELLIGENCE & UNIFIED AGENT */}
              {activePage === 'intelligence' && <AeroAIFlightIntelligenceView />}

              {/* TAB 1: MY JOURNEY (Primary Clean Workspace) */}
              {activePage === 'guided' && (
                <SimpleGuidedStoryMode
                  onSync={() => {
                    if (onRefresh) onRefresh();
                  }}
                  onRunBackendE2E={() => {
                    fetchActionHistory();
                    if (onRefresh) onRefresh();
                    addToast(
                      'Trip Recovered',
                      'Updated missed connections and generated notifications.',
                      'success'
                    );
                  }}
                  onOpenAdvancedPage={(pageId) => setActivePage(pageId)}
                />
              )}

              {/* TAB 2: EMAIL PARSER */}
              {activePage === 'inbox' && (
                <InboxView
                  inboxEmails={inboxEmails}
                  sampleEmails={sampleEmails}
                  onForwardEmail={async (payload) => {
                    await onForwardEmail(payload);
                    addToast(
                      'Booking Email Parsed',
                      'Added booking to your journey.',
                      'success'
                    );
                  }}
                  forwardingLoading={forwardingLoading}
                />
              )}

              {/* TAB 3: AI OPTIMIZER & GRAPH */}
              {(activePage === 'recovery-plan' || activePage === 'journey-graph') && (
                <div className="space-y-6">
                  {/* Segmented Viewport Switcher */}
                  <div className="inline-flex items-center flex-wrap p-1.5 rounded-2xl bg-surface-container-low/90 backdrop-blur-xl border border-surface-container-high shadow-xl gap-2 shrink-0">
                    <button
                      onClick={() => setOptimizerSubTab('graph')}
                      className={`px-4 py-2 rounded-xl text-xs sm:text-sm transition-all cursor-pointer ${
                        optimizerSubTab === 'graph'
                          ? 'bg-surface-container-high text-primary-container shadow-md border border-primary/20 font-bold'
                          : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/50 font-medium'
                      }`}
                    >
                      NetworkX Journey Graph
                    </button>
                    <button
                      onClick={() => setOptimizerSubTab('suppliers')}
                      className={`px-4 py-2 rounded-xl text-xs sm:text-sm transition-all cursor-pointer ${
                        optimizerSubTab === 'suppliers'
                          ? 'bg-surface-container-high text-primary-container shadow-md border border-primary/20 font-bold'
                          : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/50 font-medium'
                      }`}
                    >
                      Mock Supplier Inventory
                    </button>
                  </div>

                  {optimizerSubTab === 'graph' && (
                    <JourneyGraphView
                      journey={currentJourney}
                      graphData={graphData}
                      loading={loading}
                      onRefreshGraph={onRefreshGraph}
                    />
                  )}
                  {optimizerSubTab === 'suppliers' && <SupplierEcosystemView />}
                </div>
              )}

              {/* TAB 4: SENT EMAILS & LOGS */}
              {(activePage === 'notifications' || activePage === 'action-history') && (
                <div className="space-y-6">
                  {/* Segmented Viewport Switcher */}
                  <div className="inline-flex items-center flex-wrap p-1.5 rounded-2xl bg-surface-container-low/90 backdrop-blur-xl border border-surface-container-high shadow-xl gap-2 shrink-0">
                    <button
                      onClick={() => setLogsSubTab('emails')}
                      className={`px-4 py-2 rounded-xl text-xs sm:text-sm transition-all cursor-pointer ${
                        logsSubTab === 'emails'
                          ? 'bg-surface-container-high text-primary-container shadow-md border border-primary/20 font-bold'
                          : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/50 font-medium'
                      }`}
                    >
                      Sent Emails
                    </button>
                    <button
                      onClick={() => setLogsSubTab('audit')}
                      className={`px-4 py-2 rounded-xl text-xs sm:text-sm transition-all cursor-pointer ${
                        logsSubTab === 'audit'
                          ? 'bg-surface-container-high text-primary-container shadow-md border border-primary/20 font-bold'
                          : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/50 font-medium'
                      }`}
                    >
                      Action Execution Audit Log
                    </button>
                  </div>

                  {logsSubTab === 'emails' ? <NotificationInboxView /> : <ActionExecutionView />}
                </div>
              )}

              {/* TAB 5: POLICY CHATBOT */}
              {activePage === 'chatbot' && (
                <div className="w-full max-w-5xl mx-auto">
                  <PolicyAssistantChat
                    activeJourneyContext={
                      currentJourney
                        ? {
                            journey_id: currentJourney.id,
                            airline: 'Air India',
                            flight_number: 'AI-202',
                            origin: 'Mumbai',
                            destination: 'Delhi',
                            delay_minutes: 240,
                          }
                        : null
                    }
                  />
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>

      {/* Floating Chatbot Beacon Button */}
      {activePage !== 'chatbot' && (
        <motion.button
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          whileHover={{ scale: 1.05, y: -2 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setActivePage('chatbot')}
          className="fixed bottom-6 right-6 z-40 bg-gradient-to-r from-primary-container to-primary-fixed-dim text-on-primary px-4 py-3 rounded-full shadow-[0_0_25px_rgba(0,229,255,0.4)] flex items-center gap-2.5 border border-primary/30 cursor-pointer group hover:brightness-110 transition-all"
          title="Open Airline Policy & Legal Rights AI"
        >
          <div className="relative">
            <Bot className="w-5 h-5 text-on-primary group-hover:rotate-12 transition-transform duration-300" />
            <span className="w-2 h-2 rounded-full bg-primary-container absolute -top-0.5 -right-0.5 shadow-[0_0_8px_rgba(0,229,255,0.9)] animate-ping" />
            <span className="w-2 h-2 rounded-full bg-primary-container absolute -top-0.5 -right-0.5" />
          </div>
          <span className="text-xs font-bold tracking-wide font-headline-md">Ask Policy AI</span>
        </motion.button>
      )}

      {/* Footer matching Google Stitch Reference */}
      <footer className={`w-full bg-surface-container-lowest border-t border-surface-container-high/40 py-6 ${activePage === 'chatbot' ? 'mt-6 sm:mt-8' : 'mt-16'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-col md:flex-row items-center justify-between gap-4 text-outline font-body-sm text-body-sm">
          <div>© 2025 AeroAI Avionics & Flight Recovery Intelligence. All rights reserved.</div>
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-2 text-on-surface-variant font-mono text-xs px-3 py-1 rounded-full bg-surface-container border border-surface-container-high">
              <span className="w-2 h-2 rounded-full bg-primary-container animate-ping" />
              OPS Telemetry Engine: Online (Latency 14ms)
            </span>
          </div>
        </div>
      </footer>

      {/* Modal for LoginPage */}
      <AnimatePresence>
        {showAuthModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-surface-container-lowest/80 backdrop-blur-md overflow-y-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.25 }}
              className="relative w-full max-w-5xl my-8 bg-surface-container-low border border-surface-container-high rounded-2xl shadow-2xl overflow-hidden"
            >
              <button
                onClick={() => setShowAuthModal(false)}
                className="absolute top-4 right-4 z-50 p-2 rounded-xl bg-surface-container-high text-on-surface-variant hover:text-on-surface border border-surface-container-high transition cursor-pointer"
                title="Close"
              >
                <X className="w-5 h-5" />
              </button>

              <LoginPage
                currentUser={user}
                onLogin={async (email, password) => {
                  if (onRefresh) await onRefresh();
                  setShowAuthModal(false);
                  addToast('Authenticated', `Signed in as ${email}`, 'success');
                }}
                onContinueAsCurrent={() => {
                  setShowAuthModal(false);
                }}
              />
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
