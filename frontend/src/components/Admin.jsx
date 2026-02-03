import React, { useState } from 'react'
import apiService from '../services/api'

function Admin() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  const handleClearData = async () => {
    if (!window.confirm('⚠️ ВНИМАНИЕ: Это удалит ВСЕ данные (вакансии, кандидаты, отборы). Продолжить?')) {
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const result = await apiService.clearAllData()
      setSuccess(result.message || 'Все данные успешно удалены')
      setTimeout(() => {
        window.location.reload()
      }, 2000)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Не удалось очистить данные')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateData = async () => {
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const result = await apiService.generateSampleData()
      setSuccess(result.message || `Создано ${result.positions_count} вакансий и ${result.candidates_count} кандидатов`)
      setTimeout(() => {
        window.location.reload()
      }, 2000)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Не удалось сгенерировать данные')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="dashboard">
      <div className="card">
        <h2>Администрирование</h2>
        <p className="dashboard-intro">
          Управление данными системы. Очистка и генерация тестовых данных.
        </p>
      </div>

      <div className="card">
        <h3>Очистка данных</h3>
        <p style={{ color: '#64748b', marginBottom: '1rem' }}>
          Удалить все вакансии, кандидатов и результаты отборов из базы данных.
        </p>
        <button
          className="btn btn-primary"
          onClick={handleClearData}
          disabled={loading}
          style={{ background: '#ef4444' }}
        >
          {loading ? 'Очистка...' : 'Очистить все данные'}
        </button>
      </div>

      <div className="card">
        <h3>Генерация тестовых данных</h3>
        <p style={{ color: '#64748b', marginBottom: '1rem' }}>
          Создать 12 вакансий и 12 кандидатов с резюме на русском языке для тестирования системы.
        </p>
        <button
          className="btn btn-primary"
          onClick={handleGenerateData}
          disabled={loading}
        >
          {loading ? 'Генерация...' : 'Сгенерировать тестовые данные'}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}
    </div>
  )
}

export default Admin
