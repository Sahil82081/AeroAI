import React, { useState } from 'react';
import { 
  Plane, 
  Train, 
  Bus, 
  Hotel, 
  Ticket, 
  ArrowRight, 
  AlertTriangle, 
  ShieldCheck, 
  Clock, 
  MapPin, 
  Layers, 
  GitFork, 
  Calendar, 
  Info,
  CheckCircle2,
  XCircle,
  AlertCircle
} from 'lucide-react';

export function JourneyGraphView({ 
  journey, 
  graphData, 
  loading, 
  onRefreshGraph 
}) {
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState(null);

  const nodes = graphData?.nodes || [];
  const edges = graphData?.edges || [];
  const riskSummary = graphData?.risk_summary;

  const getTypeIcon = (type) => {
    switch (type?.toLowerCase()) {
      case 'flight':
        return <Plane className="w-5 h-5 text-sky-400" />;
      case 'train':
        return <Train className="w-5 h-5 text-amber-400" />;
      case 'bus':
        return <Bus className="w-5 h-5 text-emerald-400" />;
      case 'hotel':
        return <Hotel className="w-5 h-5 text-indigo-400" />;
      case 'activity':
      case 'tour':
        return <Ticket className="w-5 h-5 text-pink-400" />;
      default:
        return <MapPin className="w-5 h-5 text-slate-400" />;
    }
  };

  const getRiskBadge = (risk) => {
    switch (risk) {
      case 'SAFE':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3 h-3" /> SAFE CONNECTION
          </span>
        );
      case 'TIGHT':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <AlertCircle className="w-3 h-3" /> TIGHT CONNECTION
          </span>
        );
      case 'IMPOSSIBLE':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <XCircle className="w-3 h-3" /> IMPOSSIBLE CONNECTION
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-xs text-slate-400 bg-slate-800">
            {risk || 'NONE'}
          </span>
        );
    }
  };

  const formatDateTime = (dtStr) => {
    if (!dtStr) return 'N/A';
    try {
      const d = new Date(dtStr);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' (' + d.toLocaleDateString([], { month: 'short', day: 'numeric' }) + ')';
    } catch {
      return dtStr;
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Top Banner: NetworkX Graph Topology & Risk Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        
        {/* Metric 1: Total Multi-Modal Nodes */}
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center gap-3.5">
          <div className="p-3 bg-sky-500/10 border border-sky-500/30 rounded-xl text-sky-400">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Journey Vertices</div>
            <div className="text-lg font-bold text-white mt-0.5">{nodes.length} Nodes</div>
            <div className="text-[10px] text-slate-400">NetworkX DAG Directed Graph</div>
          </div>
        </div>

        {/* Metric 2: Detected Connections */}
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center gap-3.5">
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/30 rounded-xl text-indigo-400">
            <GitFork className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Transfers &amp; Edges</div>
            <div className="text-lg font-bold text-white mt-0.5">{edges.length} Connections</div>
            <div className="text-[10px] text-slate-400">Chronological Sequence</div>
          </div>
        </div>

        {/* Metric 3: Safe Connections */}
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center gap-3.5">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Safe Buffers</div>
            <div className="text-lg font-bold text-emerald-400 mt-0.5">{riskSummary?.safe_connections || 0} Safe</div>
            <div className="text-[10px] text-slate-400">Exceeds min required buffer</div>
          </div>
        </div>

        {/* Metric 4: Tight / Impossible Risks */}
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center gap-3.5">
          <div className={`p-3 rounded-xl border ${
            (riskSummary?.impossible_connections || 0) > 0
              ? 'bg-rose-500/10 border-rose-500/30 text-rose-400'
              : (riskSummary?.tight_connections || 0) > 0
                ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                : 'bg-slate-800 text-slate-400'
          }`}>
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Connection Risk</div>
            <div className={`text-lg font-bold mt-0.5 ${
              riskSummary?.highest_risk === 'IMPOSSIBLE'
                ? 'text-rose-400'
                : riskSummary?.highest_risk === 'TIGHT'
                  ? 'text-amber-400'
                  : 'text-emerald-400'
            }`}>
              {riskSummary?.tight_connections || 0} Tight &middot; {riskSummary?.impossible_connections || 0} Critical
            </div>
            <div className="text-[10px] text-slate-400 font-mono">Status: {riskSummary?.highest_risk || 'SAFE'}</div>
          </div>
        </div>

      </div>

      {/* Critical Dependencies Alert if any */}
      {riskSummary?.critical_dependencies && riskSummary.critical_dependencies.length > 0 && (
        <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-500/30 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <span className="font-semibold text-amber-300">Vulnerable Connection Points Identified:</span>
            <ul className="list-disc list-inside text-slate-300 space-y-0.5 font-mono text-[11px]">
              {riskSummary.critical_dependencies.map((dep, idx) => (
                <li key={idx}>{dep}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Interactive Visual Graph: Sequential Pipeline */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <span>Multi-Modal Journey Pipeline</span>
              <span className="text-xs font-normal text-slate-400 font-mono">
                ({journey?.title || 'Active Journey'})
              </span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              NetworkX DAG visual representation showing sequential bookings, transfer buffers, and downstream dependencies.
            </p>
          </div>
          <button
            onClick={onRefreshGraph}
            disabled={loading}
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 border border-slate-700/80 cursor-pointer transition"
          >
            Recompute Graph
          </button>
        </div>

        {/* Visual Sequence Chain */}
        <div className="space-y-4">
          {nodes.length > 0 ? (
            nodes.map((node, index) => {
              const outgoingEdge = edges.find(e => e.source === node.id);

              return (
                <div key={node.id} className="space-y-4">
                  {/* Node Card */}
                  <div 
                    onClick={() => { setSelectedNodeId(node.id); setSelectedEdgeId(null); }}
                    className={`p-5 rounded-2xl border transition cursor-pointer relative ${
                      selectedNodeId === node.id 
                        ? 'bg-slate-800/90 border-sky-500 shadow-md ring-1 ring-sky-500/40' 
                        : 'bg-slate-950/70 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      
                      {/* Left: Type Icon + Provider + Title */}
                      <div className="flex items-start sm:items-center gap-3.5">
                        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800/90 shadow-inner">
                          {getTypeIcon(node.type)}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold uppercase tracking-wider text-sky-400">
                              {node.type}
                            </span>
                            <span className="text-xs text-slate-500">&bull;</span>
                            <span className="text-xs font-semibold text-slate-300">
                              {node.provider}
                            </span>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                              {node.key}
                            </span>
                          </div>
                          <h4 className="text-sm font-semibold text-white mt-0.5">
                            {node.name}
                          </h4>
                        </div>
                      </div>

                      {/* Right: Route + Times + Status */}
                      <div className="flex items-center gap-6 text-xs text-slate-300">
                        {node.origin && (
                          <div className="text-right">
                            <div className="text-slate-400 text-[11px]">Route / Location</div>
                            <div className="font-medium text-white flex items-center gap-1.5 justify-end">
                              <span>{node.origin}</span>
                              {node.destination && node.destination !== node.origin && (
                                <>
                                  <ArrowRight className="w-3 h-3 text-slate-500" />
                                  <span>{node.destination}</span>
                                </>
                              )}
                            </div>
                          </div>
                        )}

                        <div className="text-right">
                          <div className="text-slate-400 text-[11px]">Schedule Window</div>
                          <div className="font-mono text-slate-200">
                            {formatDateTime(node.start_time)} &rarr; {formatDateTime(node.end_time)}
                          </div>
                        </div>

                        <span className="text-[11px] px-2.5 py-1 rounded-full font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          {node.status || 'CONFIRMED'}
                        </span>
                      </div>

                    </div>
                  </div>

                  {/* Connecting Line & Transfer Edge Card */}
                  {outgoingEdge && (
                    <div className="flex flex-col items-center my-2">
                      {/* Connecting Line Downward */}
                      <div className="w-0.5 h-6 bg-slate-700/80" />

                      {/* Edge Transfer Card */}
                      <div 
                        onClick={() => { setSelectedEdgeId(outgoingEdge.id); setSelectedNodeId(null); }}
                        className={`w-full max-w-xl p-3.5 rounded-xl border text-xs cursor-pointer transition flex items-center justify-between gap-3 ${
                          outgoingEdge.risk_level === 'IMPOSSIBLE'
                            ? 'bg-rose-950/30 border-rose-500/40 text-rose-200'
                            : outgoingEdge.risk_level === 'TIGHT'
                              ? 'bg-amber-950/30 border-amber-500/40 text-amber-200'
                              : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700'
                        }`}
                      >
                        <div className="flex items-center gap-2.5">
                          <Clock className={`w-4 h-4 ${
                            outgoingEdge.risk_level === 'IMPOSSIBLE'
                              ? 'text-rose-400'
                              : outgoingEdge.risk_level === 'TIGHT'
                                ? 'text-amber-400'
                                : 'text-emerald-400'
                          }`} />
                          <div>
                            <div className="font-semibold text-white flex items-center gap-2">
                              <span>Connection Buffer: {outgoingEdge.buffer_minutes} mins</span>
                              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800/80 text-slate-400">
                                {outgoingEdge.transfer_type.replace(/_/g, ' ')}
                              </span>
                            </div>
                            <div className="text-[11px] text-slate-400 mt-0.5">
                              {outgoingEdge.risk_reason}
                            </div>
                          </div>
                        </div>

                        <div>
                          {getRiskBadge(outgoingEdge.risk_level)}
                        </div>
                      </div>

                      {/* Connecting Line Continued */}
                      <div className="w-0.5 h-6 bg-slate-700/80" />
                    </div>
                  )}

                </div>
              );
            })
          ) : (
            <div className="p-12 text-center text-xs text-slate-500 italic">
              No bookings recorded in journey. Ingest bookings via email in the Inbox tab to build the graph.
            </div>
          )}
        </div>

      </div>

    </div>
  );
}
