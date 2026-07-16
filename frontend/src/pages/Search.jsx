import { useState } from 'react'
import FilterBar from '../components/FilterBar'
import ReportCard from '../components/ReportCard'
import Notice from '../components/Notice'
import Button from '../components/Button'
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
  const [error, setError] = useState(null)

  async function runSearch() {
    setLoading(true)
    setError(null)
    try {
      const data = await api.search({ q: query, system, severity })
      setResults(data.results)
      setDegraded(data.degraded)
      setDegradedMessage(data.degraded_message)
      setHasSearched(true)
    } catch (e) {
      setError(e.message)
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
          <Button variant="primary" size="sm" onClick={runSearch} disabled={loading}>
            {loading ? 'Searching…' : 'Search'}
          </Button>
        </div>
        <FilterBar system={system} severity={severity} onSystemChange={setSystem} onSeverityChange={setSeverity} />
      </div>

      {error && <Notice variant="error">{error}</Notice>}

      {degraded && degradedMessage && <Notice variant="warning">{degradedMessage}</Notice>}

      {hasSearched && results.length === 0 && (
        <p className="text-text-slate text-sm">No matching reports found.</p>
      )}

      <div className="grid grid-cols-1 report-grid:grid-cols-2 gap-16">
        {results.map((r) => (
          <ReportCard key={r.report_id} report={r} />
        ))}
      </div>
    </div>
  )
}
