import React, { useState, useEffect, useCallback } from 'react';
import {
  Sparkles,
  Mail,
  Network,
  Bell,
  Bot,
  MessageSquare,
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
import {
  ToastViewport,
  ErrorAlertBanner,
} from './ui/SaaSPrimitives';

const TOP_TABS = [
  { id: 'guided', label: 'My Journey', icon: Sparkles },
  { id: 'inbox', label: 'Email Parser', icon: Mail },
  { id: 'recovery-plan', label: 'AI Optimizer & Graph', icon: Network },
  { id: 'notifications', label: 'Sent Emails & Logs', icon: Bell },
  { id: 'chatbot', label: 'Policy Chatbot', icon: Bot, badge: 'AI' },
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
}) {
  const [activePage, setActivePage] = useState('guided');
  const [toasts, setToasts] = useState([]);
  const [actionHistory, setActionHistory] = useState(null);
  const [runningDemo, setRunningDemo] = useState(false);
  const [optimizerSubTab, setOptimizerSubTab] = useState('optimizer');
  const [logsSubTab, setLogsSubTab] = useState('emails');

  const currentJourney = journeys[0];

  const addToast = useCallback((title, message = '', type = 'success') => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    setToasts((prev) => [...prev.slice(-3), { id, title, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <ToastViewport toasts={toasts} onDismiss={dismissToast} />

      {/* Clean, Minimal Top Navbar */}
      <header className="border-b border-slate-800/80 bg-slate-900/80 backdrop-blur sticky top-0 z-30">
        <div className="max-w-5xl mx-auto px-6 py-3.5 flex flex-wrap items-center justify-between gap-4">
          <div
            onClick={() => setActivePage('guided')}
            className="flex items-center gap-2.5 cursor-pointer"
          >
            <div className="p-2 bg-sky-500/15 border border-sky-500/30 rounded-xl text-sky-400">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <div className="font-bold text-sm text-white tracking-tight flex items-center gap-1.5">
                <span className="text-sky-400 font-extrabold tracking-wider">AeroAI</span>
                <span className="text-slate-500">|</span>
                <span>Disruption Recovery</span>
              </div>
            </div>
          </div>

          <nav className="flex flex-wrap items-center gap-1.5">
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
                  className={`px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition cursor-pointer ${
                    isActive
                      ? 'bg-sky-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/70'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                  {tab.badge && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-indigo-500/30 text-indigo-200 border border-indigo-400/30 font-bold ml-0.5">
                      {tab.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-6 space-y-6">
        <ErrorAlertBanner error={error} onRetry={onRefresh} />

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
          <div className="space-y-5">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
              <button
                onClick={() => setOptimizerSubTab('optimizer')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold cursor-pointer ${
                  optimizerSubTab === 'optimizer'
                    ? 'bg-sky-600 text-white'
                    : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
                }`}
              >
                OR-Tools Optimization Math
              </button>
              <button
                onClick={() => setOptimizerSubTab('graph')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold cursor-pointer ${
                  optimizerSubTab === 'graph'
                    ? 'bg-sky-600 text-white'
                    : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
                }`}
              >
                NetworkX Journey Graph
              </button>
              <button
                onClick={() => setOptimizerSubTab('suppliers')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold cursor-pointer ${
                  optimizerSubTab === 'suppliers'
                    ? 'bg-sky-600 text-white'
                    : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
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
          <div className="space-y-5">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
              <button
                onClick={() => setLogsSubTab('emails')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold cursor-pointer ${
                  logsSubTab === 'emails'
                    ? 'bg-sky-600 text-white'
                    : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
                }`}
              >
                Sent Emails
              </button>
              <button
                onClick={() => setLogsSubTab('audit')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold cursor-pointer ${
                  logsSubTab === 'audit'
                    ? 'bg-sky-600 text-white'
                    : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
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
      </main>

      {/* Floating Chatbot Quick Button */}
      {activePage !== 'chatbot' && (
        <button
          onClick={() => setActivePage('chatbot')}
          className="fixed bottom-6 right-6 z-40 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white px-4 py-3 rounded-full shadow-2xl flex items-center gap-2.5 transition-all hover:scale-105 border border-sky-400/30 cursor-pointer group"
          title="Open Airline Policy & Passenger Rights Legal AI Assistant"
        >
          <Bot className="w-5 h-5 text-sky-200 group-hover:rotate-12 transition-transform" />
          <span className="text-xs font-bold tracking-wide">Ask Policy AI</span>
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        </button>
      )}
    </div>
  );
}
