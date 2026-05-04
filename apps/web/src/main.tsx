import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'
import { Layout } from './components/Layout'
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
          <Route path="/" element={<Navigate to="/score" replace />} />
          <Route path="/score" element={<Demo />} />
          <Route path="/manual" element={<ScoreOne />} />
          <Route path="/bulk" element={<ScoreBulk />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/review" element={<Review />} />
          <Route path="/audit" element={<Audit />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
