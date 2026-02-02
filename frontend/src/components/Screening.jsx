import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import apiService from '../services/api'

function Screening() {
  const [candidateId, setCandidateId] = useState('')
  const [positionId, setPositionId] = useState('')
  const [rawJobDescription, setRawJobDescription] = useState('')
  const [useRawDescription, setUseRawDescription] = useState(false)
  const [maxIterations, setMaxIterations] = useState(3)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      let request = {
        candidate_id: candidateId,
        max_iterations: maxIterations,
      }

      if (useRawDescription) {
        if (!rawJobDescription.trim()) {
          setError('Пожалуйста, укажите описание вакансии')
          setLoading(false)
          return
        }
        request.raw_job_description = rawJobDescription
      } else {
        if (!positionId.trim()) {
          setError('Пожалуйста, укажите ID вакансии')
          setLoading(false)
          return
        }
        request.position_id = positionId
      }

      const screening = await apiService.agentMode(request)
      navigate(`/results/${screening.id}`)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to run screening')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2>Запустить отбор</h2>
      <p style={{ color: '#666', marginBottom: '1.5rem' }}>
        Запустите агентную оценку отбора. Система оценит кандидата по вакансии,
        сгенерирует уточняющие вопросы при необходимости и предоставит детальную оценку.
      </p>

      {error && <div className="alert alert-error">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="candidate-id">ID кандидата *</label>
          <input
            id="candidate-id"
            type="text"
            value={candidateId}
            onChange={(e) => setCandidateId(e.target.value)}
            placeholder="Введите ID кандидата из загруженного резюме"
            required
          />
        </div>

        <div className="form-group">
          <label>
            <input
              type="checkbox"
              checked={useRawDescription}
              onChange={(e) => setUseRawDescription(e.target.checked)}
              style={{ marginRight: '0.5rem' }}
            />
            Использовать описание вакансии напрямую (вместо ID вакансии)
          </label>
        </div>

        {useRawDescription ? (
          <div className="form-group">
            <label htmlFor="job-description">Описание вакансии *</label>
            <textarea
              id="job-description"
              value={rawJobDescription}
              onChange={(e) => setRawJobDescription(e.target.value)}
              placeholder="Вставьте описание вакансии здесь"
              required={useRawDescription}
            />
          </div>
        ) : (
          <div className="form-group">
            <label htmlFor="position-id">ID вакансии *</label>
            <input
              id="position-id"
              type="text"
              value={positionId}
              onChange={(e) => setPositionId(e.target.value)}
              placeholder="Введите ID вакансии из созданной вакансии"
              required={!useRawDescription}
            />
          </div>
        )}

        <div className="form-group">
          <label htmlFor="max-iterations">Максимум итераций агентного цикла</label>
          <input
            id="max-iterations"
            type="number"
            min="1"
            max="5"
            value={maxIterations}
            onChange={(e) => setMaxIterations(parseInt(e.target.value))}
          />
          <small style={{ color: '#666', display: 'block', marginTop: '0.25rem' }}>
            Количество итераций для агентного цикла (по умолчанию: 3)
          </small>
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Запуск отбора...' : 'Запустить отбор'}
        </button>
      </form>
    </div>
  )
}

export default Screening
