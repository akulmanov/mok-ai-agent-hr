import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const apiService = {
  // Positions
  createPosition: async (rawDescription) => {
    const response = await api.post('/positions', {
      raw_description: rawDescription,
    })
    return response.data
  },

  getPosition: async (positionId) => {
    const response = await api.get(`/positions/${positionId}`)
    return response.data
  },

  // Candidates
  uploadCV: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/candidates/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  getCandidate: async (candidateId) => {
    const response = await api.get(`/candidates/${candidateId}`)
    return response.data
  },

  listCandidates: async (params = {}) => {
    const queryParams = new URLSearchParams(params).toString()
    const response = await api.get(`/candidates?${queryParams}`)
    return response.data
  },

  // Screenings
  runScreening: async (candidateId, positionId) => {
    const response = await api.post(
      `/screenings?candidate_id=${candidateId}&position_id=${positionId}`
    )
    return response.data
  },

  getScreening: async (screeningId) => {
    const response = await api.get(`/screenings/${screeningId}`)
    return response.data
  },

  listScreenings: async (params = {}) => {
    const queryParams = new URLSearchParams(params).toString()
    const response = await api.get(`/screenings?${queryParams}`)
    return response.data
  },

  // Agent mode
  agentMode: async (request) => {
    const response = await api.post('/agent/screen', request)
    return response.data
  },

  matchPositions: async (candidateId, topN = 5) => {
    const response = await api.post(
      `/agent/match-positions?candidate_id=${candidateId}&top_n=${topN}`
    )
    return response.data
  },

  getCandidateChannels: async (candidateId) => {
    const response = await api.get(`/candidates/${candidateId}/channels`)
    return response.data
  },

  sendReviewResult: async (screeningId, channel, customMessage = null) => {
    const response = await api.post(`/screenings/${screeningId}/send-review`, {
      screening_id: screeningId,
      channel,
      custom_message: customMessage
    })
    return response.data
  },
}

export default apiService
