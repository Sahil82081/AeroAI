import React, { useState } from 'react';
import { 
  Mail, 
  Send, 
  CheckCircle2, 
  AlertCircle, 
  Copy, 
  HelpCircle, 
  Plane, 
  Train, 
  Bus, 
  Hotel, 
  Ticket,
  ChevronRight,
  Code,
  Sparkles,
  ArrowUpRight,
  ShieldAlert
} from 'lucide-react';

export function InboxView({ 
  inboxEmails = [], 
  sampleEmails = [], 
  onForwardEmail, 
  forwardingLoading 
}) {
  const [selectedEmail, setSelectedEmail] = useState(inboxEmails[0] || null);
  const [selectedSample, setSelectedSample] = useState(sampleEmails[0] || null);
  const [customSender, setCustomSender] = useState('');
  const [customSubject, setCustomSubject] = useState('');
  const [customBody, setCustomBody] = useState('');
  const [parserMode, setParserMode] = useState('auto');
  const [filterStatus, setFilterStatus] = useState('ALL');

  const handleSelectSample = (sample) => {
    setSelectedSample(sample);
    setCustomSender(sample.sender);
    setCustomSubject(sample.subject);
    setCustomBody(sample.body);
  };

  const handleForward = async (e) => {
    e.preventDefault();
    if (!customSubject || !customBody) return;
    
    await onForwardEmail({
      sender: customSender || 'traveler@example.com',
      subject: customSubject,
      body: customBody,
      force_parser: parserMode
    });
  };

  const filteredInbox = inboxEmails.filter(email => {
    if (filterStatus === 'ALL') return true;
    return email.parsing_status === filterStatus;
  });

  const getStatusBadge = (status) => {
    switch (status) {
      case 'PARSED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3 h-3" /> PARSED
          </span>
        );
      case 'UNCERTAIN':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <HelpCircle className="w-3 h-3" /> UNCERTAIN
          </span>
        );
      case 'DUPLICATE':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <Copy className="w-3 h-3" /> DUPLICATE
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <AlertCircle className="w-3 h-3" /> FAILED
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-300">
            {status}
          </span>
        );
    }
  };

  const getTypeIcon = (type) => {
    switch (type?.toLowerCase()) {
      case 'flight':
        return <Plane className="w-4 h-4 text-sky-400" />;
      case 'train':
        return <Train className="w-4 h-4 text-amber-400" />;
      case 'bus':
        return <Bus className="w-4 h-4 text-emerald-400" />;
      case 'hotel':
        return <Hotel className="w-4 h-4 text-indigo-400" />;
      case 'activity':
        return <Ticket className="w-4 h-4 text-pink-400" />;
      default:
        return <Mail className="w-4 h-4 text-on-surface-variant" />;
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Section: Quick Simulation Forwarder & Sample Dataset */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        
        {/* Sample Library */}
        <div className="p-3.5 sm:p-4 rounded-xl bg-surface-container-low/90 backdrop-blur-2xl border border-surface-container-high shadow-glass-card space-y-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-sky-400" />
              <h3 className="text-xs sm:text-sm font-bold text-white font-display">Realistic Travel Dataset</h3>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/[0.06] text-on-surface-variant font-mono border border-surface-container-high">
              {sampleEmails.length} templates
            </span>
          </div>
          
          <p className="text-xs text-on-surface-variant font-sans">
            Choose an email confirmation to load into the simulated forwarder:
          </p>

          <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
            {sampleEmails.map((sample) => (
              <button
                key={sample.id}
                onClick={() => handleSelectSample(sample)}
                className={`w-full text-left p-2.5 rounded-xl border text-xs transition cursor-pointer flex items-start justify-between gap-2 backdrop-blur-xl ${
                  selectedSample?.id === sample.id
                    ? 'bg-sky-500/15 border-sky-400/50 text-white shadow-[0_0_12px_rgba(0,229,255,0.2)]'
                    : 'bg-surface-container-lowest border-surface-container-high text-slate-300 hover:border-white/20 hover:text-white'
                }`}
              >
                <div className="space-y-0.5">
                  <div className="font-semibold flex items-center gap-1.5 font-display text-xs">
                    {getTypeIcon(sample.category)}
                    <span>{sample.title}</span>
                  </div>
                  <div className="text-[10px] text-outline font-mono truncate max-w-[200px]">
                    {sample.sender}
                  </div>
                </div>

                {sample.is_imperfect && (
                  <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30 shrink-0 font-mono">
                    Imperfect
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Email Forwarding Simulator */}
        <div className="lg:col-span-2 p-3.5 sm:p-4 rounded-xl bg-surface-container-low/90 backdrop-blur-2xl border border-surface-container-high shadow-glass-card space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
            <div className="flex items-center gap-1.5">
              <Send className="w-3.5 h-3.5 text-sky-400 shrink-0" />
              <h3 className="text-xs sm:text-sm font-bold text-white font-display">Simulated Booking Email Forwarder</h3>
            </div>
            <div className="flex items-center gap-1.5 text-xs self-start sm:self-auto">
              <span className="text-on-surface-variant font-mono text-[11px]">Engine:</span>
              <select
                value={parserMode}
                onChange={(e) => setParserMode(e.target.value)}
                className="bg-surface-container-lowest border border-surface-container-high text-slate-200 text-xs rounded-lg px-2 py-1 outline-none focus:border-sky-400 font-mono h-7.5"
              >
                <option value="auto">Auto (Gemini AI + Fallback)</option>
                <option value="heuristic">Heuristic / Rule-based</option>
                <option value="gemini">Gemini LLM Extraction</option>
              </select>
            </div>
          </div>

          <form onSubmit={handleForward} className="space-y-2.5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
              <div>
                <label className="text-[10px] font-medium text-on-surface-variant block mb-1">Traveler / Sender Email</label>
                <input
                  type="text"
                  value={customSender}
                  onChange={(e) => setCustomSender(e.target.value)}
                  placeholder="e.g. reservations@airline.com"
                  className="w-full bg-surface-container-lowest border border-surface-container-high rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:border-sky-400 focus:shadow-[0_0_12px_rgba(56,189,248,0.2)] outline-none transition h-8.5"
                />
              </div>
              <div>
                <label className="text-[10px] font-medium text-on-surface-variant block mb-1">Subject Line</label>
                <input
                  type="text"
                  value={customSubject}
                  onChange={(e) => setCustomSubject(e.target.value)}
                  placeholder="e.g. Flight Confirmation - PNR 6E-IND789"
                  className="w-full bg-surface-container-lowest border border-surface-container-high rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:border-sky-400 focus:shadow-[0_0_12px_rgba(56,189,248,0.2)] outline-none transition h-8.5"
                />
              </div>
            </div>

            <div>
              <label className="text-[10px] font-medium text-on-surface-variant block mb-1">Email Body Content</label>
              <textarea
                rows={4}
                value={customBody}
                onChange={(e) => setCustomBody(e.target.value)}
                placeholder="Paste confirmation email text, e-ticket or travel forward here..."
                className="w-full bg-surface-container-lowest border border-surface-container-high rounded-lg p-2.5 text-xs text-slate-200 font-mono focus:border-sky-400 focus:shadow-[0_0_12px_rgba(56,189,248,0.2)] outline-none leading-relaxed transition"
              />
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pt-0.5">
              <span className="text-[10px] text-outline font-mono">
                Destination: <span className="text-on-surface-variant break-all">inbox@autonomous-recovery.travel</span>
              </span>
              <button
                type="submit"
                disabled={forwardingLoading || !customSubject || !customBody}
                className="w-full sm:w-auto px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 disabled:opacity-50 text-white font-semibold text-xs flex items-center justify-center gap-1.5 cursor-pointer transition shadow-[0_0_12px_rgba(0,229,255,0.25)] font-display h-8.5"
              >
                <Send className={`w-3 h-3 ${forwardingLoading ? 'animate-pulse' : ''}`} />
                <span>{forwardingLoading ? 'Ingesting & Parsing...' : 'Forward Email to System'}</span>
              </button>
            </div>
          </form>
        </div>

      </div>

      {/* Bottom Section: Ingested Inbox List & Detail Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        {/* Email List (5 cols) */}
        <div className="lg:col-span-5 p-3.5 sm:p-4 rounded-xl bg-surface-container-low/90 backdrop-blur-2xl border border-surface-container-high shadow-glass-card space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Mail className="w-3.5 h-3.5 text-sky-400" />
              <h3 className="text-xs sm:text-sm font-bold text-white font-display">Received Ingestion Inbox</h3>
            </div>
            <span className="text-[11px] text-on-surface-variant font-mono">{filteredInbox.length} messages</span>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-1 overflow-x-auto pb-1 text-[10px]">
            {['ALL', 'PARSED', 'UNCERTAIN', 'DUPLICATE', 'FAILED'].map((st) => (
              <button
                key={st}
                onClick={() => setFilterStatus(st)}
                className={`px-2.5 py-0.5 rounded-lg font-mono cursor-pointer transition ${
                  filterStatus === st 
                    ? 'bg-sky-500/20 text-sky-300 border border-sky-400/40 shadow-[0_0_8px_rgba(56,189,248,0.15)] font-bold' 
                    : 'text-on-surface-variant hover:bg-white/[0.05] border border-transparent'
                }`}
              >
                {st}
              </button>
            ))}
          </div>

          <div className="space-y-2 max-h-[440px] overflow-y-auto pr-1">
            {filteredInbox.length > 0 ? (
              filteredInbox.map((item) => (
                <div
                  key={item.id}
                  onClick={() => setSelectedEmail(item)}
                  className={`p-3 rounded-xl border text-xs cursor-pointer transition space-y-1.5 backdrop-blur-xl ${
                    selectedEmail?.id === item.id
                      ? 'bg-sky-500/15 border-sky-400/50 text-white shadow-[0_0_12px_rgba(0,229,255,0.2)]'
                      : 'bg-surface-container-lowest border-surface-container-high text-slate-300 hover:border-white/20 hover:text-white'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-1.5">
                      {getTypeIcon(item.booking_type)}
                      <span className="font-semibold text-white truncate max-w-[160px] font-display text-xs">
                        {item.subject}
                      </span>
                    </div>
                    {getStatusBadge(item.parsing_status)}
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-on-surface-variant pt-1.5 border-t border-surface-container-high/60">
                    <span className="truncate max-w-[140px] font-mono">{item.sender}</span>
                    <span className="font-mono text-sky-300">
                      Conf: {(item.confidence_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-xs text-outline italic p-6 text-center">
                No emails match current filter. Forward an email above to populate the inbox.
              </div>
            )}
          </div>
        </div>

        {/* Email Detail & JSON Inspector (7 cols) */}
        <div className="lg:col-span-7 p-3.5 sm:p-4 rounded-xl bg-surface-container-low/90 backdrop-blur-2xl border border-surface-container-high shadow-glass-card space-y-3.5">
          {selectedEmail ? (
            <>
              {/* Header */}
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2 border-b border-surface-container-high pb-3">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 text-[11px] text-on-surface-variant mb-0.5 font-mono">
                    <span>From: <strong className="text-slate-200 break-all">{selectedEmail.sender}</strong></span>
                    <span>&bull;</span>
                    <span>To: {selectedEmail.recipient}</span>
                  </div>
                  <h3 className="text-sm sm:text-base font-bold text-white tracking-tight font-display break-words">
                    {selectedEmail.subject}
                  </h3>
                </div>
                <div className="shrink-0">{getStatusBadge(selectedEmail.parsing_status)}</div>
              </div>

              {/* Extraction Metrics Row */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <div className="p-2.5 rounded-xl bg-surface-container-lowest border border-surface-container-high text-center">
                  <div className="text-[9px] uppercase font-semibold text-outline tracking-wider font-mono">Classification</div>
                  <div className="text-xs font-bold text-white mt-0.5 uppercase flex items-center justify-center gap-1 font-display">
                    {getTypeIcon(selectedEmail.booking_type)}
                    <span>{selectedEmail.booking_type || 'Unknown'}</span>
                  </div>
                </div>

                <div className="p-2.5 rounded-xl bg-surface-container-lowest border border-surface-container-high text-center">
                  <div className="text-[9px] uppercase font-semibold text-outline tracking-wider font-mono">Confidence</div>
                  <div className={`text-xs font-bold mt-0.5 font-display ${
                    selectedEmail.confidence_score >= 0.8 ? 'text-emerald-300' : 'text-amber-300'
                  }`}>
                    {(selectedEmail.confidence_score * 100).toFixed(0)}%
                  </div>
                </div>

                <div className="p-2.5 rounded-xl bg-surface-container-lowest border border-surface-container-high text-center">
                  <div className="text-[9px] uppercase font-semibold text-outline tracking-wider font-mono">Parser Engine</div>
                  <div className="text-xs font-bold text-indigo-300 mt-0.5 font-mono">
                    {selectedEmail.parser_used}
                  </div>
                </div>

                <div className="p-2.5 rounded-xl bg-surface-container-lowest border border-surface-container-high text-center">
                  <div className="text-[9px] uppercase font-semibold text-outline tracking-wider font-mono">Booking DB ID</div>
                  <div className="text-xs font-bold text-sky-400 mt-0.5 font-mono">
                    {selectedEmail.booking_id ? `#${selectedEmail.booking_id}` : 'None'}
                  </div>
                </div>
              </div>

              {/* Clarification Alert (if imperfect/uncertain) */}
              {selectedEmail.clarification_prompt && (
                <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-500/30 flex items-start gap-2.5 backdrop-blur-xl">
                  <ShieldAlert className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
                  <div className="text-xs space-y-1">
                    <span className="font-semibold text-amber-300 font-display">Action Required &middot; Clarification Prompt:</span>
                    <p className="text-slate-300 leading-relaxed font-sans text-xs">{selectedEmail.clarification_prompt}</p>
                    {selectedEmail.missing_fields && selectedEmail.missing_fields.length > 0 && (
                      <div className="pt-0.5 flex items-center gap-1 flex-wrap font-mono">
                        <span className="text-[10px] text-on-surface-variant">Missing fields:</span>
                        {selectedEmail.missing_fields.map((field) => (
                          <span key={field} className="px-1.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-[9px]">
                            {field}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Duplicate or Error Notice */}
              {selectedEmail.error_message && (
                <div className="p-3 rounded-xl bg-rose-950/30 border border-rose-500/30 text-xs text-rose-300 flex items-center gap-2 backdrop-blur-xl">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{selectedEmail.error_message}</span>
                </div>
              )}

              {/* Structured JSON Output */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs font-semibold text-on-surface-variant">
                  <span className="flex items-center gap-1.5 font-display text-[11px]">
                    <Code className="w-3 h-3 text-sky-400" />
                    Normalized JSON Booking Output
                  </span>
                  <span className="text-[9px] text-outline font-mono">Standardized Schema</span>
                </div>

                <div className="p-3 rounded-xl bg-surface-container-lowest border border-surface-container-high overflow-x-auto max-h-52 font-mono text-[11px] text-slate-300 shadow-inner">
                  <pre>{JSON.stringify(selectedEmail.parsed_data || {}, null, 2)}</pre>
                </div>
              </div>

              {/* Raw Body Drawer */}
              <details className="text-xs text-on-surface-variant">
                <summary className="cursor-pointer hover:text-white font-medium transition-colors font-display text-[11px]">
                  View Raw Ingested Email Body
                </summary>
                <div className="mt-1.5 p-3 rounded-xl bg-surface-container-lowest border border-surface-container-high text-[10px] font-mono whitespace-pre-wrap leading-relaxed text-on-surface-variant shadow-inner">
                  {selectedEmail.raw_body}
                </div>
              </details>
            </>
          ) : (
            <div className="p-8 text-center text-xs text-outline italic">
              Select an ingested email from the inbox list to inspect parsed attributes.
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
