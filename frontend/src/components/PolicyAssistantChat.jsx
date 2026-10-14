import React, { useState, useEffect, useRef } from 'react';
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
    <div className={`flex flex-col h-[700px] rounded-2xl border border-slate-800 bg-slate-900/90 shadow-2xl overflow-hidden backdrop-blur ${embeddedMode ? 'h-full border-0' : ''}`}>
      {/* Top Header */}
      <div className="p-4 border-b border-slate-800 bg-slate-950/70 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-white tracking-tight">
                Airline Policy & Passenger Rights Assistant
              </h2>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" /> Fact-Grounded RAG
              </span>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-sky-500/15 text-sky-300 border border-sky-500/30 flex items-center gap-1">
                <Sparkles className="w-3 h-3" /> FAISS Semantic Search
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Powered by FAISS vector similarity over DGCA CAR M Part IV, EU261, US DOT & Airline Policies
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleClearChat}
            className="p-1.5 text-slate-400 hover:text-rose-300 hover:bg-rose-950/40 rounded-lg transition border border-transparent hover:border-rose-800/60 cursor-pointer"
            title="Clear Chat History"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Active Journey Personalization Alert */}
      {activeJourneyContext && (
        <div className="px-4 py-2.5 bg-indigo-950/40 border-b border-indigo-900/60 text-xs text-indigo-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Plane className="w-4 h-4 text-indigo-400" />
            <span>
              <strong>Personalized Context Active:</strong> Monitored Flight{' '}
              <span className="underline font-semibold">{activeJourneyContext.airline || 'Air India'} {activeJourneyContext.flight_number || 'AI-202'}</span>{' '}
              ({activeJourneyContext.origin || 'BOM'} &rarr; {activeJourneyContext.destination || 'DEL'})
              {activeJourneyContext.delay_minutes > 0 && (
                <span className="ml-1 text-amber-300 font-semibold">
                  &bull; Delayed {activeJourneyContext.delay_minutes}m
                </span>
              )}
            </span>
          </div>
          <span className="text-[10px] bg-indigo-900/80 px-2 py-0.5 rounded border border-indigo-700 text-indigo-300 font-medium">
            Auto-Detected: DGCA CAR M
          </span>
        </div>
      )}

      {/* Message List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 max-w-3xl ${
              msg.role === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
            }`}
          >
            {/* Avatar */}
            <div
              className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 border ${
                msg.role === 'user'
                  ? 'bg-sky-600 text-white border-sky-500'
                  : 'bg-indigo-950 text-indigo-300 border-indigo-700/60'
              }`}
            >
              {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            {/* Bubble Content */}
            <div className={`space-y-2 max-w-[85%] ${msg.role === 'user' ? 'text-right' : ''}`}>
              <div
                className={`p-3.5 rounded-2xl text-xs leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-sky-600 text-white shadow-md rounded-tr-none text-left'
                    : 'bg-slate-950 border border-slate-800 text-slate-200 shadow-md rounded-tl-none text-left'
                }`}
              >
                {/* Message text with basic markdown formatting */}
                <div className="whitespace-pre-wrap space-y-2">
                  {msg.content.split('\n\n').map((paragraph, pIdx) => (
                    <p key={pIdx}>
                      {paragraph.split('**').map((seg, sIdx) =>
                        sIdx % 2 === 1 ? <strong key={sIdx} className="font-bold text-sky-200">{seg}</strong> : seg
                      )}
                    </p>
                  ))}
                </div>
              </div>

              {/* Citations Container */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="pt-1.5 space-y-1.5 text-left">
                  <div className="text-[10px] font-semibold text-slate-400 flex items-center gap-1">
                    <FileText className="w-3 h-3 text-indigo-400" />
                    <span>Official Document Citations:</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {msg.citations.map((cite, cIdx) => (
                      <a
                        key={cIdx}
                        href={cite.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-1 rounded-lg bg-slate-950 hover:bg-indigo-950/60 border border-slate-800 hover:border-indigo-700 text-indigo-300 hover:text-indigo-200 transition cursor-pointer group"
                        title={`Open official document: ${cite.document_title} (${cite.section})`}
                      >
                        <span className="font-semibold">{cite.regulator || cite.region}:</span>
                        <span className="truncate max-w-[200px]">{cite.document_title}</span>
                        <ExternalLink className="w-2.5 h-2.5 text-slate-500 group-hover:text-indigo-300 shrink-0" />
                      </a>
                    ))}
                  </div>
                </div>
              )}

              <div className="text-[10px] text-slate-500 px-1">
                {msg.timestamp}
              </div>
            </div>
          </div>
        ))}

        {/* Loading Indicator */}
        {loading && (
          <div className="flex gap-3 mr-auto max-w-lg">
            <div className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 bg-indigo-950 text-indigo-300 border border-indigo-700/60 animate-pulse">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded-tl-none flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-spin" />
              <span>Retrieving official policy clauses & synthesizing grounded answer...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Questions Chips */}
      <div className="p-2.5 border-t border-slate-800/80 bg-slate-950/50">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-slate-400 scrollbar-thin">
          <span className="text-[10px] font-semibold flex items-center gap-1 shrink-0 text-slate-500">
            <HelpCircle className="w-3 h-3" /> Quick Prompts:
          </span>
          {DEFAULT_SUGGESTIONS.map((q, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(q)}
              disabled={loading}
              className="text-[11px] whitespace-nowrap px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 hover:border-slate-700 transition cursor-pointer shrink-0 disabled:opacity-50"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Input Bar */}
      <div className="p-3 border-t border-slate-800 bg-slate-950">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about flight delays, DGCA compensation, IndiGo/Air India refunds, baggage rules..."
            disabled={loading}
            className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="p-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:hover:bg-indigo-600 text-white transition shadow cursor-pointer shrink-0"
            title="Send Query"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        <div className="mt-1.5 text-[10px] text-slate-500 text-center">
          Answers grounded exclusively in official civil aviation charters. Not legal advice.
        </div>
      </div>
    </div>
  );
}

export default PolicyAssistantChat;
