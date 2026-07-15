import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, Legend } from 'recharts'
import { api } from '../lib/api'
import { ATA_CHAPTERS, SEVERITY_COLORS } from '../lib/constants'

function aggregateSeverityByMonth(rows) {
  const byMonth = {}
  for (const r of rows) {
    if (!byMonth[r.month]) byMonth[r.month] = { month: r.month }
    byMonth[r.month][r.severity] = (byMonth[r.month][r.severity] || 0) + r.count
  }
  return Object.values(byMonth).sort((a, b) => a.month.localeCompare(b.month))
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.stats().then(setStats).catch((e) => setError(e.message))
  }, [])

  if (error) {
    return (
      <div className="text-error text-sm">Couldn't load dashboard stats: {error}</div>
    )
  }

  if (!stats) {
    return <div className="text-text-slate text-sm">Loading dashboard…</div>
  }

  const systemData = stats.system_breakdown.map((s) => ({
    name: `${ATA_CHAPTERS[s.ata_chapter] || s.ata_chapter}`,
    code: s.ata_chapter,
    count: s.count,
  }))

  const severityTimeData = aggregateSeverityByMonth(stats.severity_over_time)

  return (
    <div className="flex flex-col gap-32">
      <div>
        <h1 className="text-[28px] font-bold text-text-charcoal mb-8">Dashboard</h1>
        <p className="text-text-slate text-sm">Corpus overview — maintenance narrative classification</p>
      </div>

      <div className="grid grid-cols-2 gap-16">
        <div className="bg-surface-white border border-border-light rounded-card p-16">
          <div className="text-xs font-medium text-text-slate mb-8">Total Reports</div>
          <div className="text-[28px] font-bold text-aviation-navy">{stats.total_reports.toLocaleString()}</div>
        </div>
        <div className="bg-surface-white border border-border-light rounded-card p-16">
          <div className="text-xs font-medium text-text-slate mb-8">Classified by Model</div>
          <div className="text-[28px] font-bold text-aviation-navy">{stats.total_classified.toLocaleString()}</div>
        </div>
      </div>

      <div className="bg-surface-white border border-border-light rounded-card p-16">
        <h2 className="text-[20px] font-semibold text-text-charcoal mb-16">Breakdown by System</h2>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={systemData} layout="vertical" margin={{ left: 40 }}>
            <XAxis type="number" stroke="#6B7280" fontSize={12} />
            <YAxis type="category" dataKey="code" width={50} stroke="#6B7280" fontSize={12} />
            <Tooltip
              formatter={(value, name, props) => [value, props.payload.name]}
              contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #D9DEE3' }}
            />
            <Bar dataKey="count" fill="#2E6E9E" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-surface-white border border-border-light rounded-card p-16">
        <h2 className="text-[20px] font-semibold text-text-charcoal mb-16">Severity Distribution Over Time</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={severityTimeData}>
            <XAxis dataKey="month" stroke="#6B7280" fontSize={12} />
            <YAxis stroke="#6B7280" fontSize={12} />
            <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #D9DEE3' }} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line type="monotone" dataKey="Low" stroke={SEVERITY_COLORS.Low} strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="Medium" stroke={SEVERITY_COLORS.Medium} strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="High" stroke={SEVERITY_COLORS.High} strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
