import React, { useState, useEffect } from 'react';
import {
  Plane,
  Train,
  Bus,
  Hotel,
  Search,
  RefreshCw,
  CheckCircle2,
  AlertOctagon,
  Clock,
  DollarSign,
  Layers,
  ArrowRight,
  RotateCcw,
  ShieldAlert,
  Sliders
} from 'lucide-react';
import { apiService } from '../services/api';

export function SupplierEcosystemView() {
  const [activeSupplierTab, setActiveSupplierTab] = useState('trains');
  const [originFilter, setOriginFilter] = useState('Delhi');
  const [destinationFilter, setDestinationFilter] = useState('Jaipur');
  const [hotelLocationFilter, setHotelLocationFilter] = useState('Jaipur');

  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [actionResult, setActionResult] = useState(null);
  const [actionError, setActionError] = useState(null);

  // Simulation controls
  const [simLatencyMs, setSimLatencyMs] = useState(35);
  const [simFailureMode, setSimFailureMode] = useState('none');
  const [disruptionWaiver, setDisruptionWaiver] = useState(true);
  const [lastLatency, setLastLatency] = useState(null);
  const [adapterTrace, setAdapterTrace] = useState(null);

  const fetchInventory = async (supplierType = activeSupplierTab, orig = originFilter, dest = destinationFilter, loc = hotelLocationFilter) => {
    setLoading(true);
    setActionError(null);
    try {
      const simParams = {
        simulate_latency_ms: simLatencyMs,
        simulate_failure: simFailureMode !== 'none' ? simFailureMode : undefined,
      };

      let res;
      if (supplierType === 'flights') {
        res = await apiService.searchSupplierFlights({
          origin: orig || undefined,
          destination: dest || undefined,
          ...simParams,
        });
      } else if (supplierType === 'trains') {
        res = await apiService.searchSupplierTrains({
          origin: orig || undefined,
          destination: dest || undefined,
          ...simParams,
        });
      } else if (supplierType === 'buses') {
        res = await apiService.searchSupplierBuses({
          origin: orig || undefined,
          destination: dest || undefined,
          ...simParams,
        });
      } else {
        res = await apiService.searchSupplierHotels({
          location: loc || undefined,
          ...simParams,
        });
      }

      setInventory(res.results || []);
      setLastLatency(res.simulated_latency_ms);
      setAdapterTrace(res.adapter_trace || null);
    } catch (err) {
      setInventory([]);
      const detail = err.response?.data?.detail;
      setActionError(typeof detail === 'object' ? detail : { message: err.message || 'Supplier API Failure' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory(activeSupplierTab, originFilter, destinationFilter, hotelLocationFilter);
  }, [activeSupplierTab]);

  const handlePresetRoute = (type, orig, dest, loc = '') => {
    setActiveSupplierTab(type);
    setOriginFilter(orig);
    setDestinationFilter(dest);
    if (loc) setHotelLocationFilter(loc);
    fetchInventory(type, orig, dest, loc);
  };

  const handleRebook = async (item) => {
    setActionError(null);
    try {
      const res = await apiService.rebookSupplierBooking({
        original_booking_ref: `ORIG-${item.transport_id}`,
        transport_id: item.transport_id,
        passenger_name: 'Sahil Sharma',
        seats: 1,
        reason: 'DISRUPTION_RECOVERY',
        waive_change_fee: disruptionWaiver,
        simulate_latency_ms: simLatencyMs,
        simulate_failure: simFailureMode !== 'none' ? simFailureMode : undefined,
      });
      setActionResult({ type: 'REBOOK_CONFIRMED', data: res });
      setLastLatency(res.simulated_latency_ms);
      setAdapterTrace(res.adapter_trace || null);
      fetchInventory();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setActionError(typeof detail === 'object' ? detail : { message: err.message });
    }
  };

  const handleRefund = async (item) => {
    setActionError(null);
    try {
      const id = item.transport_id || item.hotel_id;
      const res = await apiService.refundSupplierBooking({
        booking_reference: `REF-${id}-882`,
        transport_id: id,
        supplier_type: item.supplier_type,
        original_price: item.price || item.price_per_night || 800,
        currency: item.currency || 'INR',
        reason: disruptionWaiver ? 'CARRIER_DISRUPTION_WAIVER' : 'VOLUNTARY_CANCELLATION',
        is_disruption_waiver: disruptionWaiver,
        simulate_latency_ms: simLatencyMs,
        simulate_failure: simFailureMode !== 'none' ? simFailureMode : undefined,
      });
      setActionResult({ type: 'REFUND_EVALUATED', data: res });
      setLastLatency(res.simulated_latency_ms);
      setAdapterTrace(res.adapter_trace || null);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setActionError(typeof detail === 'object' ? detail : { message: err.message });
    }
  };

  const handleCancel = async (item) => {
    setActionError(null);
    try {
      const id = item.transport_id || item.hotel_id;
      const res = await apiService.cancelSupplierBooking({
        booking_reference: `PNR-${id}-401`,
        transport_id: id,
        supplier_type: item.supplier_type,
        original_price: item.price || item.price_per_night || 800,
        reason: disruptionWaiver ? 'DISRUPTION_CASCADE' : 'TRAVELER_REQUEST',
        simulate_latency_ms: simLatencyMs,
        simulate_failure: simFailureMode !== 'none' ? simFailureMode : undefined,
      });
      setActionResult({ type: 'BOOKING_CANCELLED', data: res });
      setLastLatency(res.simulated_latency_ms);
      setAdapterTrace(res.adapter_trace || null);
      fetchInventory();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setActionError(typeof detail === 'object' ? detail : { message: err.message });
    }
  };

  const handleHotelModify = async (hotel) => {
    setActionError(null);
    try {
      const res = await apiService.modifySupplierHotel({
        booking_reference: `HTL-RES-${hotel.hotel_id}`,
        hotel_id: hotel.hotel_id,
        new_check_in: '2026-10-20T22:45:00',
        late_arrival_notice: true,
        notes: 'Delayed arrival due to upstream flight/train connection shift. Please hold room.',
        simulate_latency_ms: simLatencyMs,
        simulate_failure: simFailureMode !== 'none' ? simFailureMode : undefined,
      });
      setActionResult({ type: 'HOTEL_CHECKIN_MODIFIED', data: res });
      setLastLatency(res.simulated_latency_ms);
      setAdapterTrace(res.adapter_trace || null);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setActionError(typeof detail === 'object' ? detail : { message: err.message });
    }
  };

  const handleResetSimulation = async () => {
    await apiService.resetSupplierSimulation();
    setSimFailureMode('none');
    setSimLatencyMs(35);
    setActionResult(null);
    setActionError(null);
    fetchInventory(activeSupplierTab, originFilter, destinationFilter, hotelLocationFilter);
  };

  return (
    <div className="space-y-6">
      {/* Architecture & Mock Disclaimer Header */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-emerald-500/30 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                STAGE 5 &middot; SIMULATED MOCK SUPPLIER API ECOSYSTEM
              </span>
              {lastLatency !== null && (
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono bg-slate-800 text-sky-400 border border-slate-700 flex items-center gap-1">
                  <Clock className="w-3 h-3" /> {lastLatency} ms simulated latency
                </span>
              )}
            </div>
            <h2 className="text-lg font-bold text-white mt-1.5">
              Decoupled Multi-Modal Supplier Ecosystem (Flight, Train, Bus &amp; Hotel Mock Services)
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              All APIs below are explicitly marked as <strong>MOCK APIs</strong>. Agents communicate strictly through the decoupled adapter chain so real GDS/CRS providers can replace mocks without changing agent code.
            </p>
          </div>

          <button
            onClick={handleResetSimulation}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 border border-slate-700 flex items-center gap-1.5 cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5 text-emerald-400" />
            Reset Mock Inventory
          </button>
        </div>

        {/* Visual Architecture Chain */}
        <div className="p-3.5 rounded-xl bg-slate-950/90 border border-slate-800 flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 font-semibold">
              1. Recovery Agent
            </span>
            <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
            <span className="px-2.5 py-1 rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-300 font-semibold">
              2. Supplier Service Interface
            </span>
            <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
            <span className="px-2.5 py-1 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 font-semibold">
              3. Supplier HTTP Adapter
            </span>
            <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
            <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 font-semibold">
              4. Mock Supplier REST API
            </span>
          </div>
          {adapterTrace && (
            <span className="font-mono text-[11px] text-slate-400">
              {adapterTrace.adapter_class} &rarr; <strong className="text-emerald-400">{adapterTrace.mock_api_endpoint}</strong>
            </span>
          )}
        </div>
      </div>

      {/* Simulation Controls & Quick Route Presets */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 cols: Supplier Tabs + Filter Bar + Inventory Cards */}
        <div className="lg:col-span-2 space-y-4">
          {/* 4 Supplier Service Selector Tabs */}
          <div className="flex flex-wrap items-center justify-between gap-2 bg-slate-900/60 p-2 rounded-xl border border-slate-800">
            <div className="flex flex-wrap gap-1.5">
              {[
                { id: 'flights', label: '1. Flight Supplier', icon: Plane, endpoint: 'GET /flights/search' },
                { id: 'trains', label: '2. Train Supplier', icon: Train, endpoint: 'GET /trains/search' },
                { id: 'buses', label: '3. Bus Supplier', icon: Bus, endpoint: 'GET /buses/search' },
                { id: 'hotels', label: '4. Hotel Supplier', icon: Hotel, endpoint: 'GET /hotels/search' },
              ].map((tab) => {
                const Icon = tab.icon;
                const active = activeSupplierTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveSupplierTab(tab.id)}
                    className={`px-3.5 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition cursor-pointer ${
                      active
                        ? 'bg-emerald-600 text-white shadow'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Quick Route Presets */}
            <div className="flex items-center gap-1.5 text-[11px]">
              <button
                onClick={() => handlePresetRoute('trains', 'Delhi', 'Jaipur')}
                className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 cursor-pointer"
              >
                Delhi &rarr; Jaipur
              </button>
              <button
                onClick={() => handlePresetRoute('flights', 'Mumbai', 'Delhi')}
                className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 cursor-pointer"
              >
                Mumbai &rarr; Delhi
              </button>
              <button
                onClick={() => handlePresetRoute('flights', 'SFO', 'HND')}
                className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 cursor-pointer"
              >
                SFO &rarr; HND
              </button>
              <button
                onClick={() => handlePresetRoute(activeSupplierTab, '', '', '')}
                className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-sky-400 border border-slate-700 cursor-pointer"
              >
                Show All
              </button>
            </div>
          </div>

          {/* Search Inputs */}
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-wrap items-end gap-3">
            {activeSupplierTab !== 'hotels' ? (
              <>
                <div className="flex-1 min-w-[140px]">
                  <label className="block text-[11px] font-medium text-slate-400 mb-1">Origin City / Code</label>
                  <input
                    type="text"
                    value={originFilter}
                    onChange={(e) => setOriginFilter(e.target.value)}
                    placeholder="e.g. Delhi, Mumbai, SFO"
                    className="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white"
                  />
                </div>
                <div className="flex-1 min-w-[140px]">
                  <label className="block text-[11px] font-medium text-slate-400 mb-1">Destination City / Code</label>
                  <input
                    type="text"
                    value={destinationFilter}
                    onChange={(e) => setDestinationFilter(e.target.value)}
                    placeholder="e.g. Jaipur, Delhi, HND"
                    className="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white"
                  />
                </div>
              </>
            ) : (
              <div className="flex-1 min-w-[200px]">
                <label className="block text-[11px] font-medium text-slate-400 mb-1">Hotel City / Location</label>
                <input
                  type="text"
                  value={hotelLocationFilter}
                  onChange={(e) => setHotelLocationFilter(e.target.value)}
                  placeholder="e.g. Jaipur, Delhi, Mumbai, Tokyo"
                  className="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white"
                />
              </div>
            )}

            <button
              onClick={() => fetchInventory()}
              disabled={loading}
              className="px-4 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
            >
              <Search className="w-3.5 h-3.5" />
              <span>{loading ? 'Querying Mock API...' : 'Search Supplier API'}</span>
            </button>
          </div>

          {/* Inventory Cards */}
          <div className="space-y-3">
            {inventory.length > 0 ? (
              inventory.map((item) => {
                const id = item.transport_id || item.hotel_id;
                const rules = item.cancellation_rules || {};
                return (
                  <div
                    key={id}
                    className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition space-y-3"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-mono text-xs font-bold">
                            {id}
                          </span>
                          <span className="text-sm font-bold text-white">
                            {item.provider}
                          </span>
                          <span className="text-xs text-slate-400 font-mono">
                            {item.flight_number || item.train_number || item.bus_number || item.room_type}
                          </span>
                          <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-amber-300 font-mono border border-slate-700">
                            MOCK API
                          </span>
                        </div>

                        {item.supplier_type !== 'hotel' ? (
                          <div className="text-xs text-slate-300 mt-1 flex flex-wrap items-center gap-2">
                            <span className="font-semibold text-sky-400">{item.origin}</span>
                            <span>&rarr;</span>
                            <span className="font-semibold text-sky-400">{item.destination}</span>
                            <span className="text-slate-500">|</span>
                            <span className="font-mono text-[11px]">Dep: {item.departure}</span>
                            <span className="text-slate-500">&rarr;</span>
                            <span className="font-mono text-[11px]">Arr: {item.arrival}</span>
                          </div>
                        ) : (
                          <div className="text-xs text-slate-300 mt-1">
                            <span className="font-semibold text-sky-400">{item.location}</span> &middot; {item.address} &middot; Check-in: {item.check_in_window}
                          </div>
                        )}
                      </div>

                      <div className="text-right">
                        <div className="text-base font-bold text-emerald-400">
                          {item.currency} {item.price || item.price_per_night}
                        </div>
                        <div className="text-[11px] text-slate-400">
                          {item.supplier_type !== 'hotel'
                            ? `${item.available_seats} seats available`
                            : `${item.available_rooms} rooms available`}
                        </div>
                      </div>
                    </div>

                    {/* Cancellation & Refund Rules Strip */}
                    <div className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400">
                      <div className="flex flex-wrap items-center gap-3">
                        <span>
                          Tier: <strong className="text-slate-200">{rules.fare_tier || 'STANDARD'}</strong>
                        </span>
                        <span>&bull;</span>
                        <span>
                          Refundable: <strong className={item.refund_eligibility ? 'text-emerald-400' : 'text-rose-400'}>
                            {item.refund_eligibility ? 'Yes' : 'Non-Refundable (Tax Only)'}
                          </strong>
                        </span>
                        <span>&bull;</span>
                        <span>
                          Penalty: <strong className="text-slate-200">{rules.penalty_pct}%</strong> (min {item.currency} {rules.cancellation_fee})
                        </span>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex flex-wrap items-center gap-2">
                        {item.supplier_type !== 'hotel' ? (
                          <button
                            onClick={() => handleRebook(item)}
                            className="px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-semibold cursor-pointer"
                          >
                            POST /bookings/rebook
                          </button>
                        ) : (
                          <button
                            onClick={() => handleHotelModify(item)}
                            className="px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-semibold cursor-pointer"
                          >
                            POST /hotel/modify (Late Check-in)
                          </button>
                        )}
                        <button
                          onClick={() => handleRefund(item)}
                          className="px-2.5 py-1 rounded bg-sky-600/80 hover:bg-sky-500 text-white font-semibold cursor-pointer"
                        >
                          POST /bookings/refund
                        </button>
                        <button
                          onClick={() => handleCancel(item)}
                          className="px-2.5 py-1 rounded bg-rose-600/80 hover:bg-rose-500 text-white font-semibold cursor-pointer"
                        >
                          POST /bookings/cancel
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="p-8 rounded-xl bg-slate-900/40 border border-slate-800 text-center text-xs text-slate-500">
                {loading ? 'Querying Mock Supplier API...' : 'No matching inventory found for current filter or failure simulated.'}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Fault & Latency Simulator + Live Response Inspector */}
        <div className="space-y-4">
          <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800 space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400">
              <Sliders className="w-4 h-4" />
              Supplier Fault &amp; Latency Controls
            </div>

            <div>
              <label className="block text-xs text-slate-300 mb-1">
                Simulated API Latency: <strong className="text-sky-400">{simLatencyMs} ms</strong>
              </label>
              <input
                type="range"
                min="0"
                max="500"
                step="5"
                value={simLatencyMs}
                onChange={(e) => setSimLatencyMs(Number(e.target.value))}
                className="w-full accent-sky-500"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-300 mb-1">Simulate Supplier Failure Mode</label>
              <select
                value={simFailureMode}
                onChange={(e) => setSimFailureMode(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white"
              >
                <option value="none">None (Healthy 200 OK)</option>
                <option value="timeout">HTTP 504 - Supplier Gateway Timeout</option>
                <option value="service_unavailable">HTTP 503 - Supplier GDS Unavailable</option>
                <option value="seat_unavailable">HTTP 409 - Seat/Room Inventory Exhausted</option>
              </select>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-800">
              <span className="text-xs text-slate-300">Disruption Waiver Active</span>
              <input
                type="checkbox"
                checked={disruptionWaiver}
                onChange={(e) => setDisruptionWaiver(e.target.checked)}
                className="w-4 h-4 accent-emerald-500"
              />
            </div>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              When <strong>Disruption Waiver</strong> is enabled, involuntary rebookings and refund claims waive standard airline/rail cancellation penalties.
            </p>
          </div>

          {/* Error Alert if failure injected */}
          {actionError && (
            <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold text-rose-400">
                <AlertOctagon className="w-4 h-4" />
                <span>SIMULATED SUPPLIER API ERROR ({actionError.error_code || 'ERROR'})</span>
              </div>
              <p className="text-xs text-rose-200">{actionError.message}</p>
              <pre className="p-2 rounded bg-slate-950 text-[10px] text-rose-300 overflow-x-auto font-mono">
                {JSON.stringify(actionError, null, 2)}
              </pre>
            </div>
          )}

          {/* Action Confirmation / Refund Inspector */}
          {actionResult && (
            <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  {actionResult.type}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
                  MOCK CONFIRMATION
                </span>
              </div>
              <pre className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-300 overflow-x-auto max-h-80 font-mono">
                {JSON.stringify(actionResult.data, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
