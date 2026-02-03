import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import apiService from '../services/api'
import Pagination from './Pagination'
import './Dashboard.css'

function Candidates() {
  const [candidates, setCandidates] = useState([])
  const [filteredCandidates, setFilteredCandidates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [searchTerm, setSearchTerm] = useState('')
  const [itemsPerPage] = useState(10)

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
      setError(err.response?.data?.detail || err.message || 'Не удалось загрузить кандидатов')
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

  const getContactInfo = (candidate) => {
    const profile = candidate.structured_profile || {}
    return {
      name: profile.name || 'Не указано',
      email: profile.email || null,
      phone: profile.phone || null,
      telegram: profile.telegram || null,
      whatsapp: profile.whatsapp || null
    }
  }

  const totalPages = Math.ceil(filteredCandidates.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const currentCandidates = filteredCandidates.slice(startIndex, endIndex)
  const navigate = useNavigate()

  return (
    <div className="dashboard">
      <div className="card">
        <h2>Кандидаты</h2>
        <p className="dashboard-intro">
          Список всех кандидатов, загруженных в систему. Просматривайте контактную информацию и историю отборов.
        </p>
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
          <h3 style={{ margin: 0 }}>Список кандидатов ({filteredCandidates.length})</h3>
          <div className="filter-group">
            <input
              type="text"
              placeholder="Поиск по имени, email или ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ width: '300px', padding: '0.5rem 1rem' }}
            />
          </div>
        </div>

        {loading && <div className="loading"><div className="spinner"></div></div>}
        {error && <div className="alert alert-error">{error}</div>}
        
        {!loading && !error && (
          <>
            {currentCandidates.length === 0 ? (
              <p style={{ color: '#64748b', textAlign: 'center', padding: '2rem' }}>
                {searchTerm ? 'Кандидаты не найдены по вашему запросу' : 'Кандидатов пока нет. Загрузите резюме, чтобы начать.'}
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
                          {contact.phone && (
                            <div style={{ marginBottom: '0.5rem', fontSize: '0.875rem', color: '#64748b' }}>
                              📱 {contact.phone}
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

export default Candidates
