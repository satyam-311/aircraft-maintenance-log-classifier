export default function Button({ variant = 'primary', size = 'md', className = '', children, ...props }) {
  const variantClass =
    variant === 'primary'
      ? `bg-signal-blue text-white uppercase tracking-wide hover:bg-aviation-navy ${size === 'sm' ? 'px-20 py-8' : 'px-20 py-12'}`
      : variant === 'secondary'
      ? 'text-signal-blue border border-signal-blue uppercase tracking-wide text-xs px-16 py-8 hover:bg-signal-blue/5'
      : variant === 'ghost'
      ? 'text-text-slate px-16 py-8 hover:text-text-charcoal'
      : 'text-left border border-border-light hover:border-signal-blue px-16 py-8 w-full' // 'option'

  return (
    <button
      className={`text-sm font-medium rounded-button transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${variantClass} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
