import { useState } from 'react'
import { scoreSingle, type AppointmentInput, type ScoreResult } from '../lib/api'
import { RiskBadge } from '../components/RiskBadge'
import { ExplanationCard } from '../components/ExplanationCard'

const SPECIALTIES = [
  { value: 'cardiology', label: 'Cardiology' },
  { value: 'dermatology', label: 'Dermatology' },
  { value: 'endocrinology', label: 'Endocrinology' },
  { value: 'ent', label: 'Ear, Nose and Throat' },
  { value: 'gastroenterology', label: 'Gastroenterology' },
  { value: 'general', label: 'General Practice' },
  { value: 'neurology', label: 'Neurology' },
  { value: 'obstetrics', label: 'Obstetrics and Gynaecology' },
  { value: 'oncology', label: 'Oncology' },
  { value: 'ophthalmology', label: 'Ophthalmology' },
  { value: 'orthopedics', label: 'Orthopedics' },
  { value: 'pediatrics', label: 'Pediatrics' },
  { value: 'psychiatry', label: 'Psychiatry' },
  { value: 'pulmonology', label: 'Pulmonology' },
  { value: 'urology', label: 'Urology' },
]

const CLINICS = [
  { value: 'SSMC', label: 'Sheikh Shakhbout Medical City' },
  { value: 'CCAD', label: 'Cleveland Clinic Abu Dhabi' },
  { value: 'TAWAM', label: 'Tawam Hospital' },
  { value: 'MAFRAQ', label: 'Mafraq Hospital' },
  { value: 'ALAIN', label: 'Al Ain Hospital' },
  { value: 'CORNICHE', label: 'Corniche Hospital' },
  { value: 'HEALTHPOINT', label: 'Healthpoint' },
  { value: 'NMC', label: 'NMC Royal Hospital' },
  { value: 'BURJEEL_AD', label: 'Burjeel Hospital Abu Dhabi' },
  { value: 'BURJEEL_DXB', label: 'Burjeel Hospital Dubai' },
  { value: 'MEDICLINIC', label: 'Mediclinic' },
  { value: 'DANAT', label: 'Danat Al Emarat' },
  { value: 'RASHID', label: 'Rashid Hospital' },
  { value: 'DUBAI_HOSP', label: 'Dubai Hospital' },
  { value: 'AMERICAN_DXB', label: 'American Hospital Dubai' },
  { value: 'ASTER', label: 'Aster Hospital' },
  { value: 'ALZAHRA', label: 'Al Zahra Hospital Sharjah' },
  { value: 'UHS', label: 'University Hospital Sharjah' },
]

const PATIENT_AREAS = [
  { group: 'Abu Dhabi City', options: [
    { value: 'al_maryah_island', label: 'Al Maryah Island' },
    { value: 'al_reem_island', label: 'Al Reem Island' },
    { value: 'saadiyat_island', label: 'Saadiyat Island' },
    { value: 'yas_island', label: 'Yas Island' },
    { value: 'al_bateen', label: 'Al Bateen' },
    { value: 'corniche', label: 'Corniche' },
    { value: 'al_nahyan', label: 'Al Nahyan' },
    { value: 'al_mushrif', label: 'Al Mushrif' },
    { value: 'al_karamah', label: 'Al Karamah' },
    { value: 'al_muroor', label: 'Al Muroor' },
    { value: 'al_rawdah', label: 'Al Rawdah' },
    { value: 'tourist_club', label: 'Tourist Club Area' },
    { value: 'between_bridges', label: 'Between Two Bridges' },
  ]},
  { group: 'Abu Dhabi Suburbs', options: [
    { value: 'khalifa_city', label: 'Khalifa City' },
    { value: 'mbz_city', label: 'Mohammed Bin Zayed City' },
    { value: 'mussafah', label: 'Mussafah' },
    { value: 'al_shamkha', label: 'Al Shamkha' },
    { value: 'al_reef', label: 'Al Reef' },
    { value: 'baniyas', label: 'Baniyas' },
    { value: 'al_wathba', label: 'Al Wathba' },
    { value: 'shahama', label: 'Shahama' },
    { value: 'al_rahba', label: 'Al Rahba' },
    { value: 'al_falah', label: 'Al Falah' },
  ]},
  { group: 'Al Ain', options: [
    { value: 'al_ain_centre', label: 'Al Ain City Centre' },
    { value: 'al_jimi', label: 'Al Jimi' },
    { value: 'al_muwaiji', label: 'Al Muwaiji' },
    { value: 'al_khabisi', label: 'Al Khabisi' },
    { value: 'hili', label: 'Hili' },
    { value: 'zakher', label: 'Zakher' },
  ]},
  { group: 'Dubai', options: [
    { value: 'bur_dubai', label: 'Bur Dubai' },
    { value: 'deira', label: 'Deira' },
    { value: 'downtown_dubai', label: 'Downtown Dubai' },
    { value: 'dubai_marina', label: 'Dubai Marina' },
    { value: 'jumeirah', label: 'Jumeirah' },
    { value: 'al_barsha', label: 'Al Barsha' },
    { value: 'international_city', label: 'International City' },
    { value: 'silicon_oasis', label: 'Silicon Oasis' },
  ]},
  { group: 'Sharjah', options: [
    { value: 'al_majaz', label: 'Al Majaz' },
    { value: 'al_nahda_shj', label: 'Al Nahda' },
    { value: 'al_taawun', label: 'Al Taawun' },
    { value: 'al_khan', label: 'Al Khan' },
  ]},
  { group: 'Northern Emirates', options: [
    { value: 'ajman', label: 'Ajman' },
    { value: 'rak', label: 'Ras Al Khaimah' },
    { value: 'fujairah', label: 'Fujairah' },
    { value: 'uaq', label: 'Umm Al Quwain' },
  ]},
]

