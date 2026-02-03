import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import apiService from '../services/api'
import Pagination from './Pagination'
import './Dashboard.css'

function Positions() {
  const [positions, setPositions] = useState([])
  const [filteredPositions, setFilteredPositions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [createMode, setCreateMode] = useState('text')
  const [description, setDescription] = useState('')
  const [file, setFile] = useState(null)
  const [creating, setCreating] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [itemsPerPage] = useState(10)
  const navigate = useNavigate()

  useEffect(() => {
    loadPositions()
  }, [])

  useEffect(() => {
    filterPositions()
  }, [positions, searchTerm, statusFilter])

  const loadPositions = async () => {
    try {
      setLoading(true)
      const data = await apiService.listPositions({ limit: 1000 })
      setPositions(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Не удалось загрузить вакансии')
    } finally {
      setLoading(false)
    }
  }

  const filterPositions = () => {
    let filtered = positions
    
    if (searchTerm) {
      filtered = filtered.filter(position => {
        const title = position.structured_data?.title || ''
        const searchLower = searchTerm.toLowerCase()
        return title.toLowerCase().includes(searchLower) ||
               position.id.toLowerCase().includes(searchLower)
      })
    }
    
    if (statusFilter === 'open') {
      filtered = filtered.filter(p => p.is_open)
    } else if (statusFilter === 'closed') {
      filtered = filtered.filter(p => !p.is_open)
    }
    
    setFilteredPositions(filtered)
    setCurrentPage(1)
  }

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
      setError(null)
    }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setCreating(true)
    setError(null)

    try {
      let text = description
      if (createMode === 'file' && file) {
        const reader = new FileReader()
        text = await new Promise((resolve, reject) => {
          reader.onload = (e) => resolve(e.target.result)
          reader.onerror = reject
          reader.readAsText(file)
        })
      }

      if (!text.trim()) {
        setError('Пожалуйста, введите описание вакансии или загрузите файл')
        setCreating(false)
        return
      }

      await apiService.createPosition(text)
      setDescription('')
      setFile(null)
      await loadPositions()
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Не удалось создать вакансию')
    } finally {
      setCreating(false)
    }
  }

  const handleToggleStatus = async (positionId, currentStatus) => {
    try {
      await apiService.updatePosition(positionId, { is_open: !currentStatus })
      await loadPositions()
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Не удалось обновить статус')
    }
  }

  const totalPages = Math.ceil(filteredPositions.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const currentPositions = filteredPositions.slice(startIndex, endIndex)

  return (
    <div className="dashboard">
      <div className="card">
        <h2>Вакансии</h2>
        <p className="dashboard-intro">
          Создавайте новые вакансии или просматривайте существующие. Вы можете создать вакансию из текста или загрузить файл.
        </p>
      </div>

      <div className="card">
        <h3>Создать новую вакансию</h3>
        
        <div style={{ marginBottom: '1rem', display: 'flex', gap: '1rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
            <input
              type="radio"
              value="text"
              checked={createMode === 'text'}
              onChange={(e) => setCreateMode(e.target.value)}
              style={{ marginRight: '0.5rem' }}
            />
            Ввести текст
          </label>
          <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
            <input
              type="radio"
              value="file"
              checked={createMode === 'file'}
              onChange={(e) => setCreateMode(e.target.value)}
              style={{ marginRight: '0.5rem' }}
            />
            Загрузить файл
          </label>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleCreate}>
          {createMode === 'text' ? (
            <div className="form-group">
              <label htmlFor="description">Описание вакансии</label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Вставьте описание вакансии здесь..."
                rows="10"
                required
              />
            </div>
          ) : (
            <div className="form-group">
              <label htmlFor="position-file">Файл с описанием вакансии (TXT)</label>
              <input
                id="position-file"
                type="file"
                accept=".txt"
                onChange={handleFileChange}
                required
              />
              {file && (
                <div style={{ marginTop: '0.5rem', color: '#64748b', fontSize: '0.875rem' }}>
                  Выбрано: {file.name} ({(file.size / 1024).toFixed(2)} КБ)
                </div>
              )}
            </div>
          )}

          <button type="submit" className="btn btn-primary" disabled={creating || (createMode === 'text' && !description.trim()) || (createMode === 'file' && !file)}>
            {creating ? 'Создание...' : 'Создать вакансию'}
          </button>
        </form>
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
          <h3 style={{ margin: 0 }}>Список вакансий ({filteredPositions.length})</h3>
          <div className="filters">
            <div className="filter-group">
              <input
                type="text"
                placeholder="Поиск по названию или ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ width: '250px' }}
              />
            </div>
            <div className="filter-group">
              <label>Статус:</label>
              <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                <option value="all">Все</option>
                <option value="open">Открытые</option>
                <option value="closed">Закрытые</option>
              </select>
            </div>
          </div>
        </div>

        {loading && <div className="loading"><div className="spinner"></div></div>}
        {error && <div className="alert alert-error">{error}</div>}
        
        {!loading && !error && (
          <>
            {currentPositions.length === 0 ? (
              <p style={{ color: '#64748b', textAlign: 'center', padding: '2rem' }}>
                {searchTerm || statusFilter !== 'all' ? 'Вакансии не найдены по вашим фильтрам' : 'Вакансий пока нет. Создайте первую вакансию выше.'}
              </p>
            ) : (
              <>
                <div className="cards-grid">
                  {currentPositions.map((position) => {
                    const title = position.structured_data?.title || 'Без названия'
                    const requirements = position.structured_data?.requirements || []
                    return (
                      <div key={position.id} className="card-item" onClick={() => navigate(`/positions/${position.id}`)}>
                        <div className="card-item-header">
                          <div style={{ flex: 1 }}>
                            <h4 className="card-item-title">{title}</h4>
                            <div className="card-item-meta" style={{ marginTop: '0.5rem' }}>
                              Требований: {requirements.length} | 
                              Обязательных: {requirements.filter(r => r.category === 'must').length}
                            </div>
                          </div>
                          <span className={`badge ${position.is_open ? 'badge-pass' : 'badge-reject'}`}>
                            {position.is_open ? 'ОТКРЫТА' : 'ЗАКРЫТА'}
                          </span>
                        </div>
                        <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
                          <button
                            className="btn btn-sm btn-secondary"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleToggleStatus(position.id, position.is_open)
                            }}
                          >
                            {position.is_open ? 'Закрыть' : 'Открыть'}
                          </button>
                        </div>
                        <div style={{ marginTop: '0.75rem', fontSize: '0.75rem', color: '#94a3b8' }}>
                          Создано: {new Date(position.created_at).toLocaleDateString('ru-RU')}
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

export default Positions
