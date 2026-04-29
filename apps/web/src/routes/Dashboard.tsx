export function Dashboard() {
  return (
    <div>
      <h2 className="text-xl font-medium mb-4">Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <StatCard label="Scored today" value="—" />
        <StatCard label="Average risk" value="—" />
        <StatCard label="High risk %" value="—" />
      </div>
      <div className="bg-surface-raised border border-white/5 rounded-lg p-6 text-center text-text-secondary text-sm">
        Risk distribution charts will populate once scoring traffic begins. Available in week 5.
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-surface-raised border border-white/5 rounded-lg p-4">
      <p className="text-xs text-text-secondary">{label}</p>
      <p className="text-2xl font-medium mt-1">{value}</p>
    </div>
  )
}
