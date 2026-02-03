import React, { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import apiService from '../services/api'
import './Dashboard.css'

function CandidateDetail() {
  const { candidateId } = useParams()
  const navigate = useNavigate()
  const [candidate, setCandidate] = useState(null)
  const [screenings, setScreenings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadCandidate()
    loadScreenings()
  }, [candidateId])

  const loadCandidate = async () => {
    try {
      setLoading(true)
      const data = await apiService.getCandidate(candidateId)
      setCandidate(data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Не удалось загрузить кандидата')
    } finally {
      setLoading(false)
    }
  }

  const loadScreenings = async () => {
    try {
      const data = await apiService.listScreenings({ candidate_id: candidateId })
      setScreenings(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error('Error loading screenings:', err)
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

  const getBadgeClass = (decision) => {
    switch (decision) {
      case 'pass':
        return 'badge-pass'
      case 'hold':
        return 'badge-hold'
      case 'reject':
        return 'badge-reject'
      default:
        return ''
    }
  }

  if (loading) {
    return (
      <div className="card">
        <div className="loading"><div className="spinner"></div></div>
      </div>
    )
  }

  if (error || !candidate) {
    return (
      <div className="card">
        <div className="alert alert-error">{error || 'Кандидат не найден'}</div>
        <Link to="/candidates" className="btn btn-primary">Вернуться к списку</Link>
      </div>
    )
  }

  const contact = getContactInfo(candidate)
  const profile = candidate.structured_profile || {}

  return (
    <div className="dashboard">
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2>Кандидат: {contact.name}</h2>
          <Link to="/candidates" className="btn btn-secondary">← Назад к списку</Link>
        </div>
      </div>

      <div className="card">
        <h3>Контактная информация</h3>
        <div style={{ marginTop: '1rem' }}>
          {contact.email && <div style={{ marginBottom: '0.5rem' }}>📧 Email: {contact.email}</div>}
          {contact.phone && <div style={{ marginBottom: '0.5rem' }}>📱 Телефон: {contact.phone}</div>}
          {contact.telegram && <div style={{ marginBottom: '0.5rem' }}>✈️ Telegram: {contact.telegram}</div>}
          {contact.whatsapp && <div style={{ marginBottom: '0.5rem' }}>💬 WhatsApp: {contact.whatsapp}</div>}
          <div style={{ marginTop: '1rem', color: '#666', fontSize: '0.875rem' }}>
            Загружено: {new Date(candidate.created_at).toLocaleString('ru-RU')} | 
            Тип файла: {candidate.cv_file_type?.toUpperCase() || 'N/A'}
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Резюме (CV)</h3>
        <div style={{ marginTop: '1rem' }}>
          <div style={{ marginBottom: '1rem' }}>
            <strong>Краткое резюме:</strong>
            <p style={{ marginTop: '0.5rem', color: '#666' }}>{profile.summary || 'Не указано'}</p>
          </div>
          
          {profile.experience && profile.experience.length > 0 && (
            <div style={{ marginBottom: '1rem' }}>
              <strong>Опыт работы:</strong>
              {profile.experience.map((exp, idx) => (
                <div key={idx} style={{ marginTop: '0.5rem', padding: '0.75rem', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
                  <div><strong>{exp.position || exp.role}</strong> - {exp.company}</div>
                  <div style={{ color: '#666', fontSize: '0.875rem' }}>{exp.duration}</div>
                  {exp.description && <div style={{ marginTop: '0.25rem' }}>{exp.description}</div>}
                </div>
              ))}
            </div>
          )}

          {profile.education && profile.education.length > 0 && (
            <div style={{ marginBottom: '1rem' }}>
              <strong>Образование:</strong>
              {profile.education.map((edu, idx) => (
                <div key={idx} style={{ marginTop: '0.5rem', padding: '0.75rem', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
                  <div><strong>{edu.degree}</strong> - {edu.institution}</div>
                  {edu.year && <div style={{ color: '#666', fontSize: '0.875rem' }}>Год: {edu.year}</div>}
                </div>
              ))}
            </div>
          )}

          {profile.skills && profile.skills.length > 0 && (
            <div style={{ marginBottom: '1rem' }}>
              <strong>Навыки:</strong>
              <div style={{ marginTop: '0.5rem', display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {profile.skills.map((skill, idx) => (
                  <span key={idx} style={{ 
                    padding: '0.25rem 0.75rem', 
                    backgroundColor: '#e3f2fd', 
                    borderRadius: '12px',
                    fontSize: '0.875rem'
                  }}>
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {candidate.raw_cv_text && (
            <div style={{ marginTop: '1rem' }}>
              <strong>Полный текст резюме:</strong>
              <pre style={{ 
                marginTop: '0.5rem', 
                padding: '1rem', 
                backgroundColor: '#f5f5f5', 
                borderRadius: '4px',
                whiteSpace: 'pre-wrap',
                fontSize: '0.875rem',
                maxHeight: '400px',
                overflow: 'auto'
              }}>
                {candidate.raw_cv_text}
              </pre>
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <h3>Результаты отборов ({screenings.length})</h3>
        {screenings.length === 0 ? (
          <p style={{ color: '#666', marginTop: '1rem' }}>Пока нет результатов отборов для этого кандидата.</p>
        ) : (
          <div className="screenings-list" style={{ marginTop: '1rem' }}>
            {screenings.map((screening) => (
              <div key={screening.id} className="screening-item" style={{ cursor: 'pointer' }} onClick={() => navigate(`/results/${screening.id}`)}>
                <div className="screening-header">
                  <strong>Отбор #{screening.version}</strong>
                  <span className={`badge ${getBadgeClass(screening.decision)}`}>
                    {screening.decision === 'pass' ? 'ПРОЙДЕН' : screening.decision === 'hold' ? 'НА УДЕРЖАНИИ' : 'ОТКЛОНЕН'}
                  </span>
                </div>
                <div className="screening-meta">
                  <div>Оценка: <strong>{screening.score ? (screening.score * 100).toFixed(1) : 'N/A'}%</strong></div>
                  <small style={{ display: 'block', marginTop: '0.5rem', color: '#666' }}>
                    {new Date(screening.created_at).toLocaleString('ru-RU')}
                  </small>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default CandidateDetail
