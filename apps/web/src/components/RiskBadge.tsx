type RiskBand = 'low' | 'moderate' | 'high' | 'very_high'

const styles: Record<RiskBand, string> = {
  low: 'bg-risk-low/10 text-risk-low border-risk-low/30',
  moderate: 'bg-risk-moderate/10 text-risk-moderate border-risk-moderate/30',
  high: 'bg-risk-high/10 text-risk-high border-risk-high/30',
  very_high: 'bg-risk-very-high/10 text-risk-very-high border-risk-very-high/30',
}

const labels: Record<RiskBand, string> = {
  low: 'Low',
  moderate: 'Moderate',
  high: 'High',
  very_high: 'Very High',
}

export function RiskBadge({ band }: { band: RiskBand }) {
  return (
    <span className={`inline-block px-2.5 py-0.5 rounded border text-xs font-medium ${styles[band]}`}>
      {labels[band]}
    </span>
  )
}
