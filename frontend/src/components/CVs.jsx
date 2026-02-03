import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import apiService from '../services/api'
import Pagination from './Pagination'
import './Dashboard.css'

function CVs() {
  const [candidates, setCandidates] = useState([])
  const [filteredCandidates, setFilteredCandidates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [uploadMode, setUploadMode] = useState('file')
  const [file, setFile] = useState(null)
  const [rawText, setRawText] = useState('')
  const [uploading, setUploading] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [searchTerm, setSearchTerm] = useState('')
  const [itemsPerPage] = useState(10)
  const navigate = useNavigate()

  useEffect(() => {
    loadCandidates()
  }, [])

  useEffect(() => {
    filterCandidates()
  }, [candidates, searchTerm])

  const loadCandidates = async () => {
    try {
      setLoading(true)
      const data = await apiService.listCandidates({ limit: 1000 })
      setCandidates(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Не удалось загрузить резюме')
    } finally {
      setLoading(false)
    }
  }

  const filterCandidates = () => {
    let filtered = candidates
    
    if (searchTerm) {
      filtered = candidates.filter(candidate => {
        const profile = candidate.structured_profile || {}
        const name = profile.name || ''
        const email = profile.email || ''
        const searchLower = searchTerm.toLowerCase()
        return name.toLowerCase().includes(searchLower) || 
               email.toLowerCase().includes(searchLower) ||
               candidate.id.toLowerCase().includes(searchLower)
      })
    }
    
    setFilteredCandidates(filtered)
    setCurrentPage(1)
  }

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

  const handleUpload = async (e) => {
    e.preventDefault()
    setUploading(true)
    setError(null)

    try {
      let candidate
      if (uploadMode === 'file') {
        if (!file) {
          setError('Пожалуйста, выберите файл')
          setUploading(false)
          return
        }
        candidate = await apiService.uploadCV(file)
      } else {
        if (!rawText.trim()) {
          setError('Пожалуйста, введите текст резюме')
          setUploading(false)
          return
        }
        candidate = await apiService.uploadCV(null, rawText)
      }
      
      setFile(null)
      setRawText('')
      await loadCandidates()
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Не удалось загрузить резюме')
    } finally {
      setUploading(false)
    }
  }

  const getContactInfo = (candidate) => {
    const profile = candidate.structured_profile || {}
    return {
      name: profile.name || 'Не указано',
      email: profile.email || null
    }
  }

  const totalPages = Math.ceil(filteredCandidates.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const currentCandidates = filteredCandidates.slice(startIndex, endIndex)

  return (
    <div className="dashboard">
      <div className="card">
        <h2>Резюме (CVs)</h2>
        <p className="dashboard-intro">
          Загружайте резюме кандидатов или просматривайте уже загруженные. Вы можете загрузить файл или вставить текст напрямую.
        </p>
      </div>

      <div className="card">
        <h3>Загрузить новое резюме</h3>
        
        <div style={{ marginBottom: '1rem', display: 'flex', gap: '1rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
            <input
              type="radio"
              value="file"
              checked={uploadMode === 'file'}
              onChange={(e) => setUploadMode(e.target.value)}
              style={{ marginRight: '0.5rem' }}
            />
            Загрузить файл
          </label>
          <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
            <input
              type="radio"
              value="text"
              checked={uploadMode === 'text'}
              onChange={(e) => setUploadMode(e.target.value)}
              style={{ marginRight: '0.5rem' }}
            />
            Вставить текст
          </label>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleUpload}>
          {uploadMode === 'file' ? (
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
                <div style={{ marginTop: '0.5rem', color: '#64748b', fontSize: '0.875rem' }}>
                  Выбрано: {file.name} ({(file.size / 1024).toFixed(2)} КБ)
                </div>
              )}
            </div>
          ) : (
            <div className="form-group">
              <label htmlFor="cv-text">Текст резюме</label>
              <textarea
                id="cv-text"
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                placeholder="Вставьте текст резюме здесь..."
                rows="10"
                required
              />
            </div>
          )}

          <button type="submit" className="btn btn-primary" disabled={uploading || (uploadMode === 'file' && !file) || (uploadMode === 'text' && !rawText.trim())}>
            {uploading ? 'Загрузка...' : 'Загрузить резюме'}
          </button>
        </form>
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
          <h3 style={{ margin: 0 }}>Загруженные резюме ({filteredCandidates.length})</h3>
          <div className="filter-group">
            <input
              type="text"
              placeholder="Поиск по имени, email или ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ width: '300px' }}
            />
          </div>
        </div>

        {loading && <div className="loading"><div className="spinner"></div></div>}
        {error && <div className="alert alert-error">{error}</div>}
        
        {!loading && !error && (
          <>
            {currentCandidates.length === 0 ? (
              <p style={{ color: '#64748b', textAlign: 'center', padding: '2rem' }}>
                {searchTerm ? 'Резюме не найдены по вашему запросу' : 'Резюме пока нет. Загрузите первое резюме выше.'}
              </p>
            ) : (
              <>
                <div className="cards-grid">
                  {currentCandidates.map((candidate) => {
                    const contact = getContactInfo(candidate)
                    return (
                      <div key={candidate.id} className="card-item" onClick={() => navigate(`/candidates/${candidate.id}`)}>
                        <div className="card-item-header">
                          <div>
                            <h4 className="card-item-title">{contact.name}</h4>
                            <div className="card-item-meta">
                              ID: {candidate.id.substring(0, 12)}...
                            </div>
                          </div>
                        </div>
                        <div style={{ marginTop: '1rem' }}>
                          {contact.email && (
                            <div style={{ marginBottom: '0.5rem', fontSize: '0.875rem', color: '#64748b' }}>
                              📧 {contact.email}
                            </div>
                          )}
                          <div style={{ marginTop: '0.75rem', fontSize: '0.75rem', color: '#94a3b8' }}>
                            Загружено: {new Date(candidate.created_at).toLocaleDateString('ru-RU')} | 
                            Тип: {candidate.cv_file_type?.toUpperCase() || 'N/A'}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
                
                {totalPages > 1 && (
                  <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    onPageChange={setCurrentPage}
                  />
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default CVs
