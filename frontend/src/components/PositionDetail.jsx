import React, { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import apiService from '../services/api'
import './Dashboard.css'

function PositionDetail() {
  const { positionId } = useParams()
  const navigate = useNavigate()
  const [position, setPosition] = useState(null)
  const [screenings, setScreenings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadPosition()
    loadScreenings()
  }, [positionId])

  const loadPosition = async () => {
    try {
      setLoading(true)
      const data = await apiService.getPosition(positionId)
      setPosition(data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Не удалось загрузить вакансию')
    } finally {
      setLoading(false)
    }
  }

  const loadScreenings = async () => {
    try {
      const data = await apiService.listScreenings({ position_id: positionId })
      setScreenings(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error('Error loading screenings:', err)
    }
  }

  const handleToggleStatus = async () => {
    try {
      await apiService.updatePosition(positionId, { is_open: !position.is_open })
      await loadPosition()
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Не удалось обновить статус')
    }
  }

  if (loading) {
    return (
      <div className="card">
        <div className="loading"><div className="spinner"></div></div>
      </div>
    )
  }

  if (error || !position) {
    return (
      <div className="card">
        <div className="alert alert-error">{error || 'Вакансия не найдена'}</div>
        <Link to="/positions" className="btn btn-primary">Вернуться к списку</Link>
      </div>
    )
  }

  const title = position.structured_data?.title || 'Без названия'
  const summary = position.structured_data?.summary || ''
  const requirements = position.structured_data?.requirements || []

  return (
    <div className="dashboard">
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2>{title}</h2>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <span className={`badge ${position.is_open ? 'badge-pass' : 'badge-reject'}`}>
              {position.is_open ? 'ОТКРЫТА' : 'ЗАКРЫТА'}
            </span>
            <button
              className="btn btn-secondary"
              onClick={handleToggleStatus}
            >
              {position.is_open ? 'Закрыть вакансию' : 'Открыть вакансию'}
            </button>
            <Link to="/positions" className="btn btn-secondary">← Назад к списку</Link>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Описание</h3>
        <p style={{ marginTop: '1rem', color: '#666' }}>{summary || position.raw_description}</p>
      </div>

      <div className="card">
        <h3>Требования ({requirements.length})</h3>
        <div style={{ marginTop: '1rem' }}>
          {requirements.length === 0 ? (
            <p style={{ color: '#666' }}>Требования не указаны.</p>
          ) : (
            <div>
              {requirements.filter(r => r.category === 'must').length > 0 && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ color: '#d32f2f', marginBottom: '0.5rem' }}>Обязательные требования:</h4>
                  {requirements.filter(r => r.category === 'must').map((req, idx) => (
                    <div key={idx} style={{ 
                      marginBottom: '0.5rem', 
                      padding: '0.75rem', 
                      backgroundColor: '#ffebee', 
                      borderRadius: '4px',
                      borderLeft: '3px solid #d32f2f'
                    }}>
                      {req.text} {req.weight && <span style={{ color: '#666', fontSize: '0.875rem' }}>(вес: {req.weight})</span>}
                    </div>
                  ))}
                </div>
              )}

              {requirements.filter(r => r.category === 'nice').length > 0 && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ color: '#f57c00', marginBottom: '0.5rem' }}>Желательные требования:</h4>
                  {requirements.filter(r => r.category === 'nice').map((req, idx) => (
                    <div key={idx} style={{ 
                      marginBottom: '0.5rem', 
                      padding: '0.75rem', 
                      backgroundColor: '#fff3e0', 
                      borderRadius: '4px',
                      borderLeft: '3px solid #f57c00'
                    }}>
                      {req.text} {req.weight && <span style={{ color: '#666', fontSize: '0.875rem' }}>(вес: {req.weight})</span>}
                    </div>
                  ))}
                </div>
              )}

              {requirements.filter(r => r.category === 'bonus').length > 0 && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ color: '#388e3c', marginBottom: '0.5rem' }}>Бонусные требования:</h4>
                  {requirements.filter(r => r.category === 'bonus').map((req, idx) => (
                    <div key={idx} style={{ 
                      marginBottom: '0.5rem', 
                      padding: '0.75rem', 
                      backgroundColor: '#e8f5e9', 
                      borderRadius: '4px',
                      borderLeft: '3px solid #388e3c'
                    }}>
                      {req.text} {req.weight && <span style={{ color: '#666', fontSize: '0.875rem' }}>(вес: {req.weight})</span>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <h3>Полное описание</h3>
        <pre style={{ 
          marginTop: '1rem', 
          padding: '1rem', 
          backgroundColor: '#f5f5f5', 
          borderRadius: '4px',
          whiteSpace: 'pre-wrap',
          fontSize: '0.875rem',
          maxHeight: '400px',
          overflow: 'auto'
        }}>
          {position.raw_description}
        </pre>
      </div>

      <div className="card">
        <h3>Результаты отборов ({screenings.length})</h3>
        {screenings.length === 0 ? (
          <p style={{ color: '#666', marginTop: '1rem' }}>Пока нет результатов отборов для этой вакансии.</p>
        ) : (
          <div className="screenings-list" style={{ marginTop: '1rem' }}>
            {screenings.map((screening) => (
              <div key={screening.id} className="screening-item" style={{ cursor: 'pointer' }} onClick={() => navigate(`/results/${screening.id}`)}>
                <div className="screening-header">
                  <strong>Отбор #{screening.version}</strong>
                  <span className={`badge ${screening.decision === 'pass' ? 'badge-pass' : screening.decision === 'hold' ? 'badge-hold' : 'badge-reject'}`}>
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

export default PositionDetail
