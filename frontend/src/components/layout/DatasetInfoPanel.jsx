import './DatasetInfoPanel.css';

const formatCoverage = (coverage) => {
  if (!coverage) return 'Unavailable';
  const values = [coverage.min_latitude, coverage.max_latitude, coverage.min_longitude, coverage.max_longitude];
  return values.every(Number.isFinite) ? `${values[0]}° to ${values[1]}° lat · ${values[2]}° to ${values[3]}° lon` : 'Unavailable';
};

export default function DatasetInfoPanel({ dataset, coverage, metadata }) {
  if (!dataset) return null;
  const depths = dataset.available_depth_levels || [];
  const time = dataset.temporal_coverage || {};
  return (
    <aside className="dataset-info glass-panel" aria-label="Scientific dataset information">
      <div className="dataset-info__eyebrow">OPERATIONAL DATASET · LIVE LOCAL STAGING</div>
      <h2>{dataset.model || dataset.dataset_id}</h2>
      <div className="dataset-info__row"><span>Dataset</span><strong>{dataset.dataset_id}</strong></div>
      <div className="dataset-info__row"><span>Provider</span><strong>{dataset.provider}</strong></div>
      <div className="dataset-info__row"><span>Product</span><strong>{dataset.product}</strong></div>
      <div className="dataset-info__row"><span>Forecast cycle</span><strong>{dataset.forecast_cycle || 'Not supplied'}</strong></div>
      <div className="dataset-info__row"><span>Coverage</span><strong>{formatCoverage(coverage?.spatial_coverage || dataset.spatial_coverage)}</strong></div>
      <div className="dataset-info__row"><span>Time</span><strong>{time.start || '—'} to {time.end || '—'}</strong></div>
      <div className="dataset-info__row"><span>Depth</span><strong>{depths.length ? `${Math.min(...depths)} to ${Math.max(...depths)} m` : 'Unavailable'}</strong></div>
      <div className="dataset-info__row"><span>Resolution</span><strong>{metadata?.gridResolution || dataset.metadata?.resolution || 'Backend grid'}</strong></div>
    </aside>
  );
}
