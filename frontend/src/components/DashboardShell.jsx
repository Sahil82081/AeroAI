import React, { useState, useEffect, useCallback } from 'react';
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
  ChevronRight
} from 'lucide-react';
import { api } from '../services/api';
import { InboxView } from './InboxView';
import { JourneyGraphView } from './JourneyGraphView';
import { SupplierEcosystemView } from './SupplierEcosystemView';
import { ActionExecutionView } from './ActionExecutionView';
import { NotificationInboxView } from './NotificationInboxView';
import { RecoveryPlanPage } from './pages/RecoveryPlanPage';
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
  { id: 'intelligence', label: 'Flight Intelligence', icon: Bot, badge: 'Live AI' },
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
  const [optimizerSubTab, setOptimizerSubTab] = useState('optimizer');
  const [logsSubTab, setLogsSubTab] = useState('emails');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);

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
        'Recovery Actions Executed ✓',
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
    <div className="min-h-screen bg-[#030712] text-slate-100 flex flex-col font-sans relative selection:bg-sky-500/30 selection:text-sky-200">
      <ToastViewport toasts={toasts} onDismiss={dismissToast} />

      {/* Top Mission Control Sticky Bar */}
      <header className="border-b border-white/[0.08] bg-[#030712]/80 backdrop-blur-xl sticky top-0 z-40 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-4">
          
          {/* Brand Logo & Telemetry Indicator */}
          <div
            onClick={() => setActivePage('intelligence')}
            className="flex items-center gap-3 cursor-pointer group shrink-0"
          >
            <div className="relative">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-500/20 via-sky-600/10 to-indigo-500/20 border border-sky-400/30 flex items-center justify-center text-sky-400 shadow-inner group-hover:scale-105 group-hover:border-sky-400/60 transition-all duration-300">
                <Sparkles className="w-4 h-4 text-sky-300 group-hover:rotate-12 transition-transform duration-300" />
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-400 border-2 border-[#030712] shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
            </div>

            <div>
              <div className="font-display font-extrabold text-base tracking-tight flex items-center gap-2">
                <span className="bg-gradient-to-r from-white via-sky-200 to-sky-400 bg-clip-text text-transparent">
                  AeroAI
                </span>
                <span className="text-white/20 font-normal">/</span>
                <span className="text-xs font-mono font-medium text-slate-400 hidden sm:inline tracking-wider uppercase">
                  Mission Control
                </span>
              </div>
            </div>
          </div>

          {/* Center Tabs with Animated Sliding Pill */}
          <nav className="hidden lg:flex items-center gap-1 p-1 rounded-2xl bg-[#070b16]/90 border border-white/[0.08] backdrop-blur-md relative shadow-inner">
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
                  className={`relative px-3.5 py-1.5 rounded-xl text-xs font-medium flex items-center gap-2 transition-all duration-200 cursor-pointer z-10 ${
                    isActive ? 'text-white font-semibold' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {isActive && (
                    <motion.div
                      layoutId="activeTabPill"
                      className="absolute inset-0 rounded-xl bg-gradient-to-r from-sky-600/90 to-indigo-600/90 border border-sky-400/40 shadow-[0_0_20px_rgba(14,165,233,0.35)] -z-10"
                      transition={{ type: 'spring', stiffness: 450, damping: 35 }}
                    />
                  )}
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-sky-200' : 'text-slate-400'}`} />
                  <span>{tab.label}</span>
                  {tab.badge && (
                    <span className="relative flex items-center ml-0.5">
                      <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-sky-400 opacity-75" />
                      <span className="relative inline-flex rounded-full text-[9px] font-mono px-1.5 py-0.2 bg-sky-400/20 text-sky-300 border border-sky-400/40 font-bold uppercase tracking-wider">
                        {tab.badge}
                      </span>
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* Right Status & Mobile Toggle */}
          <div className="flex items-center gap-2.5">
            {/* System Telemetry Pill */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-xl bg-[#070b16] border border-white/[0.08] text-[11px] font-mono text-slate-400">
              <span className={`w-2 h-2 rounded-full ${health?.status === 'offline' ? 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]' : 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]'}`} />
              <span className="text-slate-300 font-medium">SYS: OK</span>
            </div>

            {/* Quick Traveler Profile / Switcher button */}
            <button
              onClick={() => setShowAuthModal(true)}
              className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-white border border-white/[0.08] text-xs transition cursor-pointer"
              title="View Traveler Credentials or Switch Profile"
            >
              <User className="w-3.5 h-3.5 text-sky-400" />
              <span className="truncate max-w-[100px]">{user?.full_name || 'Aarav Sharma'}</span>
            </button>

            {/* Refresh Sync Button */}
            {onRefresh && (
              <button
                onClick={onRefresh}
                disabled={loading}
                title="Sync Live Radar & Graph"
                className="p-2 rounded-xl bg-[#070b16] hover:bg-slate-800 text-slate-400 hover:text-sky-300 border border-white/[0.08] transition cursor-pointer"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-sky-400' : ''}`} />
              </button>
            )}

            {/* Mobile Hamburger Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-xl bg-[#070b16] text-slate-400 hover:text-white border border-white/[0.08] cursor-pointer"
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
              className="lg:hidden border-t border-white/[0.08] bg-[#070b16]/95 backdrop-blur-2xl overflow-hidden px-4 py-3 space-y-1"
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
                    className={`w-full px-3 py-2.5 rounded-xl text-xs font-medium flex items-center justify-between transition cursor-pointer ${
                      isActive
                        ? 'bg-gradient-to-r from-sky-600 to-indigo-600 text-white font-semibold shadow-md'
                        : 'text-slate-400 hover:text-white hover:bg-white/[0.05]'
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className="w-4 h-4" />
                      <span>{tab.label}</span>
                    </div>
                    {tab.badge && (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-sky-400/20 text-sky-200 border border-sky-400/30">
                        {tab.badge}
                      </span>
                    )}
                  </button>
                );
              })}

              <div className="pt-2 mt-2 border-t border-white/[0.08] flex items-center justify-between text-xs text-slate-400 px-2">
                <span className="font-mono text-[11px]">User: {user?.email || 'traveler@example.com'}</span>
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    setShowAuthModal(true);
                  }}
                  className="text-sky-400 hover:underline flex items-center gap-1 font-semibold"
                >
                  <LogIn className="w-3.5 h-3.5" /> Sign In Screen
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      {/* Main Content View with Animated Tab Fade/Slide Transitions */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        <ErrorAlertBanner error={error} onRetry={onRefresh} />

        <AnimatePresence mode="wait">
          <motion.div
            key={activePage}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
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
                    'Trip Recovered ✓',
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
                    'Booking Email Parsed ✓',
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
                <div className="flex flex-wrap items-center gap-2 p-1 rounded-2xl bg-[#070b16]/75 border border-white/[0.08] backdrop-blur-md w-fit">
                  <button
                    onClick={() => setOptimizerSubTab('optimizer')}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold transition cursor-pointer ${
                      optimizerSubTab === 'optimizer'
                        ? 'bg-gradient-to-r from-sky-600 to-indigo-600 text-white shadow-[0_0_15px_rgba(14,165,233,0.3)]'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    OR-Tools Optimization Math
                  </button>
                  <button
                    onClick={() => setOptimizerSubTab('graph')}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold transition cursor-pointer ${
                      optimizerSubTab === 'graph'
                        ? 'bg-gradient-to-r from-sky-600 to-indigo-600 text-white shadow-[0_0_15px_rgba(14,165,233,0.3)]'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    NetworkX Journey Graph
                  </button>
                  <button
                    onClick={() => setOptimizerSubTab('suppliers')}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold transition cursor-pointer ${
                      optimizerSubTab === 'suppliers'
                        ? 'bg-gradient-to-r from-sky-600 to-indigo-600 text-white shadow-[0_0_15px_rgba(14,165,233,0.3)]'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Mock Supplier Inventory
                  </button>
                </div>

                {optimizerSubTab === 'optimizer' && (
                  <RecoveryPlanPage
                    onExecuteRecoveryActions={handleExecuteRecoveryPlanActions}
                    executingActions={runningDemo}
                    actionExecutionResult={actionHistory}
                  />
                )}
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
                <div className="flex flex-wrap items-center gap-2 p-1 rounded-2xl bg-[#070b16]/75 border border-white/[0.08] backdrop-blur-md w-fit">
                  <button
                    onClick={() => setLogsSubTab('emails')}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold transition cursor-pointer ${
                      logsSubTab === 'emails'
                        ? 'bg-gradient-to-r from-sky-600 to-indigo-600 text-white shadow-[0_0_15px_rgba(14,165,233,0.3)]'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Sent Emails
                  </button>
                  <button
                    onClick={() => setLogsSubTab('audit')}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold transition cursor-pointer ${
                      logsSubTab === 'audit'
                        ? 'bg-gradient-to-r from-sky-600 to-indigo-600 text-white shadow-[0_0_15px_rgba(14,165,233,0.3)]'
                        : 'text-slate-400 hover:text-white'
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
              <div className="space-y-4">
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
      </main>

      {/* Floating Chatbot Beacon Button */}
      {activePage !== 'chatbot' && (
        <motion.button
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          whileHover={{ scale: 1.05, y: -2 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setActivePage('chatbot')}
          className="fixed bottom-6 right-6 z-40 bg-gradient-to-r from-sky-600 via-sky-500 to-indigo-600 text-white px-4 py-3 rounded-full shadow-[0_12px_32px_rgba(14,165,233,0.4)] flex items-center gap-2.5 border border-sky-300/40 cursor-pointer group"
          title="Open Airline Policy & Legal Rights AI"
        >
          <div className="relative">
            <Bot className="w-5 h-5 text-sky-100 group-hover:rotate-12 transition-transform duration-300" />
            <span className="w-2 h-2 rounded-full bg-emerald-400 absolute -top-0.5 -right-0.5 shadow-[0_0_8px_rgba(52,211,153,0.9)] animate-ping" />
            <span className="w-2 h-2 rounded-full bg-emerald-400 absolute -top-0.5 -right-0.5" />
          </div>
          <span className="text-xs font-bold tracking-wide font-display">Ask Policy AI</span>
        </motion.button>
      )}

      {/* Modal to view / test the Cinematic LoginPage */}
      <AnimatePresence>
        {showAuthModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#030712]/80 backdrop-blur-md overflow-y-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.25 }}
              className="relative w-full max-w-5xl my-8"
            >
              <button
                onClick={() => setShowAuthModal(false)}
                className="absolute top-4 right-4 z-50 p-2 rounded-xl bg-slate-900/90 text-slate-400 hover:text-white border border-white/10 transition cursor-pointer"
                title="Close"
              >
                <X className="w-5 h-5" />
              </button>

              <LoginPage
                currentUser={user}
                onLogin={async (email, password) => {
                  if (onRefresh) await onRefresh();
                  setShowAuthModal(false);
                  addToast('Authenticated ✓', `Signed in as ${email}`, 'success');
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

