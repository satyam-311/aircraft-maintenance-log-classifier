import { useState } from 'react'
import ReportCard from '../components/ReportCard'
import Notice from '../components/Notice'
import Button from '../components/Button'
import { api } from '../lib/api'

export default function Ask() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState(null)
  const [sources, setSources] = useState([])
  const [generationError, setGenerationError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [hasAsked, setHasAsked] = useState(false)
  const [error, setError] = useState(null)

  async function handleAsk() {
    setLoading(true)
    setAnswer(null)
    setError(null)
    try {
      const data = await api.ask(question)
      setAnswer(data.answer)
      setSources(data.sources)
      setGenerationError(data.generation_error)
      setHasAsked(true)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const canAsk = question.trim().length > 0 && !loading

  return (
    <div className="flex flex-col gap-32">
      <div>
        <h1 className="text-[28px] font-bold text-text-charcoal mb-8">Ask</h1>
        <p className="text-text-slate text-sm">
          Ask a natural-language question — answers are grounded in retrieved report excerpts.
        </p>
      </div>

      <div className="flex gap-16">
        <input
          className="flex-1 border border-border-light rounded-input px-16 py-8 text-sm
                     focus:border-signal-blue focus:outline-none focus:ring-2 focus:ring-signal-blue/20 bg-surface-white"
          placeholder="e.g. what usually causes hydraulic pressure loss?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && canAsk && handleAsk()}
        />
        <Button variant="primary" size="sm" onClick={handleAsk} disabled={!canAsk}>
          {loading ? 'Asking…' : 'Ask'}
        </Button>
      </div>

      {error && <Notice variant="error">{error}</Notice>}

      {hasAsked && (
        <>
          {answer && (
            <div className="bg-surface-white border border-border-light rounded-card p-16">
              <div className="text-xs font-medium text-text-slate mb-8">Answer</div>
              <p className="text-sm text-text-charcoal leading-relaxed whitespace-pre-wrap">{answer}</p>
            </div>
          )}

          {generationError && <Notice variant="warning">{generationError}</Notice>}

          {sources.length > 0 && (
            <div>
              <h2 className="text-[20px] font-semibold text-text-charcoal mb-16">
                Source Reports
              </h2>
              <div className="grid grid-cols-1 report-grid:grid-cols-2 gap-16">
                {sources.map((s) => (
                  <ReportCard key={s.report_id} report={s} />
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
