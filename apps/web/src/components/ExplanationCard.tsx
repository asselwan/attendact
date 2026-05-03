interface Factor {
  feature: string
  value: string | number | boolean
  contribution: number
  plain_text: string
}

export function ExplanationCard({ factors }: { factors: Factor[] }) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-text-secondary">Contributing Factors</h3>
      {factors.map((factor) => (
        <div
          key={factor.feature}
          className="bg-surface-raised border border-white/15 rounded-lg p-3"
        >
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm text-text-primary">{factor.plain_text}</p>
            <span className="text-xs text-text-secondary whitespace-nowrap">
              +{(factor.contribution * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}
