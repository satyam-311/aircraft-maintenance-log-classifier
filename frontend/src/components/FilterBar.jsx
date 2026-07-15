import { ATA_CHAPTERS, SEVERITY_LEVELS } from '../lib/constants'

export default function FilterBar({ system, severity, onSystemChange, onSeverityChange }) {
  const inputClass =
    'border border-border-light rounded-input px-16 py-8 text-sm text-text-charcoal ' +
    'focus:border-signal-blue focus:outline-none focus:ring-2 focus:ring-signal-blue/20 bg-surface-white'

  return (
    <div className="flex flex-wrap gap-16 items-center">
      <select
        className={inputClass}
        value={system || ''}
        onChange={(e) => onSystemChange(e.target.value || null)}
      >
        <option value="">All systems</option>
        {Object.entries(ATA_CHAPTERS).map(([code, name]) => (
          <option key={code} value={code}>
            {name} (ATA {code})
          </option>
        ))}
      </select>

      <select
        className={inputClass}
        value={severity || ''}
        onChange={(e) => onSeverityChange(e.target.value || null)}
      >
        <option value="">All severities</option>
        {SEVERITY_LEVELS.map((level) => (
          <option key={level} value={level}>
            {level}
          </option>
        ))}
      </select>
    </div>
  )
}
