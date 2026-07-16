export function WarningTriangleIcon({ className = 'w-16 h-16' }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className} aria-hidden="true">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 9v4m0 3.5h.01M10.29 3.86l-8.13 14.1A1.5 1.5 0 0 0 3.5 20h17a1.5 1.5 0 0 0 1.34-2.04l-8.13-14.1a1.5 1.5 0 0 0-2.72 0Z"
      />
    </svg>
  )
}

export function ErrorCircleIcon({ className = 'w-16 h-16' }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className} aria-hidden="true">
      <circle cx="12" cy="12" r="9" />
      <path strokeLinecap="round" d="M12 8v5m0 3.5h.01" />
    </svg>
  )
}
