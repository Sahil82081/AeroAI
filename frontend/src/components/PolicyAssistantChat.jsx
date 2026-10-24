import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MessageSquare,
  Send,
  Trash2,
  ExternalLink,
  ShieldCheck,
  AlertCircle,
  Sparkles,
  Bot,
  User,
  Scale,
  Plane,
  FileText,
  HelpCircle,
  ChevronRight
} from 'lucide-react';
import { api } from '../services/api';

const DEFAULT_SUGGESTIONS = [
  'What compensation or refreshments do I get for a 4-hour delay?',
  'Can I get a 100% full refund if my flight is cancelled?',
  'What is the free baggage allowance on IndiGo vs Air India?',
  'What are my statutory rights if bumped due to overbooking?',
  'Can I correct a spelling typo in my ticket without cancellation fees?'
];

export function PolicyAssistantChat({
  activeJourneyContext = null,
  embeddedMode = false
}) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: `Hello! I am your **Airline Policy & Passenger Rights Legal Assistant**.\n\nI answer questions grounded **strictly in official civil aviation regulatory orders and airline Conditions of Carriage** (DGCA CAR Series M Part IV, EU Regulation 261/2004, US DOT 14 CFR Part 260, IndiGo & Air India carriage policies).\n\nAsk me about flight delays, mandatory compensation, cancellations, full refunds, baggage allowances, or denied boarding!`,
      citations: [
        {
          document_title: 'DGCA CAR Section 3 Series M Part IV',
          section: 'Facilities for Delays and Cancellations',
          page_number: 1,
          source_url: 'https://www.dgca.gov.in',
          region: 'India'
        },
        {
          document_title: 'EU Regulation 261/2004 (EUR-Lex)',
          section: 'Statutory Delay Compensation',
          page_number: 1,
          source_url: 'https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32004R0261',
          region: 'European Union'
        }
      ],
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(() => `sess-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (messageText = null) => {
    const textToSend = (messageText || input).trim();
    if (!textToSend || loading) return;

    setError(null);
    const userMsgId = `user-${Date.now()}`;
    const userTimestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    setMessages((prev) => [
      ...prev,
      {
        id: userMsgId,
        role: 'user',
        content: textToSend,
        timestamp: userTimestamp
      }
    ]);

    setInput('');
    setLoading(true);

    try {
      const payload = {
        message: textToSend,
        session_id: sessionId,
      };

      if (activeJourneyContext) {
        if (activeJourneyContext.airline) payload.airline = activeJourneyContext.airline;
        if (activeJourneyContext.journey_id) payload.journey_id = activeJourneyContext.journey_id;
      }

      const res = await api.sendChatMessage(payload);

      const assistantMsg = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: res.answer,
        citations: res.citations || [],
        confidence: res.confidence,
        journey_context: res.journey_context,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error('Policy chat error:', err);
      setError(err?.response?.data?.detail || err?.message || 'Failed to generate grounded answer.');
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: '⚠️ I encountered a temporary communication issue while consulting the policy database. Please verify your query or retry.',
          citations: [],
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        role: 'assistant',
        content: 'Conversation history cleared. How can I assist you with airline policies or passenger rights today?',
        citations: [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
    setSessionId(`sess-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`);
    setError(null);
  };

  return (
    <div className={`flex flex-col h-[calc(100vh-14rem)] min-h-[620px] max-h-[820px] rounded-2xl border border-surface-container-high/80 bg-surface-container-low/95 shadow-2xl backdrop-blur-2xl overflow-hidden relative ${embeddedMode ? 'h-full border-0' : ''}`}>
      {/* Top subtle border glow line */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-indigo-500/40 to-transparent pointer-events-none z-10" />

      {/* Top Header */}
      <div className="px-4 py-3.5 sm:px-6 sm:py-4 border-b border-surface-container-high bg-surface-container-low/95 flex items-center justify-between gap-3 backdrop-blur-md">
        <div className="flex items-center gap-3 sm:gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-300 border border-indigo-400/30 shadow-[0_0_15px_rgba(99,102,241,0.2)] flex items-center justify-center shrink-0">
            <Scale className="w-5 h-5 text-indigo-300" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-sm sm:text-base font-bold text-white tracking-tight font-display">
                Airline Policy & Passenger Rights Legal AI
              </h2>
              <span className="text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 flex items-center gap-1.5 shadow-sm">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]" />
                Fact-Grounded RAG
              </span>
              <span className="text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-sky-500/15 text-sky-300 border border-sky-500/30 flex items-center gap-1.5 shadow-sm hidden sm:inline-flex">
                <Sparkles className="w-3 h-3 text-sky-400" /> FAISS Vector Index
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1 font-sans">
              DGCA CAR Series M Part IV &bull; EU Regulation 261/2004 &bull; US DOT 14 CFR Part 260
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleClearChat}
            className="h-9 w-9 rounded-xl text-slate-400 hover:text-rose-300 hover:bg-rose-950/40 border border-surface-container-high hover:border-rose-500/40 transition flex items-center justify-center cursor-pointer shadow-sm"
            title="Clear Chat History"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Active Journey Personalization Alert */}
      {activeJourneyContext && (
        <div className="px-4 sm:px-6 py-2.5 bg-indigo-950/40 border-b border-indigo-500/25 text-xs sm:text-[13px] text-indigo-100 flex items-center justify-between gap-3 backdrop-blur-md">
          <div className="flex items-center gap-2 min-w-0">
            <Plane className="w-4 h-4 text-indigo-300 shrink-0" />
            <span className="truncate">
              <strong className="text-indigo-200">Personalized Context:</strong> Flight{' '}
              <span className="font-semibold text-white">{activeJourneyContext.airline || 'Air India'} {activeJourneyContext.flight_number || 'AI-202'}</span>{' '}
              <span className="text-indigo-200">({activeJourneyContext.origin || 'BOM'} &rarr; {activeJourneyContext.destination || 'DEL'})</span>
              {activeJourneyContext.delay_minutes > 0 && (
                <span className="ml-1.5 text-amber-300 font-semibold font-mono">
                  &bull; +{activeJourneyContext.delay_minutes}m Delay
                </span>
              )}
            </span>
          </div>
          <span className="text-[11px] font-mono bg-indigo-900/80 px-2.5 py-1 rounded-md border border-indigo-600/50 text-indigo-200 font-semibold shrink-0 shadow-sm">
            DGCA CAR M Active
          </span>
        </div>
      )}

      {/* Message List */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5 sm:space-y-6">
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 12, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
              className={`flex gap-3 sm:gap-3.5 max-w-4xl ${
                msg.role === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
              }`}
            >
              {/* Avatar */}
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border shadow-md ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-br from-sky-600 to-indigo-600 text-white border-sky-400/50 shadow-sky-950/50'
                    : 'bg-surface-container-high text-indigo-300 border-indigo-400/30 shadow-[0_0_12px_rgba(99,102,241,0.2)]'
                }`}
              >
                {msg.role === 'user' ? <User className="w-4.5 h-4.5" /> : <Bot className="w-4.5 h-4.5" />}
              </div>

              {/* Bubble Content */}
              <div className={`space-y-2 max-w-[88%] sm:max-w-[82%] ${msg.role === 'user' ? 'text-right' : ''}`}>
                <div
                  className={`p-4 sm:p-5 rounded-2xl text-[13.5px] sm:text-[14.5px] leading-relaxed shadow-lg ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-r from-sky-600 to-indigo-600 text-white rounded-tr-sm text-left shadow-[0_4px_20px_rgba(14,165,233,0.25)] font-sans'
                      : 'bg-[#182030] border border-surface-container-high text-slate-100 rounded-tl-sm text-left backdrop-blur-md shadow-glass-card font-sans'
                  }`}
                >
                  {/* Message text with clear markdown formatting and comfortable spacing */}
                  <div className="whitespace-pre-wrap space-y-2.5">
                    {msg.content.split('\n\n').map((paragraph, pIdx) => (
                      <p key={pIdx}>
                        {paragraph.split('**').map((seg, sIdx) =>
                          sIdx % 2 === 1 ? <strong key={sIdx} className="font-bold text-sky-300">{seg}</strong> : seg
                        )}
                      </p>
                    ))}
                  </div>
                </div>

                {/* Citations Container */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="pt-1.5 space-y-1.5 text-left">
                    <div className="text-[11px] font-mono font-semibold text-slate-300 flex items-center gap-1.5 uppercase tracking-wider">
                      <FileText className="w-3.5 h-3.5 text-indigo-400" />
                      <span>Official Regulatory Citations:</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {msg.citations.map((cite, cIdx) => (
                        <a
                          key={cIdx}
                          href={cite.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 text-xs font-mono px-3 py-1.5 rounded-lg bg-surface-container-high/90 hover:bg-indigo-950/70 border border-surface-container-high hover:border-sky-400/40 text-indigo-200 hover:text-white transition cursor-pointer group shadow-sm"
                          title={`Open official document: ${cite.document_title} (${cite.section})`}
                        >
                          <span className="font-bold text-sky-400">{cite.regulator || cite.region}:</span>
                          <span className="truncate max-w-[220px] text-slate-200 group-hover:text-white">{cite.document_title}</span>
                          <ExternalLink className="w-3 h-3 text-slate-400 group-hover:text-sky-300 shrink-0" />
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                <div className="text-[11px] text-slate-400 font-mono px-1">
                  {msg.timestamp}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Loading Indicator with Animated 3 Bouncing Dots */}
        {loading && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-3 sm:gap-3.5 mr-auto max-w-lg"
          >
            <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 bg-surface-container-high text-indigo-300 border border-indigo-500/40 shadow-sm">
              <Bot className="w-4.5 h-4.5" />
            </div>
            <div className="p-3.5 sm:p-4 rounded-2xl bg-[#182030] border border-surface-container-high text-xs sm:text-sm text-slate-200 rounded-tl-sm flex items-center gap-3 backdrop-blur-md shadow-md">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full bg-sky-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span className="text-xs text-slate-300 font-mono">Consulting DGCA CAR &amp; Airline Conditions of Carriage...</span>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Questions Chips */}
      <div className="px-4 py-3 sm:px-5 sm:py-3.5 border-t border-surface-container-high/70 bg-surface-container-low/70 backdrop-blur-md">
        <div className="flex items-center gap-2 sm:gap-2.5 overflow-x-auto pb-1 text-slate-300 scrollbar-thin">
          <span className="text-xs font-mono font-bold flex items-center gap-1.5 shrink-0 text-sky-400 uppercase tracking-wider bg-sky-500/10 px-2.5 py-1.5 rounded-lg border border-sky-400/25">
            <HelpCircle className="w-3.5 h-3.5 text-sky-400" /> Prompts:
          </span>
          {DEFAULT_SUGGESTIONS.map((q, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(q)}
              disabled={loading}
              className="text-xs sm:text-[13px] whitespace-nowrap px-3.5 py-2 rounded-xl bg-surface-container-high/90 hover:bg-surface-container-highest text-slate-200 hover:text-white border border-surface-container-high hover:border-sky-400/50 transition-all cursor-pointer shrink-0 disabled:opacity-50 h-9 flex items-center shadow-sm hover:scale-[1.01] active:scale-[0.99]"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Input Bar */}
      <div className="p-3.5 sm:p-4 border-t border-surface-container-high/80 bg-surface-container-lowest/90 backdrop-blur-md">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2.5 sm:gap-3"
        >
          <div className="relative flex-1 min-w-0">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about flight delay compensation, DGCA refunds, IndiGo/Air India carriage rules..."
              disabled={loading}
              className="w-full bg-surface-container-low/90 border border-surface-container-high rounded-xl px-4 py-3 text-xs sm:text-sm text-slate-100 placeholder:text-slate-400 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-400/40 transition font-sans h-12 shadow-inner"
            />
          </div>
          <motion.button
            type="submit"
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.96 }}
            disabled={!input.trim() || loading}
            className="h-12 w-12 rounded-xl bg-gradient-to-r from-sky-500 via-sky-600 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 disabled:opacity-40 disabled:hover:from-sky-500 text-white transition shadow-[0_0_15px_rgba(14,165,233,0.3)] cursor-pointer shrink-0 flex items-center justify-center"
            title="Send Query"
          >
            <Send className="w-5 h-5 text-white" />
          </motion.button>
        </form>
        <div className="mt-2 text-[11px] sm:text-xs text-slate-400 text-center font-mono">
          Answers grounded strictly in official civil aviation charters &bull; Zero hallucination guardrails
        </div>
      </div>
    </div>
  );
}

export default PolicyAssistantChat;
