import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"
});

export async function fetchSymptoms() {
  const { data } = await api.get("/api/symptoms");
  return data;
}

export async function fetchTopFeatures() {
  const { data } = await api.get("/api/feature-importance?top_n=20");
  return data;
}

export async function predictDisease(payload) {
  const { data } = await api.post("/api/predict", payload);
  return data;
}

export async function fetchHistoryFull(limit = 100) {
  const { data } = await api.get(`/api/history-full?limit=${limit}`);
  return data;
}

export async function fetchReportPdf(recordId) {
  const response = await api.get(`/api/report/${recordId}`, { responseType: "blob" });
  return response.data;
}

export function reportUrl(recordId) {
  return `${api.defaults.baseURL}/api/report/${recordId}`;
}
