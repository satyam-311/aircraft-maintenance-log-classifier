import { LOW_CONFIDENCE_THRESHOLD } from '../lib/constants'
import { WarningTriangleIcon } from './icons'

export default function ConfidenceBadge({ confidence }) {
  const pct = Math.round(confidence * 100)
  const isLow = confidence < LOW_CONFIDENCE_THRESHOLD

  return (
    <div className="flex items-center gap-8 flex-wrap">
      <span className="text-xs font-medium text-text-slate">{pct}% confidence</span>
      {isLow && (
        <span
          className="inline-flex items-center gap-4 text-xs font-semibold text-severity-high
                     bg-severity-high/10 border border-severity-high/40 rounded-full px-8 py-2"
        >
          <WarningTriangleIcon className="w-12 h-12" />
          Low confidence — please review manually
        </span>
      )}
    </div>
  )
}
