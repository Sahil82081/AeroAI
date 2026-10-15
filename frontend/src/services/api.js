import axios from 'axios';

let rawBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
let normalizedBaseUrl = rawBaseUrl.trim().replace(/\/+$/, '');
if (!normalizedBaseUrl.endsWith('/api/v1') && !normalizedBaseUrl.endsWith('/api')) {
  normalizedBaseUrl = `${normalizedBaseUrl}/api/v1`;
}

export const API_BASE_URL = normalizedBaseUrl;

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('adr_access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const apiService = {
  // Health
  checkHealth: async () => {
    const res = await apiClient.get('/health');
    return res.data;
  },

  // Auth
  login: async (email, password) => {
    const res = await apiClient.post('/auth/login', { email, password });
    if (res.data.access_token) {
      localStorage.setItem('adr_access_token', res.data.access_token);
    }
    return res.data;
  },
  getCurrentUser: async () => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },
  logout: () => {
    localStorage.removeItem('adr_access_token');
  },

  // Journeys
  getJourneys: async () => {
    const res = await apiClient.get('/journeys/');
    return res.data;
  },
  getJourney: async (id) => {
    const res = await apiClient.get(`/journeys/${id}`);
    return res.data;
  },
  getJourneyGraph: async (id) => {
    const res = await apiClient.get(`/journeys/${id}/graph`);
    return res.data;
  },
  getJourneyNodes: async (id) => {
    const res = await apiClient.get(`/journeys/${id}/nodes`);
    return res.data;
  },
  getJourneyDependencies: async (id) => {
    const res = await apiClient.get(`/journeys/${id}/dependencies`);
    return res.data;
  },
  getJourneyRisks: async (id) => {
    const res = await apiClient.get(`/journeys/${id}/risks`);
    return res.data;
  },

  // Disruptions
  getDisruptions: async (journeyId) => {
    const res = await apiClient.get('/disruptions/', {
      params: journeyId ? { journey_id: journeyId } : {},
    });
    return res.data;
  },
  simulateDisruption: async (payload) => {
    const res = await apiClient.post('/disruptions/simulate', payload);
    return res.data;
  },
  getDisruptionEvents: async () => {
    const res = await apiClient.get('/disruptions/events');
    return res.data;
  },

  // Recovery Plans
  getRecoveryPlans: async (journeyId) => {
    const res = await apiClient.get('/recovery/plans', {
      params: journeyId ? { journey_id: journeyId } : {},
    });
    return res.data;
  },

  // Notifications
  getNotifications: async () => {
    const res = await apiClient.get('/notifications/');
    return res.data;
  },

  // Ingestion & Simulated Inbox
  getSampleEmails: async () => {
    const res = await apiClient.get('/ingestion/samples');
    return res.data;
  },
  getInboxEmails: async (status) => {
    const res = await apiClient.get('/ingestion/inbox', {
      params: status ? { status } : {},
    });
    return res.data;
  },
  forwardEmail: async (payload) => {
    const res = await apiClient.post('/ingestion/forward', payload);
    return res.data;
  },

  // Stage 5: Mock Supplier Ecosystem (via SupplierIntegrationService -> SupplierAdapter -> Mock API)
  searchSupplierFlights: async (params = {}) => {
    const res = await apiClient.get('/suppliers/flights/search', { params });
    return res.data;
  },
  searchSupplierTrains: async (params = {}) => {
    const res = await apiClient.get('/suppliers/trains/search', { params });
    return res.data;
  },
  searchSupplierBuses: async (params = {}) => {
    const res = await apiClient.get('/suppliers/buses/search', { params });
    return res.data;
  },
  searchSupplierHotels: async (params = {}) => {
    const res = await apiClient.get('/suppliers/hotels/search', { params });
    return res.data;
  },
  rebookSupplierBooking: async (payload) => {
    const res = await apiClient.post('/suppliers/bookings/rebook', payload);
    return res.data;
  },
  cancelSupplierBooking: async (payload) => {
    const res = await apiClient.post('/suppliers/bookings/cancel', payload);
    return res.data;
  },
  refundSupplierBooking: async (payload) => {
    const res = await apiClient.post('/suppliers/bookings/refund', payload);
    return res.data;
  },
  modifySupplierHotel: async (payload) => {
    const res = await apiClient.post('/suppliers/hotel/modify', payload);
    return res.data;
  },
  getSupplierSimulationConfig: async () => {
    const res = await apiClient.get('/suppliers/simulation/config');
    return res.data;
  },
  updateSupplierSimulationConfig: async (payload) => {
    const res = await apiClient.post('/suppliers/simulation/config', payload);
    return res.data;
  },
  resetSupplierSimulation: async () => {
    const res = await apiClient.post('/suppliers/simulation/reset');
    return res.data;
  },

  // Stage 6: Google OR-Tools Recovery Optimization
  optimizeRecovery: async (payload) => {
    const res = await apiClient.post('/recovery/optimize', payload);
    return res.data;
  },
  getOptimizationPresets: async () => {
    const res = await apiClient.get('/recovery/optimize/presets');
    return res.data;
  },

  // Stage 7: LangGraph Autonomous Recovery Agent Workflow
  runLangGraphAgent: async (payload) => {
    const res = await apiClient.post('/recovery/agent/run', payload);
    return res.data;
  },
  getLangGraphMetadata: async () => {
    const res = await apiClient.get('/recovery/agent/graph-metadata');
    return res.data;
  },

  // Stage 8: Autonomous Recovery Action Execution & Audit History
  executeRecoveryPlan: async (payload) => {
    const res = await apiClient.post('/recovery/execute', payload);
    return res.data;
  },
  executeSingleAction: async (payload) => {
    const res = await apiClient.post('/recovery/actions/execute-single', payload);
    return res.data;
  },
  getActionHistory: async () => {
    const res = await apiClient.get('/recovery/actions/history');
    return res.data;
  },
  clearActionHistory: async () => {
    const res = await apiClient.post('/recovery/actions/clear');
    return res.data;
  },

  // Stage 9: Event-Driven Architecture with Apache Kafka & Real-Time WebSocket
  getKafkaWebSocketUrl: () => {
    const httpBase = API_BASE_URL.replace(/^http/i, 'ws');
    return `${httpBase}/events/ws`;
  },
  triggerKafkaDisruptionPipeline: async (payload) => {
    const res = await apiClient.post('/events/disruption-pipeline', payload);
    return res.data;
  },
  publishCustomKafkaEvent: async (payload) => {
    const res = await apiClient.post('/events/publish', payload);
    return res.data;
  },
  getKafkaTopics: async () => {
    const res = await apiClient.get('/events/topics');
    return res.data;
  },
  getKafkaEventStream: async (params = {}) => {
    const res = await apiClient.get('/events/stream', { params });
    return res.data;
  },
  getKafkaConsumers: async () => {
    const res = await apiClient.get('/events/consumers');
    return res.data;
  },
  getKafkaDlq: async () => {
    const res = await apiClient.get('/events/dlq');
    return res.data;
  },
  replayKafkaDlqEvent: async (dlqId) => {
    const res = await apiClient.post(`/events/dlq/${dlqId}/replay`);
    return res.data;
  },
  resetKafkaBroker: async () => {
    const res = await apiClient.post('/events/reset');
    return res.data;
  },

  // Stage 10: Email and Notification Agent & Anti-Hallucination Inbox
  getNotificationInbox: async (category = null, seedIfEmpty = false) => {
    const params = { seed_if_empty: seedIfEmpty };
    if (category && category !== 'ALL') params.category = category;
    const res = await apiClient.get('/notifications/inbox', { params });
    return res.data;
  },
  generateNotificationSuite: async (payload = {}) => {
    const res = await apiClient.post('/notifications/generate-suite', payload);
    return res.data;
  },
  validateNotificationDraft: async (payload) => {
    const res = await apiClient.post('/notifications/validate-draft', payload);
    return res.data;
  },
  getNotificationTemplates: async () => {
    const res = await apiClient.get('/notifications/templates');
    return res.data;
  },
  clearNotificationInbox: async () => {
    const res = await apiClient.post('/notifications/clear');
    return res.data;
  },

  // Live SQLite Workspace API (Zero Dummy Fallback)
  getLiveWorkspace: async () => {
    const res = await apiClient.get('/recovery/live-workspace');
    return res.data;
  },
  clearLiveWorkspace: async () => {
    const res = await apiClient.post('/recovery/live-workspace/clear');
    return res.data;
  },
  addLiveBooking: async (payload) => {
    const res = await apiClient.post('/recovery/live-workspace/add-booking', payload);
    return res.data;
  },
  deleteLiveBooking: async (bookingId) => {
    const res = await apiClient.delete(`/recovery/live-workspace/booking/${bookingId}`);
    return res.data;
  },
  simulateDemoDisruption: async (payload) => {
    const res = await apiClient.post('/recovery/demo/simulate-disruption', payload);
    return res.data;
  },
  recoverLiveWorkspace: async () => {
    const res = await apiClient.post('/recovery/live-workspace/recover');
    return res.data;
  },
  getRealTransportCatalog: async () => {
    const res = await apiClient.get('/recovery/live-workspace/real-catalog');
    return res.data;
  },

  // Feature 1: Live Travel News Feed (Google News RSS)
  getNews: async (params = {}) => {
    const res = await apiClient.get('/news', { params });
    return res.data;
  },

  // Feature 2: Airline Policy Chatbot (RAG)
  sendChatMessage: async (payload) => {
    const res = await apiClient.post('/chat', payload);
    return res.data;
  },
  getChatHistory: async (sessionId) => {
    const res = await apiClient.get(`/chat/history/${sessionId}`);
    return res.data;
  },

  // Stage 6: Flight Provider & Live Status Intelligence
  getFlightStatus: async (flightNumber, date = null) => {
    const params = date ? { date } : {};
    const res = await apiClient.get(`/flights/status/${flightNumber}`, { params });
    return res.data;
  },
  getFlightPrediction: async (flightNumber, date = null) => {
    const params = date ? { date } : {};
    const res = await apiClient.get(`/flights/status/${flightNumber}/prediction`, { params });
    return res.data;
  },
  searchFlightInventory: async (params) => {
    const res = await apiClient.get('/flights/inventory', { params });
    return res.data;
  },
  getFlightProviderInfo: async () => {
    const res = await apiClient.get('/flights/provider-info');
    return res.data;
  },

  // Weather Intelligence
  getWeatherObservation: async (airportCode) => {
    const res = await apiClient.get(`/weather/observation/${airportCode}`);
    return res.data;
  },

  // Stage 7: AeroAI Unified AI Agent
  sendAgentQuery: async (payload) => {
    const res = await apiClient.post('/agent/query', payload);
    return res.data;
  },
  sendAgentChat: async (payload) => {
    const res = await apiClient.post('/agent/chat', payload);
    return res.data;
  },
  getAgentTools: async () => {
    const res = await apiClient.get('/agent/tools');
    return res.data;
  },
  getAgentAuditLogs: async (limit = 20) => {
    const res = await apiClient.get('/agent/audit-logs', { params: { limit } });
    return res.data;
  },

  // Stage 4: Machine Learning Model Metrics & Evaluation Benchmarks
  getModelEvaluationMetrics: async () => {
    const res = await apiClient.get('/predict/evaluation-metrics');
    return res.data;
  },
  getModelInfo: async () => {
    const res = await apiClient.get('/predict/model-info');
    return res.data;
  },
};

export const api = apiService;
export default apiService;

