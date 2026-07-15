import { useState } from 'react'
import FilterBar from '../components/FilterBar'
import ReportCard from '../components/ReportCard'
import { api } from '../lib/api'

export default function Search() {
  const [query, setQuery] = useState('')
  const [system, setSystem] = useState(null)
  const [severity, setSeverity] = useState(null)
  const [results, setResults] = useState([])
  const [degraded, setDegraded] = useState(false)
  const [degradedMessage, setDegradedMessage] = useState(null)
  const [loading, setLoading] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)

  async function runSearch() {
    setLoading(true)
    try {
      const data = await api.search({ q: query, system, severity })
      setResults(data.results)
      setDegraded(data.degraded)
      setDegradedMessage(data.degraded_message)
      setHasSearched(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-32">
      <div>
        <h1 className="text-[28px] font-bold text-text-charcoal mb-8">Search</h1>
        <p className="text-text-slate text-sm">Search the report corpus by meaning, not just keywords.</p>
      </div>

      <div className="flex flex-col gap-16">
        <div className="flex gap-16">
          <input
            className="flex-1 border border-border-light rounded-input px-16 py-8 text-sm
                       focus:border-signal-blue focus:outline-none focus:ring-2 focus:ring-signal-blue/20 bg-surface-white"
            placeholder="e.g. hydraulic pressure loss on approach"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && runSearch()}
          />
          <button
            onClick={runSearch}
            disabled={loading}
            className="bg-signal-blue text-white text-sm font-medium uppercase tracking-wide
                       rounded-button px-20 py-8 hover:bg-aviation-navy transition-colors disabled:opacity-40"
          >
            {loading ? 'Searching…' : 'Search'}
          </button>
        </div>
        <FilterBar system={system} severity={severity} onSystemChange={setSystem} onSeverityChange={setSeverity} />
      </div>

      {degraded && degradedMessage && (
        <div className="text-severity-medium text-sm bg-surface-white border border-border-light rounded-card p-16">
          {degradedMessage}
        </div>
      )}

      {hasSearched && results.length === 0 && (
        <p className="text-text-slate text-sm">No matching reports found.</p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-16">
        {results.map((r) => (
          <ReportCard key={r.report_id} report={r} />
        ))}
      </div>
    </div>
  )
}
