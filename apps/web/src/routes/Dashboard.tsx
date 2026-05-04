import { useEffect, useState } from 'react'
import { fetchMetrics, resetDashboard } from '../lib/api'

interface Aggregates {
  total_scored: number
  risk_distribution: Record<string, number>
  by_specialty: Record<string, { count: number; avg_risk: number }>
  by_time_of_day: Record<string, { count: number; avg_risk: number }>
  by_booking_channel: Record<string, { count: number; avg_risk: number }>
  top_risk_factors: Record<string, number>
}

const BASE = import.meta.env.VITE_API_URL || ''

const RISK_COLORS: Record<string, string> = {
  low: 'bg-emerald-500/20 text-emerald-400',
  moderate: 'bg-amber-500/20 text-amber-400',
  high: 'bg-orange-500/20 text-orange-400',
  very_high: 'bg-red-500/20 text-red-400',
}

const RISK_ORDER = ['low', 'moderate', 'high', 'very_high']

export function Dashboard() {
  const [metrics, setMetrics] = useState<{
    total_scored: number
    total_with_outcomes: number
    calibration_by_band: Record<string, { count: number; avg_predicted_probability: number; actual_noshow_rate: number; calibration_error: number }>
  } | null>(null)
  const [aggregates, setAggregates] = useState<Aggregates | null>(null)
  const [loading, setLoading] = useState(true)
  const [resetting, setResetting] = useState(false)

  function load() {
    setLoading(true)
    Promise.all([
      fetchMetrics(),
      fetch(`${BASE}/api/insights/aggregates`).then(r => r.ok ? r.json() : null),
    ]).then(([m, agg]) => {
      setMetrics(m)
      setAggregates(agg?.aggregates ?? null)
      setLoading(false)
    }).catch(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function handleReset() {
    if (!confirm('Reset dashboard? This clears all scored appointments and calibration adjustments.')) return
    setResetting(true)
    try {
      await resetDashboard()
      load()
    } catch (e) {
      alert('Reset failed.')
    } finally {
      setResetting(false)
    }
  }

  if (loading) {
    return (
      <div className="text-text-secondary text-sm py-12 text-center">
        Loading dashboard...
      </div>
    )
  }

  const totalScored = metrics?.total_scored ?? 0
  const totalWithOutcomes = metrics?.total_with_outcomes ?? 0
  const riskDist = aggregates?.risk_distribution ?? {}
  const highRiskCount = (riskDist['high'] ?? 0) + (riskDist['very_high'] ?? 0)
  const highRiskPct = totalScored > 0 ? ((highRiskCount / totalScored) * 100).toFixed(1) : '0'
  const allProbs = aggregates?.by_specialty
    ? Object.values(aggregates.by_specialty).reduce(
        (acc, s) => acc + s.avg_risk * s.count,
        0
      ) / Math.max(totalScored, 1)
    : 0
  const avgRisk = totalScored > 0 ? (allProbs * 100).toFixed(1) : '0'

  if (totalScored === 0) {
    return (
      <div>
        <DashboardHeader onReset={handleReset} resetting={resetting} hasData={false} />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <StatCard label="Total scored" value="0" />
          <StatCard label="Average risk" value="—" />
          <StatCard label="High risk %" value="—" />
        </div>
        <div className="bg-surface-raised border border-white/15 rounded-lg p-6 text-center text-text-secondary text-sm">
          Score some appointments to populate the dashboard.
        </div>
      </div>
    )
  }

  return (
    <div>
      <DashboardHeader onReset={handleReset} resetting={resetting} hasData />

      {/* Top stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <StatCard label="Total scored" value={totalScored.toLocaleString()} />
        <StatCard label="Average risk" value={`${avgRisk}%`} />
        <StatCard label="High risk %" value={`${highRiskPct}%`} />
        <StatCard label="Outcomes recorded" value={totalWithOutcomes.toLocaleString()} />
      </div>

      {/* Risk distribution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-surface-raised border border-white/15 rounded-lg p-5">
          <h3 className="text-sm font-medium text-text-secondary mb-3">Risk distribution</h3>
          <div className="space-y-2">
            {RISK_ORDER.map((band) => {
              const count = riskDist[band] ?? 0
              const pct = totalScored > 0 ? (count / totalScored) * 100 : 0
              return (
                <div key={band} className="flex items-center gap-3">
                  <span className={`text-xs px-2 py-0.5 rounded ${RISK_COLORS[band]} min-w-[80px] text-center`}>
                    {band.replace('_', ' ')}
                  </span>
                  <div className="flex-1 bg-white/5 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${RISK_COLORS[band].split(' ')[0]}`}
                      style={{ width: `${Math.max(pct, 1)}%` }}
                    />
                  </div>
                  <span className="text-xs text-text-secondary w-16 text-right">
                    {count} ({pct.toFixed(0)}%)
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Top risk factors */}
        {aggregates?.top_risk_factors && Object.keys(aggregates.top_risk_factors).length > 0 && (
          <div className="bg-surface-raised border border-white/15 rounded-lg p-5">
            <h3 className="text-sm font-medium text-text-secondary mb-3">Top contributing factors</h3>
            <div className="space-y-2">
              {Object.entries(aggregates.top_risk_factors)
                .sort(([, a], [, b]) => b - a)
                .map(([factor, count]) => (
                  <div key={factor} className="flex items-center justify-between">
                    <span className="text-sm">{factor.replace(/_/g, ' ')}</span>
                    <span className="text-xs text-text-secondary">{count} scores</span>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>

      {/* Breakdown tables */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {aggregates?.by_specialty && Object.keys(aggregates.by_specialty).length > 0 && (
          <BreakdownTable
            title="By specialty"
            data={aggregates.by_specialty}
          />
        )}
        {aggregates?.by_time_of_day && Object.keys(aggregates.by_time_of_day).length > 0 && (
          <BreakdownTable
            title="By time of day"
            data={aggregates.by_time_of_day}
          />
        )}
        {aggregates?.by_booking_channel && Object.keys(aggregates.by_booking_channel).length > 0 && (
          <BreakdownTable
            title="By booking channel"
            data={aggregates.by_booking_channel}
          />
        )}
      </div>

      {/* Calibration */}
      {metrics?.calibration_by_band && Object.keys(metrics.calibration_by_band).length > 0 && (
        <div className="bg-surface-raised border border-white/15 rounded-lg p-5">
          <h3 className="text-sm font-medium text-text-secondary mb-3">Calibration accuracy</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-text-secondary text-xs">
                  <th className="text-left py-2 pr-4">Band</th>
                  <th className="text-right py-2 px-4">Count</th>
                  <th className="text-right py-2 px-4">Avg predicted</th>
                  <th className="text-right py-2 px-4">Actual no show rate</th>
                  <th className="text-right py-2 pl-4">Calibration error</th>
                </tr>
              </thead>
              <tbody>
                {RISK_ORDER.map((band) => {
                  const b = metrics.calibration_by_band[band]
                  if (!b) return null
                  return (
                    <tr key={band} className="border-t border-white/15">
                      <td className="py-2 pr-4">
                        <span className={`text-xs px-2 py-0.5 rounded ${RISK_COLORS[band]}`}>
                          {band.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="text-right py-2 px-4">{b.count}</td>
                      <td className="text-right py-2 px-4">{(b.avg_predicted_probability * 100).toFixed(1)}%</td>
                      <td className="text-right py-2 px-4">{(b.actual_noshow_rate * 100).toFixed(1)}%</td>
                      <td className="text-right py-2 pl-4">{(b.calibration_error * 100).toFixed(1)}%</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

function DashboardHeader({ onReset, resetting, hasData }: { onReset: () => void; resetting: boolean; hasData: boolean }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <h2 className="text-xl font-medium">Dashboard</h2>
      <button
        type="button"
        onClick={onReset}
        disabled={resetting || !hasData}
        className="text-xs px-3 py-1.5 rounded border border-white/20 text-text-secondary hover:text-text-primary hover:border-white/40 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        {resetting ? 'Resetting…' : 'Reset'}
      </button>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-surface-raised border border-white/15 rounded-lg p-4">
      <p className="text-xs text-text-secondary">{label}</p>
      <p className="text-2xl font-medium mt-1">{value}</p>
    </div>
  )
}

function BreakdownTable({
  title,
  data,
}: {
  title: string
  data: Record<string, { count: number; avg_risk: number }>
}) {
  const sorted = Object.entries(data).sort(([, a], [, b]) => b.avg_risk - a.avg_risk)
  return (
    <div className="bg-surface-raised border border-white/15 rounded-lg p-5">
      <h3 className="text-sm font-medium text-text-secondary mb-3">{title}</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-text-secondary text-xs">
            <th className="text-left py-1">Name</th>
            <th className="text-right py-1">Scored</th>
            <th className="text-right py-1">Avg risk</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map(([name, { count, avg_risk }]) => (
            <tr key={name} className="border-t border-white/15">
              <td className="py-1.5">{name.replace(/_/g, ' ')}</td>
              <td className="text-right py-1.5 text-text-secondary">{count}</td>
              <td className="text-right py-1.5">{(avg_risk * 100).toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
