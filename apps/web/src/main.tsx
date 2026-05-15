import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'
import { Layout } from './components/Layout'
import { AccessGate } from './components/AccessGate'
import { Demo } from './routes/Demo'
import { ScoreOne } from './routes/ScoreOne'
import { ScoreBulk } from './routes/ScoreBulk'
import { Dashboard } from './routes/Dashboard'
import { Review } from './routes/Review'
import { Audit } from './routes/Audit'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Demo />} />
          <Route path="/app" element={<Navigate to="/" replace />} />
          <Route path="/score" element={<Navigate to="/" replace />} />
          <Route path="/manual" element={<AccessGate><ScoreOne /></AccessGate>} />
          <Route path="/bulk" element={<AccessGate><ScoreBulk /></AccessGate>} />
          <Route path="/dashboard" element={<AccessGate><Dashboard /></AccessGate>} />
          <Route path="/review" element={<AccessGate><Review /></AccessGate>} />
          <Route path="/audit" element={<AccessGate><Audit /></AccessGate>} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
