import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const fetchStoreAnalytics = async (storeId: string) => {
  const response = await api.get(`/analytics/store-summary`, {
    params: { store_id: storeId },
  })
  return response.data
}

export const fetchZoneAnalytics = async (storeId: string) => {
  const response = await api.get(`/analytics/zones`, {
    params: { store_id: storeId },
  })
  return response.data
}

export const fetchQueueAnalytics = async (storeId: string) => {
  const response = await api.get(`/analytics/queue`, {
    params: { store_id: storeId },
  })
  return response.data
}

export const fetchAnomalies = async () => {
  const response = await api.get('/analytics/anomalies')
  return response.data
}

export const fetchRecentEvents = async (limit: number = 50, storeId?: string) => {
  const response = await api.get('/events/recent', {
    params: { limit, store_id: storeId },
  })
  return response.data
}

export const ingestData = async () => {
  const response = await api.post('/ingest')
  return response.data
}
