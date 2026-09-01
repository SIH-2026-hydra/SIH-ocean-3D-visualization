import './ObservationToggle.css';

export default function ObservationToggle({ checked, onChange }) {
  return <label className="observation-toggle glass-panel"><span>OBSERVATIONS</span><input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} /><b>{checked ? 'On' : 'Off'}</b></label>;
}
