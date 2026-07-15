import { LOW_CONFIDENCE_THRESHOLD } from '../lib/constants'

export default function ConfidenceBadge({ confidence }) {
  const pct = Math.round(confidence * 100)
  const isLow = confidence < LOW_CONFIDENCE_THRESHOLD

  return (
    <span className="inline-flex items-center gap-4 text-xs font-medium text-text-slate">
      {pct}% confidence
      {isLow && (
        <span className="text-severity-high font-medium">
          — Low confidence, please review manually
        </span>
      )}
    </span>
  )
}
