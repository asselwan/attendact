export function ScoreBulk() {
  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-xl font-medium mb-4">Bulk Score</h2>
      <div className="border-2 border-dashed border-white/20 rounded-lg p-12 text-center">
        <p className="text-text-secondary text-sm mb-2">
          Upload tomorrow's schedule as CSV to score all appointments at once.
        </p>
        <p className="text-text-secondary text-xs">
          Maximum 5,000 rows per upload. Available in week 3.
        </p>
      </div>
    </div>
  )
}
