import { useState } from 'react'
import ConfidenceBadge from '../components/ConfidenceBadge'
import SeverityPill from '../components/SeverityPill'
import { api } from '../lib/api'
import { ATA_CHAPTERS, SEVERITY_LEVELS } from '../lib/constants'

export default function Classify() {
  const [text, setText] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [reportId, setReportId] = useState(null)
  const [correctionOpen, setCorrectionOpen] = useState(null) // 'ata_chapter' | 'severity' | null
  const [correctionStatus, setCorrectionStatus] = useState(null)

  const canSubmit = text.trim().split(/\s+/).filter(Boolean).length >= 3 && !loading

  async function handleClassify() {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await api.classify(text)
      setResult(data)
      setReportId(data.report_id)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function submitCorrection(field, value) {
    if (!reportId) return
    try {
      await api.submitCorrection(reportId, field, value)
      setCorrectionStatus('saved')
      setCorrectionOpen(null)
    } catch (e) {
      setCorrectionStatus(`error: ${e.message}`)
    }
  }

  return (
    <div className="flex flex-col gap-32">
      <div>
        <h1 className="text-[28px] font-bold text-text-charcoal mb-8">Classify</h1>
        <p className="text-text-slate text-sm">Paste a maintenance narrative to get an instant classification.</p>
      </div>

      <div className="bg-surface-white border border-border-light rounded-card p-16">
        <textarea
          className="w-full min-h-[160px] border border-border-light rounded-input p-16 text-sm font-mono
                     focus:border-signal-blue focus:outline-none focus:ring-2 focus:ring-signal-blue/20"
          placeholder="Paste the maintenance or incident narrative text here…"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <div className="mt-16 flex justify-end">
          <button
            disabled={!canSubmit}
            onClick={handleClassify}
            className="bg-signal-blue text-white text-sm font-medium uppercase tracking-wide
                       rounded-button px-20 py-12 disabled:opacity-40 disabled:cursor-not-allowed
                       hover:bg-aviation-navy transition-colors"
          >
            {loading ? 'Classifying…' : 'Classify'}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-surface-white border border-error rounded-card p-16 text-error text-sm">
          {error}
        </div>
      )}

      {result && (
        <div className="bg-surface-white border border-border-light rounded-card p-16 flex flex-col gap-24">
          {result.warnings?.length > 0 && (
            <div className="text-severity-medium text-sm">{result.warnings.join(' ')}</div>
          )}

          <div className="flex justify-between items-start">
            <div>
              <div className="text-xs font-medium text-text-slate mb-4">Predicted System</div>
              <div className="text-lg font-bold text-text-charcoal">
                {ATA_CHAPTERS[result.ata_chapter] || result.ata_chapter}{' '}
                <span className="text-text-slate font-normal text-sm">— ATA {result.ata_chapter}</span>
              </div>
              <div className="mt-4">
                <ConfidenceBadge confidence={result.ata_confidence} />
              </div>
              {result.ata_other_possible?.length > 0 && (
                <div className="mt-8 text-xs text-text-slate">
                  Other possible systems:{' '}
                  {result.ata_other_possible
                    .map((o) => `${ATA_CHAPTERS[o.label] || o.label} (${Math.round(o.confidence * 100)}%)`)
                    .join(', ')}
                </div>
              )}
            </div>
            <button
              onClick={() => setCorrectionOpen('ata_chapter')}
              className="text-signal-blue border border-signal-blue rounded-button px-16 py-8 text-xs font-medium uppercase"
            >
              Correct
            </button>
          </div>

          <div className="flex justify-between items-start border-t border-border-light pt-16">
            <div>
              <div className="text-xs font-medium text-text-slate mb-4">Predicted Severity</div>
              <div className="flex items-center gap-8">
                <SeverityPill severity={result.severity} />
                <ConfidenceBadge confidence={result.severity_confidence} />
              </div>
            </div>
            <button
              onClick={() => setCorrectionOpen('severity')}
              className="text-signal-blue border border-signal-blue rounded-button px-16 py-8 text-xs font-medium uppercase"
            >
              Correct
            </button>
          </div>

        </div>
      )}

      {/* Correction modal — centered, max-width 480px, per Frontend Spec */}
      {correctionOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-surface-white rounded-card p-24 max-w-[480px] w-full mx-16">
            <h3 className="text-[20px] font-semibold text-text-charcoal mb-16">Correct this prediction</h3>
            <div className="flex flex-col gap-8">
              {(correctionOpen === 'ata_chapter' ? Object.entries(ATA_CHAPTERS) : SEVERITY_LEVELS.map((s) => [s, s])).map(
                ([value, label]) => (
                  <button
                    key={value}
                    onClick={() => submitCorrection(correctionOpen, value)}
                    className="text-left px-16 py-8 rounded-button border border-border-light hover:border-signal-blue text-sm"
                  >
                    {label}
                  </button>
                )
              )}
            </div>
            <div className="mt-16 flex justify-end">
              <button
                onClick={() => setCorrectionOpen(null)}
                className="text-text-slate text-sm font-medium px-16 py-8"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {correctionStatus === 'saved' && (
        <div className="text-success text-sm">Correction saved — thank you.</div>
      )}
    </div>
  )
}
