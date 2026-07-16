import Spinner from './Spinner'

export default function LoadingState({ label = 'Loading…' }) {
  return (
    <div className="flex items-center justify-center gap-8 text-text-slate text-sm py-32">
      <Spinner />
      {label}
    </div>
  )
}
