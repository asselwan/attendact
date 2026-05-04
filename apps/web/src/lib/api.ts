const BASE = import.meta.env.VITE_API_URL || ''

export interface ScoreResult {
  appointment_id: string
  probability: number
  risk_band: 'low' | 'moderate' | 'high' | 'very_high'
  top_factors: Array<{
    feature: string
    value: string | number | boolean
    contribution: number
    plain_text: string
  }>
  model_version: string
  recommended_action: string
  distance_km?: number
}

export interface AppointmentInput {
  appointment_at: string
  booked_at: string
  specialty: string
  clinic_area?: string
  patient_area?: string
  patient_age_band: string
  patient_gender: string
  insurance_tier: string
  booking_channel: string
  language_pref: string
  prior_noshow_count_12mo: number
  prior_attended_count_12mo: number
  emirate: string
}

export async function scoreSingle(input: AppointmentInput): Promise<ScoreResult> {
  const res = await fetch(`${BASE}/api/score/single`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!res.ok) throw new Error(`Score failed: ${res.status}`)
  return res.json()
}

export async function scoreBulk(file: File): Promise<Blob> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/api/score/bulk`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) throw new Error(`Bulk score failed: ${res.status}`)
  return res.blob()
}

export interface Insight {
  title: string
  body: string
  category: 'scheduling' | 'capacity' | 'risk_pattern' | 'intervention'
  confidence: 'high' | 'medium' | 'low'
}

export interface InsightsResponse {
  insights: Insight[]
  total_scores_analysed: number
}

export async function fetchInsights(): Promise<InsightsResponse> {
  const res = await fetch(`${BASE}/api/insights/generate`)
  if (!res.ok) throw new Error(`Insights failed: ${res.status}`)
  return res.json()
}

// --- Outcomes & Self-Learning ---

export interface PredictionError {
  appointment_id: string
  specialty: string
  risk_band: string
  probability: number
  outcome: string
  error_type: 'false_negative' | 'false_positive'
  top_factors: Array<{ feature: string; contribution: number; plain_text: string }>
  clinic_area: string
  patient_area: string
  distance_km: number | null
}

export interface CalibrationBand {
  count: number
  avg_predicted_probability: number
  actual_noshow_rate: number
  calibration_error: number
}

export interface ReviewResponse {
  total_with_outcomes: number
  total_errors: number
  false_negatives: number
  false_positives: number
  errors: PredictionError[]
  calibration: {
    total_labeled: number
    bands: Record<string, CalibrationBand>
  }
}

export interface OutcomeInput {
  appointment_id: string
  outcome: 'attended' | 'no_show' | 'cancelled'
}

export async function fetchReview(): Promise<ReviewResponse> {
  const res = await fetch(`${BASE}/api/outcomes/review`)
  if (!res.ok) throw new Error(`Review failed: ${res.status}`)
  return res.json()
}

export async function recordOutcomes(outcomes: OutcomeInput[]): Promise<{ recorded: number; not_found: number }> {
  const res = await fetch(`${BASE}/api/outcomes/record`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ outcomes }),
  })
  if (!res.ok) throw new Error(`Outcome recording failed: ${res.status}`)
  return res.json()
}

export async function triggerCalibration(): Promise<{
  samples_used: number
  overall_calibration_error: number
  recommendation: string
  effective_weights: Record<string, number>
}> {
  const res = await fetch(`${BASE}/api/outcomes/calibrate`, { method: 'POST' })
  if (!res.ok) throw new Error(`Calibration failed: ${res.status}`)
  return res.json()
}

export async function fetchMetrics(): Promise<{
  total_scored: number
  total_with_outcomes: number
  calibration_by_band: Record<string, CalibrationBand>
}> {
  const res = await fetch(`${BASE}/api/outcomes/metrics`)
  if (!res.ok) throw new Error(`Metrics failed: ${res.status}`)
  return res.json()
}

export async function resetDashboard(): Promise<{ cleared: number }> {
  const res = await fetch(`${BASE}/api/insights/reset`, { method: 'POST' })
  if (!res.ok) throw new Error(`Reset failed: ${res.status}`)
  return res.json()
}
