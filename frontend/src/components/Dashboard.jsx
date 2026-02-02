import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import apiService from '../services/api'
import './Dashboard.css'

function Dashboard() {
  const [screenings, setScreenings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadScreenings()
  }, [])

  const loadScreenings = async () => {
    try {
      setLoading(true)
      const data = await apiService.listScreenings({ limit: 10 })
      setScreenings(Array.isArray(data) ? data : [])
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

  return (
    <div className="dashboard">
      <div className="card">
        <h2>Панель управления</h2>
        <p className="dashboard-intro">
          Добро пожаловать в Агент HR-Отбора. Создавайте вакансии, загружайте резюме и запускайте автоматизированный отбор кандидатов.
        </p>

        <div className="dashboard-actions">
          <Link to="/job-posting" className="btn btn-primary">
            Создать новую вакансию
          </Link>
          <Link to="/upload-cv" className="btn btn-primary">
            Загрузить резюме
          </Link>
          <Link to="/screening" className="btn btn-primary">
            Запустить отбор
          </Link>
        </div>
      </div>

      <div className="card">
        <h2>Последние отборы</h2>
        {loading && <div className="loading"><div className="spinner"></div></div>}
        {error && <div className="alert alert-error">{error}</div>}
        
        {!loading && !error && (
          <>
            {screenings.length === 0 ? (
              <p>Отборов пока нет. Создайте вакансию и загрузите резюме, чтобы начать.</p>
            ) : (
              <div className="screenings-list">
                {screenings.map((screening) => (
                  <Link
                    key={screening.id}
                    to={`/results/${screening.id}`}
                    className="screening-item"
                  >
                    <div className="screening-header">
                      <span className={`badge ${getBadgeClass(screening.decision)}`}>
                        {screening.decision === 'pass' ? 'ПРИНЯТ' : screening.decision === 'hold' ? 'НА РАССМОТРЕНИИ' : 'ОТКЛОНЕН'}
                      </span>
                      <span className="screening-score">
                        Оценка: {(screening.score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="screening-meta">
                      <small>
                        Кандидат: {screening.candidate_id?.substring(0, 8)}... | 
                        Вакансия: {screening.position_id?.substring(0, 8)}... | 
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
