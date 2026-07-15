import { SEVERITY_COLORS } from '../lib/constants'

export default function SeverityPill({ severity }) {
  if (!severity) return null
  const color = SEVERITY_COLORS[severity] || '#6B7280'

  return (
    <span
      className="inline-block px-8 py-4 rounded-full text-xs font-medium text-white"
      style={{ backgroundColor: color, paddingLeft: 10, paddingRight: 10, paddingTop: 2, paddingBottom: 2 }}
    >
      {severity}
    </span>
  )
}
