import { useState } from 'react'
import { scoreSingle, type AppointmentInput, type ScoreResult } from '../lib/api'
import { RiskBadge } from '../components/RiskBadge'
import { ExplanationCard } from '../components/ExplanationCard'

type Scenario = {
  id: string
  title: string
  context: string
  input: AppointmentInput
}

const SCENARIOS: Scenario[] = [
  {
    id: 'cross_emirate',
    title: 'Cross emirate, July afternoon, first visit',
    context: 'Sharjah resident booked at SSMC Abu Dhabi. 2pm in peak summer. New patient, no attendance history.',
    input: {
      appointment_at: '2026-07-15T14:00:00',
      booked_at: '2026-07-08T11:00:00',
      specialty: 'cardiology',
      clinic_area: 'SSMC',
      patient_area: 'al_majaz',
      patient_age_band: '40-64',
      patient_gender: 'm',
      insurance_tier: 'commercial',
      booking_channel: 'phone',
      language_pref: 'ar',
      prior_noshow_count_12mo: 0,
      prior_attended_count_12mo: 0,
      emirate: 'AD',
    },
  },
  {
    id: 'ramadan',
    title: 'Ramadan late afternoon, two prior no shows',
    context: 'Daman Basic patient in Mussafah, 4pm dermatology slot during fasting, two missed appointments in the last year.',
    input: {
      appointment_at: '2026-03-05T16:00:00',
      booked_at: '2026-02-25T10:00:00',
      specialty: 'dermatology',
      clinic_area: 'CCAD',
      patient_area: 'mussafah',
      patient_age_band: '18-39',
      patient_gender: 'f',
      insurance_tier: 'daman_basic',
      booking_channel: 'app',
      language_pref: 'ur',
      prior_noshow_count_12mo: 2,
      prior_attended_count_12mo: 1,
      emirate: 'AD',
    },
  },
  {
    id: 'regular',
    title: 'Tuesday morning, Thiqa regular, twenty attended',
    context: 'Established cardiology patient near the hospital, 9am visit, Thiqa, twenty attended appointments and zero missed.',
    input: {
      appointment_at: '2026-05-12T09:00:00',
      booked_at: '2026-04-28T14:30:00',
      specialty: 'cardiology',
      clinic_area: 'SSMC',
      patient_area: 'al_nahyan',
      patient_age_band: '65+',
      patient_gender: 'm',
      insurance_tier: 'thiqa',
      booking_channel: 'phone',
      language_pref: 'ar',
      prior_noshow_count_12mo: 0,
      prior_attended_count_12mo: 20,
      emirate: 'AD',
    },
  },
]

export function Demo() {
  const [activeId, setActiveId] = useState<string | null>(null)
  const [result, setResult] = useState<ScoreResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function runScenario(scenario: Scenario) {
    setActiveId(scenario.id)
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await scoreSingle(scenario.input)
      setResult(res)
    } catch (err) {
      setError('Could not score that appointment. Try again.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-10">
      <div className="brand-hero">
        <video className="brand-video" autoPlay muted playsInline loop preload="metadata"
               poster="https://umodapwphcxtiijizqll.supabase.co/storage/v1/object/public/surface-videos/noshight-v3.jpg"
               aria-label="Noshight product video">
          <source src="https://umodapwphcxtiijizqll.supabase.co/storage/v1/object/public/surface-videos/noshight-v3.mp4" type="video/mp4" />
        </video>
      </div>
      <header className="space-y-2">
        <h1 className="text-3xl font-medium tracking-tight">See no shows before they happen</h1>
        <p className="text-text-secondary text-base">
          Heuristic risk scoring tuned for UAE clinics. Pick a scenario.
        </p>
      </header>

      <div className="space-y-3">
        {SCENARIOS.map((s) => (
          <button
            key={s.id}
            onClick={() => runScenario(s)}
            className={`w-full text-left bg-surface-raised border rounded-lg p-4 transition-colors hover:border-gold/60 ${
              activeId === s.id ? 'border-gold' : 'border-white/20'
            }`}
          >
            <p className="text-sm font-medium text-text-primary">{s.title}</p>
            <p className="text-xs text-text-secondary mt-1 leading-relaxed">{s.context}</p>
          </button>
        ))}
      </div>

      <div className="min-h-[200px]">
        {loading && (
          <div className="flex items-center justify-center h-32 text-text-secondary text-sm">
            Scoring…
          </div>
        )}
        {error && <p className="text-sm text-risk-very-high">{error}</p>}
        {result && !loading && (
          <div className="space-y-5">
            <div>
              <p className="text-xs text-text-secondary uppercase tracking-wide mb-2">Risk Assessment</p>
              <div className="flex items-center gap-3">
                <RiskBadge band={result.risk_band} />
                <span className="text-3xl font-medium">{(result.probability * 100).toFixed(0)}%</span>
                <span className="text-sm text-text-secondary">likelihood of no show</span>
              </div>
            </div>
            <div className="bg-surface-raised border border-gold/40 rounded-lg p-4">
              <p className="text-xs text-text-secondary uppercase tracking-wide mb-1">Recommended Action</p>
              <p className="text-sm text-gold font-medium">{result.recommended_action}</p>
            </div>
            <ExplanationCard factors={result.top_factors} />
          </div>
        )}
      </div>

      <div className="border-t border-white/20 pt-8 space-y-3">
        <p className="text-base text-text-primary">
          Want this scoring your real patient list?
        </p>
        <p className="text-sm text-text-secondary leading-relaxed">
          Email <a href="mailto:assel@nomoi.ai?subject=Noshight%20pilot" className="text-gold hover:underline">assel@nomoi.ai</a> with your clinic name and a sample week of bookings. We score it, send back the high risk list, and discuss a pilot.
        </p>
      </div>

      <footer className="text-text-secondary text-xs pt-4">
        Heuristic v1 — operational tool, not a clinical decision. Built by NOMOI in Abu Dhabi.
      </footer>
    </div>
  )
}
