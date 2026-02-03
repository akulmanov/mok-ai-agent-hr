import React, { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import apiService from '../services/api'

function Screening() {
  const [candidateId, setCandidateId] = useState('')
  const [positionId, setPositionId] = useState('')
  const [rawJobDescription, setRawJobDescription] = useState('')
  const [useRawDescription, setUseRawDescription] = useState(false)
  const [useTrueAgent, setUseTrueAgent] = useState(false)
  const [maxIterations, setMaxIterations] = useState(3)
  const [goal, setGoal] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [candidates, setCandidates] = useState([])
  const [positions, setPositions] = useState([])
  const [loadingData, setLoadingData] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    loadCandidates()
    loadPositions()
  }, [])

  const loadCandidates = async () => {
    try {
      const data = await apiService.listCandidates({ limit: 100 })
      setCandidates(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error('Error loading candidates:', err)
    } finally {
      setLoadingData(false)
    }
  }

  const loadPositions = async () => {
    try {
      const data = await apiService.listPositions({ limit: 100, is_open: true })
      setPositions(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error('Error loading positions:', err)
    }
  }

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

      let screening
      if (useTrueAgent) {
        // Use True Agent mode
        if (goal.trim()) {
          request.goal = goal.trim()
        }
        screening = await apiService.trueAgentMode(request)
      } else {
        // Use simple agent mode
        screening = await apiService.agentMode(request)
      }
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

      <div className="form-group" style={{ 
        padding: '1rem', 
        backgroundColor: '#f5f5f5', 
        borderRadius: '8px', 
        marginBottom: '1.5rem',
        border: '1px solid #ddd'
      }}>
        <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={useTrueAgent}
            onChange={(e) => setUseTrueAgent(e.target.checked)}
            style={{ marginRight: '0.5rem', width: '18px', height: '18px' }}
          />
          <div>
            <strong>🤖 Использовать True Agent (Автономный режим)</strong>
            <small style={{ display: 'block', color: '#666', marginTop: '0.25rem' }}>
              True Agent использует автономное рассуждение, планирование и адаптацию.
              Работает дольше, но более интеллектуально обрабатывает сложные случаи.
            </small>
          </div>
        </label>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="candidate-id">Кандидат *</label>
          <select
            id="candidate-id"
            value={candidateId}
            onChange={(e) => setCandidateId(e.target.value)}
            required
            disabled={loadingData}
          >
            <option value="">Выберите кандидата...</option>
            {candidates.map((candidate) => {
              const profile = candidate.structured_profile || {}
              const name = profile.name || `Кандидат ${candidate.id.substring(0, 8)}`
              return (
                <option key={candidate.id} value={candidate.id}>
                  {name} ({candidate.id.substring(0, 8)}...)
                </option>
              )
            })}
          </select>
          {!loadingData && candidates.length === 0 && (
            <small style={{ color: '#666', display: 'block', marginTop: '0.25rem' }}>
              Нет кандидатов. <Link to="/cvs">Загрузите резюме</Link>
            </small>
          )}
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
            <label htmlFor="position-id">Вакансия *</label>
            <select
              id="position-id"
              value={positionId}
              onChange={(e) => setPositionId(e.target.value)}
              required={!useRawDescription}
              disabled={loadingData}
            >
              <option value="">Выберите вакансию...</option>
              {positions.map((position) => {
                const title = position.structured_data?.title || `Вакансия ${position.id.substring(0, 8)}`
                return (
                  <option key={position.id} value={position.id}>
                    {title} ({position.id.substring(0, 8)}...)
                  </option>
                )
              })}
            </select>
            {!loadingData && positions.length === 0 && (
              <small style={{ color: '#666', display: 'block', marginTop: '0.25rem' }}>
                Нет открытых вакансий. <Link to="/positions">Создайте вакансию</Link>
              </small>
            )}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="max-iterations">
            Максимум итераций агентного цикла
          </label>
          <input
            id="max-iterations"
            type="number"
            min="1"
            max={useTrueAgent ? "10" : "5"}
            value={maxIterations}
            onChange={(e) => setMaxIterations(parseInt(e.target.value))}
          />
          <small style={{ color: '#666', display: 'block', marginTop: '0.25rem' }}>
            {useTrueAgent 
              ? 'Количество итераций для True Agent (рекомендуется: 5-10)' 
              : 'Количество итераций для простого агента (по умолчанию: 3)'}
          </small>
        </div>

        {useTrueAgent && (
          <div className="form-group">
            <label htmlFor="goal">Цель для агента (опционально)</label>
            <textarea
              id="goal"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="Например: Оценить кандидата с высокой уверенностью и разрешить все неопределенности"
              rows="2"
            />
            <small style={{ color: '#666', display: 'block', marginTop: '0.25rem' }}>
              Кастомная цель для True Agent. Если не указано, используется цель по умолчанию.
            </small>
          </div>
        )}

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Запуск отбора...' : 'Запустить отбор'}
        </button>
      </form>
    </div>
  )
}

export default Screening