const EMIRATES = [
  { value: 'AD', label: 'Abu Dhabi' },
  { value: 'DXB', label: 'Dubai' },
  { value: 'SHJ', label: 'Sharjah' },
  { value: 'AJM', label: 'Ajman' },
  { value: 'RAK', label: 'Ras Al Khaimah' },
  { value: 'FUJ', label: 'Fujairah' },
  { value: 'UAQ', label: 'Umm Al Quwain' },
]

const AGE_BANDS = [
  { value: '0-17', label: 'Under 18' },
  { value: '18-39', label: '18 to 39' },
  { value: '40-64', label: '40 to 64' },
  { value: '65+', label: '65 and above' },
]

const GENDERS = [
  { value: 'm', label: 'Male' },
  { value: 'f', label: 'Female' },
  { value: 'unknown', label: 'Not specified' },
]

const INSURANCE_TIERS = [
  { value: 'thiqa', label: 'Thiqa' },
  { value: 'daman_basic', label: 'Daman Basic' },
  { value: 'daman_enhanced', label: 'Daman Enhanced' },
  { value: 'commercial', label: 'Commercial' },
  { value: 'self_pay', label: 'Self Pay' },
]

const BOOKING_CHANNELS = [
  { value: 'app', label: 'Mobile App' },
  { value: 'web', label: 'Website' },
  { value: 'phone', label: 'Phone Call' },
  { value: 'walk_in', label: 'Walk In' },
]

const LANGUAGES = [
  { value: 'en', label: 'English' },
  { value: 'ar', label: 'Arabic' },
  { value: 'ur', label: 'Urdu' },
  { value: 'tl', label: 'Tagalog' },
  { value: 'other', label: 'Other' },
]

