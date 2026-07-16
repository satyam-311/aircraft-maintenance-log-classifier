import { WarningTriangleIcon, ErrorCircleIcon } from './icons'

const VARIANTS = {
  warning: {
    container: 'bg-severity-medium/10 border border-severity-medium/40',
    text: 'text-text-charcoal',
    icon: 'text-severity-medium',
    Icon: WarningTriangleIcon,
  },
  error: {
    container: 'bg-error/10 border border-error/40',
    text: 'text-error',
    icon: 'text-error',
    Icon: ErrorCircleIcon,
  },
}

export default function Notice({ variant = 'warning', children }) {
  const v = VARIANTS[variant] || VARIANTS.warning
  return (
    <div className={`flex items-start gap-8 text-sm rounded-card p-16 ${v.container} ${v.text}`}>
      <v.Icon className={`w-16 h-16 mt-2 shrink-0 ${v.icon}`} />
      <span>{children}</span>
    </div>
  )
}
