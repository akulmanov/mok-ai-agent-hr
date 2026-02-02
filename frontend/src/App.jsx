import React, { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import JobPosting from './components/JobPosting'
import CVUpload from './components/CVUpload'
import Screening from './components/Screening'
import Results from './components/Results'
import Dashboard from './components/Dashboard'
import Candidates from './components/Candidates'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <div className="nav-container">
            <Link to="/" className="nav-logo">
              <h1>🎯 Агент HR-Отбора</h1>
            </Link>
            <div className="nav-links">
              <Link to="/">Панель управления</Link>
              <Link to="/candidates">Кандидаты</Link>
              <Link to="/job-posting">Создать вакансию</Link>
              <Link to="/upload-cv">Загрузить резюме</Link>
              <Link to="/screening">Запустить отбор</Link>
            </div>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/candidates" element={<Candidates />} />
            <Route path="/job-posting" element={<JobPosting />} />
            <Route path="/upload-cv" element={<CVUpload />} />
            <Route path="/screening" element={<Screening />} />
            <Route path="/results/:screeningId" element={<Results />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
