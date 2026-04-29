import { useState } from 'react'
import {
  fetchReview,
  recordOutcomes,
  triggerCalibration,
  type ReviewResponse,
  type OutcomeInput,
  type PredictionError,
} from '../lib/api'
import { RiskBadge } from '../components/RiskBadge'

const RISK_BAND_LABELS: Record<string, string> = {
  low: 'Low',
  moderate: 'Moderate',
  high: 'High',
  very_high: 'Very High',
}

export function Review() {
  const [review, setReview] = useState<ReviewResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [outcomeInputs, setOutcomeInputs] = useState<OutcomeInput[]>([
    { appointment_id: '', outcome: 'no_show' },
  ])
  const [recordResult, setRecordResult] = useState<string | null>(null)
  const [calibrationMsg, setCalibrationMsg] = useState<string | null>(null)

  async function loadReview() {
    setLoading(true)
    try {
      const data = await fetchReview()
      setReview(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  async function handleRecordOutcomes(e: React.FormEvent) {
    e.preventDefault()
    const valid = outcomeInputs.filter((o) => o.appointment_id.trim())
    if (!valid.length) return
    try {
      const res = await recordOutcomes(valid)
      setRecordResult(`Recorded ${res.recorded} outcome(s). ${res.not_found} not found.`)
      if (res.recorded > 0) loadReview()
    } catch (err) {
      setRecordResult('Failed to record outcomes.')
      console.error(err)
    }
  }

  async function handleCalibrate() {
    try {
      const res = await triggerCalibration()
      setCalibrationMsg(
        `${res.recommendation} (${res.samples_used} samples, error: ${(res.overall_calibration_error * 100).toFixed(1)}%)`
      )
      loadReview()
    } catch (err) {
      setCalibrationMsg('Calibration failed.')
      console.error(err)
    }
  }

  function addOutcomeRow() {
    setOutcomeInputs([...outcomeInputs, { appointment_id: '', outcome: 'no_show' }])
  }

  function updateOutcome(idx: number, field: keyof OutcomeInput, value: string) {
    const updated = [...outcomeInputs]
    updated[idx] = { ...updated[idx], [field]: value }
    setOutcomeInputs(updated)
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Record Outcomes */}
      <section>
        <h2 className="text-xl font-medium mb-1">Record Outcomes</h2>
        <p className="text-sm text-text-secondary mb-4">
          Enter appointment IDs and what actually happened. This is how the model learns.
        </p>
        <form onSubmit={handleRecordOutcomes} className="space-y-3">
          {outcomeInputs.map((o, idx) => (
            <div key={idx} className="flex gap-3 items-end">
              <label className="flex-1 block">
                {idx === 0 && <span className="text-xs text-text-secondary">Appointment ID</span>}
                <input
                  value={o.appointment_id}
                  onChange={(e) => updateOutcome(idx, 'appointment_id', e.target.value)}
                  placeholder="Paste appointment ID from scoring result"
                  className="mt-0.5 w-full bg-surface-raised border border-white/10 rounded px-3 py-2 text-sm text-text-primary focus:border-gold focus:outline-none font-mono"
                />
              </label>
              <label className="w-40 block">
                {idx === 0 && <span className="text-xs text-text-secondary">Outcome</span>}
                <select
                  value={o.outcome}
                  onChange={(e) => updateOutcome(idx, 'outcome', e.target.value)}
                  className="mt-0.5 w-full bg-surface-raised border border-white/10 rounded px-3 py-2 text-sm text-text-primary focus:border-gold focus:outline-none"
                >
                  <option value="attended">Attended</option>
                  <option value="no_show">No Show</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </label>
            </div>
          ))}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={addOutcomeRow}
              className="text-xs text-gold hover:text-gold-dim transition-colors"
            >
              + Add another
            </button>
            <button
              type="submit"
              className="bg-gold hover:bg-gold-dim text-surface font-semibold py-2 px-4 rounded text-sm transition-colors"
            >
              Record Outcomes
            </button>
          </div>
          {recordResult && (
            <p className="text-sm text-text-secondary">{recordResult}</p>
          )}
        </form>
      </section>

      {/* Prediction Review */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-medium">Prediction Review</h2>
            <p className="text-sm text-text-secondary">
              Where the model was wrong — and how it is calibrated
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={loadReview}
              disabled={loading}
              className="bg-surface-raised border border-white/10 hover:border-gold/30 text-text-primary font-medium py-2 px-4 rounded text-sm transition-colors disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Load Review'}
            </button>
            <button
              onClick={handleCalibrate}
              className="bg-gold hover:bg-gold-dim text-surface font-semibold py-2 px-4 rounded text-sm transition-colors"
            >
              Recalibrate Model
            </button>
          </div>
        </div>

        {calibrationMsg && (
          <div className="bg-surface-raised border border-gold/20 rounded-lg p-4 mb-4">
            <p className="text-sm text-gold">{calibrationMsg}</p>
          </div>
        )}

        {review && (
          <div className="space-y-6">
            {/* Stats */}
            <div className="grid grid-cols-4 gap-4">
              <StatCard label="Outcomes Recorded" value={review.total_with_outcomes.toString()} />
              <StatCard label="Prediction Errors" value={review.total_errors.toString()} highlight={review.total_errors > 0} />
              <StatCard label="False Negatives" value={review.false_negatives.toString()} subtitle="Predicted safe, actually no showed" />
              <StatCard label="False Positives" value={review.false_positives.toString()} subtitle="Predicted risky, actually attended" />
            </div>

            {/* Calibration by band */}
            {review.calibration.total_labeled > 0 && (
              <div>
                <h3 className="text-sm font-medium mb-3">Calibration by Risk Band</h3>
                <div className="grid grid-cols-1 gap-2">
                  {Object.entries(review.calibration.bands).map(([band, stats]) => (
                    <div key={band} className="bg-surface-raised border border-white/5 rounded-lg p-4 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <RiskBadge band={band} />
                        <span className="text-sm text-text-secondary">{stats.count} outcomes</span>
                      </div>
                      <div className="flex gap-6 text-sm">
                        <div>
                          <span className="text-text-secondary">Predicted: </span>
                          <span className="text-text-primary font-medium">{(stats.avg_predicted_probability * 100).toFixed(0)}%</span>
                        </div>
                        <div>
                          <span className="text-text-secondary">Actual: </span>
                          <span className="text-text-primary font-medium">{(stats.actual_noshow_rate * 100).toFixed(0)}%</span>
                        </div>
                        <div>
                          <span className="text-text-secondary">Error: </span>
                          <span className={`font-medium ${stats.calibration_error > 0.1 ? 'text-risk-very-high' : 'text-green-400'}`}>
                            {(stats.calibration_error * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Error list */}
            {review.errors.length > 0 && (
              <div>
                <h3 className="text-sm font-medium mb-3">Prediction Errors</h3>
                <div className="space-y-2">
                  {review.errors.map((err) => (
                    <ErrorCard key={err.appointment_id} error={err} />
                  ))}
                </div>
              </div>
            )}

            {review.total_with_outcomes === 0 && (
              <div className="flex items-center justify-center h-32 text-text-secondary text-sm border border-dashed border-white/10 rounded-lg">
                No outcomes recorded yet. Record outcomes above to see how the model is performing.
              </div>
            )}
          </div>
        )}

        {!review && (
          <div className="flex items-center justify-center h-32 text-text-secondary text-sm border border-dashed border-white/10 rounded-lg">
            Click "Load Review" to see prediction accuracy and calibration data
          </div>
        )}
      </section>
    </div>
  )
}

function StatCard({ label, value, subtitle, highlight }: {
  label: string
  value: string
  subtitle?: string
  highlight?: boolean
}) {
  return (
    <div className="bg-surface-raised border border-white/5 rounded-lg p-4">
      <p className="text-xs text-text-secondary">{label}</p>
      <p className={`text-2xl font-medium mt-1 ${highlight ? 'text-gold' : ''}`}>{value}</p>
      {subtitle && <p className="text-xs text-text-secondary mt-1">{subtitle}</p>}
    </div>
  )
}

function ErrorCard({ error }: { error: PredictionError }) {
  return (
    <div className="bg-surface-raised border border-white/5 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <RiskBadge band={error.risk_band} />
          <span className="text-sm font-medium">
            {(error.probability * 100).toFixed(0)}% predicted
          </span>
          <span className="text-xs px-2 py-0.5 rounded bg-risk-very-high/10 text-risk-very-high border border-risk-very-high/20">
            {error.error_type === 'false_negative' ? 'Missed No Show' : 'False Alarm'}
          </span>
        </div>
        <span className="text-xs text-text-secondary font-mono">{error.appointment_id.slice(0, 8)}</span>
      </div>
      <div className="flex gap-4 text-xs text-text-secondary">
        <span>{error.specialty}</span>
        {error.clinic_area && <span>{error.clinic_area}</span>}
        {error.patient_area && <span>{error.patient_area}</span>}
        {error.distance_km && <span>{error.distance_km} km</span>}
      </div>
    </div>
  )
}
