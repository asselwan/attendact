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
}

export interface AppointmentInput {
  appointment_at: string
  booked_at: string
  specialty: string
  clinic_location?: string
  patient_age_band: string
  patient_gender: string
  insurance_tier: string
  booking_channel: string
  language_pref: string
  prior_noshow_count_12mo: number
  prior_attended_count_12mo: number
  distance_km?: number
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
