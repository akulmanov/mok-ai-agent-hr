import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import apiService from '../services/api'

function JobPosting() {
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const position = await apiService.createPosition(description)
      setSuccess(`Вакансия создана! ID вакансии: ${position.id}`)
      setDescription('')
      setTimeout(() => {
        navigate('/')
      }, 2000)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to create job posting')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2>Создать вакансию</h2>
      <p style={{ color: '#666', marginBottom: '1.5rem' }}>
        Вставьте текст описания вакансии. Система автоматически извлечет структурированные требования.
      </p>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="description">Описание вакансии</label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Вставьте описание вакансии здесь. Например:&#10;&#10;Ищем Senior Python Developer с опытом работы 5+ лет. Обязательно: опыт работы с FastAPI, PostgreSQL и облачными платформами (предпочтительно AWS). Желательно: Docker, Kubernetes, опыт работы с машинным обучением."
            required
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Создание...' : 'Создать вакансию'}
        </button>
      </form>
    </div>
  )
}

export default JobPosting
