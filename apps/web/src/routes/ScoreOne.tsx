import { useState } from 'react'
import { scoreSingle, type AppointmentInput, type ScoreResult } from '../lib/api'
import { RiskBadge } from '../components/RiskBadge'
import { ExplanationCard } from '../components/ExplanationCard'

const SPECIALTIES = [
  'cardiology', 'dermatology', 'endocrinology', 'ent', 'gastroenterology',
  'general', 'neurology', 'obstetrics', 'oncology', 'ophthalmology',
  'orthopedics', 'pediatrics', 'psychiatry', 'pulmonology', 'urology',
]

const EMIRATES = ['AD', 'DXB', 'SHJ', 'AJM', 'RAK', 'FUJ', 'UAQ']

export function ScoreOne() {
  const [result, setResult] = useState<ScoreResult | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setLoading(true)
    const fd = new FormData(e.currentTarget)
    const input: AppointmentInput = {
      appointment_at: fd.get('appointment_at') as string,
      booked_at: fd.get('booked_at') as string,
      specialty: fd.get('specialty') as string,
      clinic_location: fd.get('clinic_location') as string || undefined,
      patient_age_band: fd.get('patient_age_band') as string,
      patient_gender: fd.get('patient_gender') as string,
      insurance_tier: fd.get('insurance_tier') as string,
      booking_channel: fd.get('booking_channel') as string,
      language_pref: fd.get('language_pref') as string,
      prior_noshow_count_12mo: Number(fd.get('prior_noshow_count_12mo')),
      prior_attended_count_12mo: Number(fd.get('prior_attended_count_12mo')),
      distance_km: fd.get('distance_km') ? Number(fd.get('distance_km')) : undefined,
      emirate: fd.get('emirate') as string,
    }
    try {
      const res = await scoreSingle(input)
      setResult(res)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div>
        <h2 className="text-xl font-medium mb-4">Score Appointment</h2>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Appointment date/time" name="appointment_at" type="datetime-local" required />
            <Field label="Booked date/time" name="booked_at" type="datetime-local" required />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Select label="Specialty" name="specialty" options={SPECIALTIES} />
            <Select label="Emirate" name="emirate" options={EMIRATES} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Select label="Age band" name="patient_age_band" options={['0-17', '18-39', '40-64', '65+']} />
            <Select label="Gender" name="patient_gender" options={['m', 'f', 'unknown']} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Select label="Insurance tier" name="insurance_tier" options={['thiqa', 'daman_basic', 'daman_enhanced', 'commercial', 'self_pay']} />
            <Select label="Booking channel" name="booking_channel" options={['app', 'web', 'phone', 'walk_in']} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Select label="Language preference" name="language_pref" options={['en', 'ar', 'ur', 'tl', 'other']} />
            <Field label="Distance (km)" name="distance_km" type="number" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Field label="No shows (12mo)" name="prior_noshow_count_12mo" type="number" defaultValue="0" />
            <Field label="Attended (12mo)" name="prior_attended_count_12mo" type="number" defaultValue="0" />
          </div>
          <Field label="Clinic location" name="clinic_location" />
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gold hover:bg-gold-dim text-surface font-medium py-2 px-4 rounded transition-colors disabled:opacity-50"
          >
            {loading ? 'Scoring...' : 'Score Appointment'}
          </button>
        </form>
      </div>

      <div>
        {result && (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <RiskBadge band={result.risk_band} />
              <span className="text-2xl font-medium">
                {(result.probability * 100).toFixed(1)}%
              </span>
            </div>
            <p className="text-sm text-text-secondary">
              Model: {result.model_version}
            </p>
            <div className="bg-surface-raised border border-white/5 rounded-lg p-4">
              <p className="text-sm text-gold">{result.recommended_action}</p>
            </div>
            <ExplanationCard factors={result.top_factors} />
          </div>
        )}
        {!result && (
          <div className="flex items-center justify-center h-full text-text-secondary text-sm">
            Score an appointment to see the risk assessment
          </div>
        )}
      </div>
    </div>
  )
}

function Field({ label, ...props }: { label: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="block">
      <span className="text-xs text-text-secondary">{label}</span>
      <input
        {...props}
        className="mt-0.5 w-full bg-surface-raised border border-white/10 rounded px-3 py-1.5 text-sm text-text-primary focus:border-gold focus:outline-none"
      />
    </label>
  )
}

function Select({ label, name, options }: { label: string; name: string; options: string[] }) {
  return (
    <label className="block">
      <span className="text-xs text-text-secondary">{label}</span>
      <select
        name={name}
        className="mt-0.5 w-full bg-surface-raised border border-white/10 rounded px-3 py-1.5 text-sm text-text-primary focus:border-gold focus:outline-none"
      >
        {options.map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
    </label>
  )
}
