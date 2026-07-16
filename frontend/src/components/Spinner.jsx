export default function Spinner({ className = 'w-16 h-16' }) {
  return (
    <span
      className={`inline-block ${className} border-2 border-current border-t-transparent rounded-full animate-spin`}
      aria-hidden="true"
    />
  )
}
