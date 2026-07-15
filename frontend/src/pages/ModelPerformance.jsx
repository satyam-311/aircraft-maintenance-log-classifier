import { useEffect, useState } from 'react'
import { api, API_BASE } from '../lib/api'

function MetricCard({ label, value, target, meetsTarget }) {
  return (
    <div className="bg-surface-white border border-border-light rounded-card p-16">
      <div className="text-xs font-medium text-text-slate mb-8">{label}</div>
      <div className={`text-[28px] font-bold ${meetsTarget ? 'text-success' : 'text-severity-high'}`}>
        {value}
      </div>
      <div className="text-xs text-text-slate mt-4">Target: {target}</div>
    </div>
  )
}

function ClassifierSection({ title, metrics, confusionMatrixUrl, targetLabel, targetValue, actualKey, formatFn }) {
  if (!metrics) {
    return (
      <div className="bg-surface-white border border-border-light rounded-card p-16 text-text-slate text-sm">
        {title}: no evaluation results found yet.
      </div>
    )
  }

  const meetsTarget = metrics.meets_prd_target
  const actual = formatFn(metrics[actualKey])

  return (
    <div className="flex flex-col gap-16">
      <h2 className="text-[20px] font-semibold text-text-charcoal">{title}</h2>

      <div className="grid grid-cols-3 gap-16">
        <MetricCard label={targetLabel} value={actual} target={targetValue} meetsTarget={meetsTarget} />
        <MetricCard label="Macro Precision" value={metrics.test_macro_precision.toFixed(3)} target="—" meetsTarget />
        <MetricCard label="Macro Recall" value={metrics.test_macro_recall.toFixed(3)} target="—" meetsTarget />
      </div>

      {!meetsTarget && (
        <div className="text-sm text-severity-high bg-surface-white border border-severity-high/30 rounded-card p-16">
          This model does not currently meet the PRD's target. See the project write-up for the documented
          root cause and iteration history — this is a disclosed, known limitation, not a hidden gap.
        </div>
      )}

      <div className="bg-surface-white border border-border-light rounded-card p-16">
        <div className="text-xs font-medium text-text-slate mb-8">
          Confusion Matrix (Test Set, {metrics.n_test_examples} examples)
        </div>
        <img src={confusionMatrixUrl} alt={`${title} confusion matrix`} className="max-w-full rounded" />
      </div>
    </div>
  )
}

export default function ModelPerformance() {
  const [data, setData] = useState(null)

  useEffect(() => {
    api.modelPerformance().then(setData)
  }, [])

  if (!data) return <div className="text-text-slate text-sm">Loading model performance…</div>

  return (
    <div className="flex flex-col gap-32">
      <div>
        <h1 className="text-[28px] font-bold text-text-charcoal mb-8">Model Performance</h1>
        <p className="text-text-slate text-sm">
          Real results on the held-out test set — reported honestly, including where targets weren't met.
        </p>
      </div>

      <ClassifierSection
        title="ATA Chapter Classifier"
        metrics={data.ata_classifier}
        confusionMatrixUrl={`${API_BASE}/reports/ata_classifier/confusion_matrix.png`}
        targetLabel="Test Accuracy"
        targetValue="≥ 80%"
        actualKey="test_accuracy"
        formatFn={(v) => `${(v * 100).toFixed(1)}%`}
      />

      <ClassifierSection
        title="Severity Classifier"
        metrics={data.severity_classifier}
        confusionMatrixUrl={`${API_BASE}/reports/severity_classifier/confusion_matrix.png`}
        targetLabel="Macro F1"
        targetValue="≥ 0.70"
        actualKey="test_macro_f1"
        formatFn={(v) => v.toFixed(3)}
      />
    </div>
  )
}
