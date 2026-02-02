import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import apiService from '../services/api'

function Results() {
  const { screeningId } = useParams()
  const [screening, setScreening] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [channels, setChannels] = useState(null)
  const [sending, setSending] = useState(false)
  const [sendSuccess, setSendSuccess] = useState(null)
  const [sendError, setSendError] = useState(null)

  useEffect(() => {
    loadScreening()
  }, [screeningId])

  const loadScreening = async () => {
    try {
      setLoading(true)
      const data = await apiService.getScreening(screeningId)
      setScreening(data)
      
      // Load candidate channels
      if (data.candidate_id) {
        try {
          const channelsData = await apiService.getCandidateChannels(data.candidate_id)
          setChannels(channelsData)
        } catch (err) {
          console.error('Failed to load channels:', err)
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load screening')
    } finally {
      setLoading(false)
    }
  }

  const handleSendReview = async (channel) => {
    if (!screening) return
    
    setSending(true)
    setSendSuccess(null)
    setSendError(null)
    
    try {
      const result = await apiService.sendReviewResult(screeningId, channel)
      setSendSuccess(result.message || `Результат отправлен через ${channel}`)
    } catch (err) {
      setSendError(err.response?.data?.detail || err.message || 'Не удалось отправить результат')
    } finally {
      setSending(false)
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

  const getCategoryClass = (category) => {
    switch (category) {
      case 'must':
        return 'must'
      case 'nice':
        return 'nice'
      case 'bonus':
        return 'bonus'
      default:
        return ''
    }
  }

  if (loading) {
    return (
      <div className="card">
        <div className="loading">
          <div className="spinner"></div>
          <p>Загрузка результатов отбора...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card">
        <div className="alert alert-error">{error}</div>
      </div>
    )
  }

  if (!screening) {
    return (
      <div className="card">
        <div className="alert alert-error">Отбор не найден</div>
      </div>
    )
  }

  return (
    <div className="results">
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2>Результаты отбора</h2>
          <span className={`badge ${getBadgeClass(screening.decision)}`}>
            {screening.decision === 'pass' ? 'ПРИНЯТ' : screening.decision === 'hold' ? 'НА РАССМОТРЕНИИ' : 'ОТКЛОНЕН'}
          </span>
        </div>

        <div className="score-display">
          {(screening.score * 100).toFixed(1)}%
        </div>

        <div style={{ textAlign: 'center', color: '#666', marginBottom: '2rem' }}>
          <p>Версия: {screening.version}</p>
          <p>Создано: {new Date(screening.created_at).toLocaleString('ru-RU')}</p>
        </div>
      </div>

      {screening.requirement_breakdown && screening.requirement_breakdown.length > 0 && (
        <div className="card">
          <h2>Детализация требований</h2>
          <div>
            {screening.requirement_breakdown.map((req, idx) => (
              <div key={idx} className={`requirement-item ${getCategoryClass(req.category)}`}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <strong>{req.requirement_text}</strong>
                  <span>
                    Оценка: {req.rating} / 1.0 | Вес: {(req.weight * 100).toFixed(1)}% | 
                    Уверенность: {req.confidence === 'high' ? 'высокая' : req.confidence === 'medium' ? 'средняя' : 'низкая'}
                  </span>
                </div>
                <div style={{ fontSize: '0.875rem', color: '#666' }}>
                  Категория: <strong>{req.category === 'must' ? 'обязательно' : req.category === 'nice' ? 'желательно' : 'бонус'}</strong>
                </div>
                {req.evidence && req.evidence.length > 0 && (
                  <ul className="evidence-list">
                    {req.evidence.map((evidence, eIdx) => (
                      <li key={eIdx}>{evidence}</li>
                    ))}
                  </ul>
                )}
                {req.notes && (
                  <div style={{ marginTop: '0.5rem', fontStyle: 'italic', color: '#666' }}>
                    {req.notes}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid">
        {screening.strengths && screening.strengths.length > 0 && (
          <div className="card">
            <h2>Сильные стороны</h2>
            <ul className="strengths-list">
              {screening.strengths.map((strength, idx) => (
                <li key={idx}>{strength}</li>
              ))}
            </ul>
          </div>
        )}

        {screening.gaps && screening.gaps.length > 0 && (
          <div className="card">
            <h2>Пробелы</h2>
            <ul className="gaps-list">
              {screening.gaps.map((gap, idx) => (
                <li key={idx}>{gap}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {screening.clarification_questions && screening.clarification_questions.length > 0 && (
        <div className="card">
          <h2>Уточняющие вопросы</h2>
          <div className="alert alert-info">
            <p>Следующие вопросы были сгенерированы для уточнения неясной информации:</p>
            <ul style={{ marginTop: '1rem', paddingLeft: '1.5rem' }}>
              {screening.clarification_questions.map((question, idx) => (
                <li key={idx} style={{ margin: '0.5rem 0' }}>{question}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {screening.suggested_interview_questions && screening.suggested_interview_questions.length > 0 && (
        <div className="card">
          <h2>Рекомендуемые вопросы для собеседования</h2>
          <ol style={{ paddingLeft: '1.5rem' }}>
            {screening.suggested_interview_questions.map((question, idx) => (
              <li key={idx} style={{ margin: '0.5rem 0', lineHeight: '1.6' }}>{question}</li>
            ))}
          </ol>
        </div>
      )}

      {screening.candidate_email_draft && (
        <div className="card">
          <h2>Черновик письма</h2>
          <div className="email-preview">
            <div className="subject">Тема: {screening.candidate_email_draft.subject}</div>
            <div className="body">{screening.candidate_email_draft.body}</div>
          </div>
        </div>
      )}

      {channels && channels.available_channels && channels.available_channels.length > 0 && (
        <div className="card">
          <h2>Отправить результат кандидату</h2>
          <div style={{ marginBottom: '1rem' }}>
            <p style={{ color: '#666', marginBottom: '1rem' }}>
              Кандидат: <strong>{channels.candidate_name || 'Не указано'}</strong>
            </p>
            <div style={{ marginBottom: '1rem' }}>
              <strong>Доступные каналы связи:</strong>
              <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                {channels.available_channels.map((channel) => (
                  <li key={channel} style={{ margin: '0.25rem 0' }}>
                    {channel === 'email' ? '📧 Email' : 
                     channel === 'phone' ? '📱 Телефон' :
                     channel === 'telegram' ? '✈️ Telegram' :
                     channel === 'whatsapp' ? '💬 WhatsApp' : channel}: {channels.channels[channel]}
                  </li>
                ))}
              </ul>
            </div>
          </div>
          
          {sendSuccess && (
            <div className="alert alert-success" style={{ marginBottom: '1rem' }}>
              {sendSuccess}
            </div>
          )}
          
          {sendError && (
            <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
              {sendError}
            </div>
          )}
          
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {channels.available_channels.map((channel) => (
              <button
                key={channel}
                onClick={() => handleSendReview(channel)}
                disabled={sending}
                className="btn btn-primary"
                style={{ minWidth: '120px' }}
              >
                {sending ? 'Отправка...' : 
                 channel === 'email' ? '📧 Отправить Email' :
                 channel === 'phone' ? '📱 Отправить SMS' :
                 channel === 'telegram' ? '✈️ Отправить в Telegram' :
                 channel === 'whatsapp' ? '💬 Отправить в WhatsApp' : `Отправить ${channel}`}
              </button>
            ))}
          </div>
        </div>
      )}

      {screening.audit_trail && (
        <div className="card">
          <h2>Журнал аудита</h2>
          <div style={{ background: '#f8f9fa', padding: '1rem', borderRadius: '8px' }}>
            <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '0.875rem' }}>
              {JSON.stringify(screening.audit_trail, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}

export default Results
