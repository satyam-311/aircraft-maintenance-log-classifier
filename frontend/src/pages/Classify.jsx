import { useState } from 'react'
import ConfidenceBadge from '../components/ConfidenceBadge'
import SeverityPill from '../components/SeverityPill'
import Notice from '../components/Notice'
import Button from '../components/Button'
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
          <Button variant="primary" disabled={!canSubmit} onClick={handleClassify}>
            {loading ? 'Classifying…' : 'Classify'}
          </Button>
        </div>
      </div>

      {error && <Notice variant="error">{error}</Notice>}

      {result && (
        <div className="bg-surface-white border border-border-light rounded-card p-16 flex flex-col gap-24">
          {result.warnings?.length > 0 && <Notice variant="warning">{result.warnings.join(' ')}</Notice>}

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
            <Button variant="secondary" onClick={() => setCorrectionOpen('ata_chapter')}>
              Correct
            </Button>
          </div>

          <div className="flex justify-between items-start border-t border-border-light pt-16">
            <div>
              <div className="text-xs font-medium text-text-slate mb-4">Predicted Severity</div>
              <div className="flex items-center gap-8">
                <SeverityPill severity={result.severity} />
                <ConfidenceBadge confidence={result.severity_confidence} />
              </div>
            </div>
            <Button variant="secondary" onClick={() => setCorrectionOpen('severity')}>
              Correct
            </Button>
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
                  <Button key={value} variant="option" onClick={() => submitCorrection(correctionOpen, value)}>
                    {label}
                  </Button>
                )
              )}
            </div>
            <div className="mt-16 flex justify-end">
              <Button variant="ghost" onClick={() => setCorrectionOpen(null)}>
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}

      {correctionStatus === 'saved' && (
        <div className="text-success text-sm">Correction saved — thank you.</div>
      )}
      {correctionStatus?.startsWith('error:') && (
        <Notice variant="error">Couldn't save correction: {correctionStatus.replace(/^error:\s*/, '')}</Notice>
      )}
    </div>
  )
}
