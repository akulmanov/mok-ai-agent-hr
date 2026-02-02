import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import apiService from '../services/api'
import './Dashboard.css'

function Candidates() {
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadCandidates()
  }, [])

  const loadCandidates = async () => {
    try {
      setLoading(true)
      const data = await apiService.listCandidates({ limit: 100 })
      setCandidates(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Не удалось загрузить кандидатов')
    } finally {
      setLoading(false)
    }
  }

  const getContactInfo = (candidate) => {
    const profile = candidate.structured_profile || {}
    return {
      name: profile.name || 'Не указано',
      email: profile.email || null,
      phone: profile.phone || null,
      telegram: profile.telegram || null,
      whatsapp: profile.whatsapp || null
    }
  }

  return (
    <div className="dashboard">
      <div className="card">
        <h2>Кандидаты</h2>
        <p className="dashboard-intro">
          Список всех кандидатов, загруженных в систему. Просматривайте контактную информацию и историю отборов.
        </p>
      </div>

      <div className="card">
        <h2>Список кандидатов</h2>
        {loading && <div className="loading"><div className="spinner"></div></div>}
        {error && <div className="alert alert-error">{error}</div>}
        
        {!loading && !error && (
          <>
            {candidates.length === 0 ? (
              <p>Кандидатов пока нет. Загрузите резюме, чтобы начать.</p>
            ) : (
              <div className="screenings-list">
                {candidates.map((candidate) => {
                  const contact = getContactInfo(candidate)
                  return (
                    <div key={candidate.id} className="screening-item">
                      <div className="screening-header">
                        <strong>{contact.name}</strong>
                        <span className="screening-score">
                          ID: {candidate.id.substring(0, 8)}...
                        </span>
                      </div>
                      <div className="screening-meta">
                        <div style={{ marginTop: '0.5rem' }}>
                          {contact.email && (
                            <span style={{ marginRight: '1rem' }}>📧 {contact.email}</span>
                          )}
                          {contact.phone && (
                            <span style={{ marginRight: '1rem' }}>📱 {contact.phone}</span>
                          )}
                          {contact.telegram && (
                            <span style={{ marginRight: '1rem' }}>✈️ {contact.telegram}</span>
                          )}
                          {contact.whatsapp && (
                            <span style={{ marginRight: '1rem' }}>💬 {contact.whatsapp}</span>
                          )}
                        </div>
                        <small style={{ display: 'block', marginTop: '0.5rem', color: '#666' }}>
                          Загружено: {new Date(candidate.created_at).toLocaleString('ru-RU')} | 
                          Тип файла: {candidate.cv_file_type?.toUpperCase() || 'N/A'}
                        </small>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default Candidates
