import SeverityPill from './SeverityPill'
import { ATA_CHAPTERS } from '../lib/constants'

// Per Frontend Spec: white surface, 1px light grey border, 12px radius, 16px padding.
// Top-right: severity pill + confidence %. ATA system name bold under excerpt,
// chapter number in muted grey next to it (e.g. "Hydraulic Power — ATA 29").
export default function ReportCard({ report }) {
  const systemName = report.ata_chapter ? ATA_CHAPTERS[report.ata_chapter] : null

  return (
    <div className="bg-surface-white border border-border-light rounded-card p-16">
      <div className="flex justify-between items-start gap-16">
        <p className="font-mono text-sm text-text-charcoal leading-relaxed flex-1">
          {report.excerpt}
        </p>
        <div className="flex flex-col items-end gap-4 shrink-0">
          <SeverityPill severity={report.severity} />
          {report.score !== null && report.score !== undefined && (
            <span className="text-xs text-text-slate">{Math.round(report.score * 100)}% match</span>
          )}
        </div>
      </div>
      {systemName && (
        <div className="mt-16 text-sm">
          <span className="font-bold text-text-charcoal">{systemName}</span>{' '}
          <span className="text-text-slate">— ATA {report.ata_chapter}</span>
        </div>
      )}
    </div>
  )
}
