import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import apiService from '../services/api'

function CVUpload() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [candidateId, setCandidateId] = useState(null)
  const navigate = useNavigate()

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      const ext = selectedFile.name.split('.').pop().toLowerCase()
      if (['pdf', 'docx', 'txt'].includes(ext)) {
        setFile(selectedFile)
        setError(null)
      } else {
        setError('Неподдерживаемый тип файла. Пожалуйста, загрузите файлы PDF, DOCX или TXT.')
        setFile(null)
      }
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) {
        setError('Пожалуйста, выберите файл')
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const candidate = await apiService.uploadCV(file)
      setCandidateId(candidate.id)
      setSuccess(`Резюме успешно загружено! ID кандидата: ${candidate.id}`)
      setFile(null)
      setTimeout(() => {
        navigate('/')
      }, 3000)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to upload CV')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2>Загрузить резюме</h2>
      <p style={{ color: '#666', marginBottom: '1.5rem' }}>
        Загрузите резюме кандидата в формате PDF, DOCX или TXT. Система извлечет структурированную информацию профиля.
      </p>

      {error && <div className="alert alert-error">{error}</div>}
      {success && (
        <div className="alert alert-success">
          {success}
          {candidateId && (
            <div style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>
              ID кандидата: <strong>{candidateId}</strong>
            </div>
          )}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="cv-file">Файл резюме (PDF, DOCX или TXT)</label>
          <input
            id="cv-file"
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={handleFileChange}
            required
          />
          {file && (
            <div style={{ marginTop: '0.5rem', color: '#666', fontSize: '0.875rem' }}>
              Выбрано: {file.name} ({(file.size / 1024).toFixed(2)} КБ)
            </div>
          )}
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading || !file}>
          {loading ? 'Загрузка...' : 'Загрузить резюме'}
        </button>
      </form>
    </div>
  )
}

export default CVUpload
