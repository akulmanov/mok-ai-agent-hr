import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import apiService from '../services/api'
import './Dashboard.css'

function Dashboard() {
  const [screenings, setScreenings] = useState([])
  const [positions, setPositions] = useState([])
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [screeningsData, positionsData, candidatesData] = await Promise.all([
        apiService.listScreenings({ limit: 10 }),
        apiService.listPositions({ limit: 1000 }),
        apiService.listCandidates({ limit: 1000 })
      ])
      setScreenings(Array.isArray(screeningsData) ? screeningsData : [])
      setPositions(Array.isArray(positionsData) ? positionsData : [])
      setCandidates(Array.isArray(candidatesData) ? candidatesData : [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
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

  const openPositions = positions.filter(p => p.is_open).length
  const closedPositions = positions.filter(p => !p.is_open).length

  return (
    <div className="dashboard">
      <div className="card">
        <h2>Панель управления</h2>
        <p className="dashboard-intro">
          Добро пожаловать в Агент HR-Отбора. Создавайте вакансии, загружайте резюме и запускайте автоматизированный отбор кандидатов.
        </p>

        <div className="dashboard-actions">
          <Link to="/positions" className="btn btn-primary">
            Вакансии
          </Link>
          <Link to="/cvs" className="btn btn-primary">
            Резюме
          </Link>
          <Link to="/screening" className="btn btn-primary">
            Запустить отбор
          </Link>
        </div>
      </div>

      <div className="stats">
        <div className="stat-card">
          <div className="stat-value">{positions.length}</div>
          <div className="stat-label">Всего вакансий</div>
          <div style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: '#64748b' }}>
            Открыто: {openPositions} | Закрыто: {closedPositions}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{candidates.length}</div>
          <div className="stat-label">Всего кандидатов</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{screenings.length}</div>
          <div className="stat-label">Последних отборов</div>
        </div>
      </div>

      <div className="card">
        <h2>Последние отборы</h2>
        {loading && <div className="loading"><div className="spinner"></div></div>}
        {error && <div className="alert alert-error">{error}</div>}
        
        {!loading && !error && (
          <>
            {screenings.length === 0 ? (
              <p style={{ color: '#64748b', textAlign: 'center', padding: '2rem' }}>
                Отборов пока нет. Создайте вакансию и загрузите резюме, чтобы начать.
              </p>
            ) : (
              <div className="screenings-list">
                {screenings.map((screening) => (
                  <Link
                    key={screening.id}
                    to={`/results/${screening.id}`}
                    className="screening-item"
                  >
                    <div className="screening-header">
                      <strong>Отбор #{screening.version}</strong>
                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <span className={`badge ${getBadgeClass(screening.decision)}`}>
                          {screening.decision === 'pass' ? 'ПРИНЯТ' : screening.decision === 'hold' ? 'НА РАССМОТРЕНИИ' : 'ОТКЛОНЕН'}
                        </span>
                        <span className="screening-score">
                          {(screening.score * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    <div className="screening-meta">
                      <small>
                        {new Date(screening.created_at).toLocaleString('ru-RU')}
                      </small>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default Dashboard
