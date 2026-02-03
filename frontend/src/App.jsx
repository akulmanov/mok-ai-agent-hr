import React, { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import Positions from './components/Positions'
import PositionDetail from './components/PositionDetail'
import CVs from './components/CVs'
import Screening from './components/Screening'
import Results from './components/Results'
import Dashboard from './components/Dashboard'
import Candidates from './components/Candidates'
import CandidateDetail from './components/CandidateDetail'
import Admin from './components/Admin'
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
              <Link to="/positions">Вакансии</Link>
              <Link to="/cvs">Резюме</Link>
              <Link to="/screening">Запустить отбор</Link>
              <Link to="/admin">Администрирование</Link>
            </div>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/candidates" element={<Candidates />} />
            <Route path="/candidates/:candidateId" element={<CandidateDetail />} />
            <Route path="/positions" element={<Positions />} />
            <Route path="/positions/:positionId" element={<PositionDetail />} />
            <Route path="/cvs" element={<CVs />} />
            <Route path="/screening" element={<Screening />} />
            <Route path="/results/:screeningId" element={<Results />} />
            <Route path="/admin" element={<Admin />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