export function ScoreOne() {
  const [result, setResult] = useState<ScoreResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    const fd = new FormData(e.currentTarget)
    const input: AppointmentInput = {
      appointment_at: fd.get('appointment_at') as string,
      booked_at: fd.get('booked_at') as string,
      specialty: fd.get('specialty') as string,
      clinic_area: (fd.get('clinic_area') as string) || undefined,
      patient_area: (fd.get('patient_area') as string) || undefined,
      patient_age_band: fd.get('patient_age_band') as string,
      patient_gender: fd.get('patient_gender') as string,
      insurance_tier: fd.get('insurance_tier') as string,
      booking_channel: fd.get('booking_channel') as string,
      language_pref: fd.get('language_pref') as string,
      prior_noshow_count_12mo: Number(fd.get('prior_noshow_count_12mo')),
      prior_attended_count_12mo: Number(fd.get('prior_attended_count_12mo')),
      emirate: fd.get('emirate') as string,
    }
    try {
      const res = await scoreSingle(input)
      setResult(res)
    } catch (err) {
      setError('Failed to score appointment. Please try again.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-5xl mx-auto">
      <div>
        <h2 className="text-xl font-medium mb-1">Score Appointment</h2>
        <p className="text-sm text-text-secondary mb-5">
          Enter appointment details to generate a no show risk assessment.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <fieldset className="space-y-3">
            <legend className="text-xs font-medium text-gold mb-2 uppercase tracking-wide">Appointment Details</legend>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Appointment Date and Time" name="appointment_at" type="datetime-local" required />
              <Field label="Booking Date and Time" name="booked_at" type="datetime-local" required />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Select label="Specialty" name="specialty" options={SPECIALTIES} />
              <Select label="Emirate" name="emirate" options={EMIRATES} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Select label="Booking Channel" name="booking_channel" options={BOOKING_CHANNELS} />
              <Select label="Language Preference" name="language_pref" options={LANGUAGES} />
            </div>
          </fieldset>

          <fieldset className="space-y-3">
            <legend className="text-xs font-medium text-gold mb-2 uppercase tracking-wide">Location</legend>
            <div className="grid grid-cols-2 gap-3">
              <Select label="Clinic" name="clinic_area" options={CLINICS} />
              <GroupedSelect label="Patient Area" name="patient_area" groups={PATIENT_AREAS} />
            </div>
          </fieldset>

          <fieldset className="space-y-3">
            <legend className="text-xs font-medium text-gold mb-2 uppercase tracking-wide">Patient Profile</legend>
            <div className="grid grid-cols-2 gap-3">
              <Select label="Age Group" name="patient_age_band" options={AGE_BANDS} />
              <Select label="Gender" name="patient_gender" options={GENDERS} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Select label="Insurance" name="insurance_tier" options={INSURANCE_TIERS} />
              <div />
            </div>
          </fieldset>

          <fieldset className="space-y-3">
            <legend className="text-xs font-medium text-gold mb-2 uppercase tracking-wide">Attendance History</legend>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Missed Appointments (Past 12 Months)" name="prior_noshow_count_12mo" type="number" defaultValue="0" min="0" />
              <Field label="Attended Appointments (Past 12 Months)" name="prior_attended_count_12mo" type="number" defaultValue="0" min="0" />
            </div>
          </fieldset>

          {error && (
            <p className="text-sm text-risk-very-high">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gold hover:bg-gold-dim text-surface font-semibold py-2.5 px-4 rounded transition-colors disabled:opacity-50"
          >
            {loading ? 'Generating Risk Score...' : 'Generate Risk Score'}
          </button>
        </form>
      </div>

      <div className="lg:sticky lg:top-6 lg:self-start">
        {result && (
          <div className="space-y-5">
            <div>
              <p className="text-xs text-text-secondary uppercase tracking-wide mb-2">Risk Assessment</p>
              <div className="flex items-center gap-3">
                <RiskBadge band={result.risk_band} />
                <span className="text-3xl font-medium">
                  {(result.probability * 100).toFixed(0)}%
                </span>
                <span className="text-sm text-text-secondary">likelihood of no show</span>
              </div>
            </div>
            <div className="bg-surface-raised border border-gold/20 rounded-lg p-4">
              <p className="text-xs text-text-secondary uppercase tracking-wide mb-1">Recommended Action</p>
              <p className="text-sm text-gold">{result.recommended_action}</p>
            </div>
            <ExplanationCard factors={result.top_factors} />
            <p className="text-xs text-text-secondary">
              Model: {result.model_version} — This is an operational tool, not a clinical decision.
            </p>
          </div>
        )}
        {!result && (
          <div className="flex items-center justify-center h-64 text-text-secondary text-sm border border-dashed border-white/20 rounded-lg">
            Complete the form to see the risk assessment
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
        className="mt-0.5 w-full bg-surface-raised border border-white/20 rounded px-3 py-2 text-sm text-text-primary focus:border-gold focus:outline-none"
      />
    </label>
  )
}

function Select({ label, name, options }: { label: string; name: string; options: Array<{ value: string; label: string }> }) {
  return (
    <label className="block">
      <span className="text-xs text-text-secondary">{label}</span>
      <select
        name={name}
        className="mt-0.5 w-full bg-surface-raised border border-white/20 rounded px-3 py-2 text-sm text-text-primary focus:border-gold focus:outline-none"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </label>
  )
}

function GroupedSelect({ label, name, groups }: {
  label: string
  name: string
  groups: Array<{ group: string; options: Array<{ value: string; label: string }> }>
}) {
  return (
    <label className="block">
      <span className="text-xs text-text-secondary">{label}</span>
      <select
        name={name}
        className="mt-0.5 w-full bg-surface-raised border border-white/20 rounded px-3 py-2 text-sm text-text-primary focus:border-gold focus:outline-none"
      >
        <option value="">Select area</option>
        {groups.map((g) => (
          <optgroup key={g.group} label={g.group}>
            {g.options.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </optgroup>
        ))}
      </select>
    </label>
  )
}
