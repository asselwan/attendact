import { useState } from 'react'
import { fetchInsights, type Insight, type InsightsResponse } from '../lib/api'

const CATEGORY_LABELS: Record<string, string> = {
  scheduling: 'Scheduling',
  capacity: 'Capacity',
  risk_pattern: 'Risk Pattern',
  intervention: 'Intervention',
}

const CONFIDENCE_STYLES: Record<string, string> = {
  high: 'bg-green-500/10 text-green-400 border-green-500/20',
  medium: 'bg-gold/10 text-gold border-gold/20',
  low: 'bg-white/5 text-text-secondary border-white/10',
}

export function Insights() {
  const [data, setData] = useState<InsightsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleGenerate() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetchInsights()
      setData(res)
    } catch (err) {
      setError('Failed to generate insights. Check that the API key is configured.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-medium">Operational Insights</h2>
          <p className="text-sm text-text-secondary mt-0.5">
            AI powered pattern analysis from your scoring activity
          </p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="bg-gold hover:bg-gold-dim text-surface font-semibold py-2 px-4 rounded text-sm transition-colors disabled:opacity-50"
        >
          {loading ? 'Analysing...' : 'Generate Insights'}
        </button>
      </div>

      {error && (
        <div className="bg-risk-very-high/10 border border-risk-very-high/20 rounded-lg p-4 mb-6">
          <p className="text-sm text-risk-very-high">{error}</p>
        </div>
      )}

      {data && (
        <div className="space-y-4">
          <p className="text-xs text-text-secondary">
            Based on {data.total_scores_analysed} scored appointments
          </p>
          {data.insights.map((insight, idx) => (
            <InsightCard key={idx} insight={insight} />
          ))}
        </div>
      )}

      {!data && !error && (
        <div className="flex items-center justify-center h-64 text-text-secondary text-sm border border-dashed border-white/20 rounded-lg">
          Score appointments, then generate insights to see AI powered operational intelligence
        </div>
      )}
    </div>
  )
}

function InsightCard({ insight }: { insight: Insight }) {
  return (
    <div className="bg-surface-raised border border-white/15 rounded-lg p-5">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-medium text-gold uppercase tracking-wide">
          {CATEGORY_LABELS[insight.category] || insight.category}
        </span>
        <span className={`text-xs px-2 py-0.5 rounded border ${CONFIDENCE_STYLES[insight.confidence] || CONFIDENCE_STYLES.low}`}>
          {insight.confidence}
        </span>
      </div>
      <h3 className="text-sm font-medium text-text-primary mb-1">{insight.title}</h3>
      <p className="text-sm text-text-secondary leading-relaxed">{insight.body}</p>
    </div>
  )
}
