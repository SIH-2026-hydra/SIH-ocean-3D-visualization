import './ParameterControl.css';

const OPTIONS = [
  { value: 'temperature', label: 'Temperature' },
  { value: 'salinity', label: 'Salinity' },
  { value: 'current', label: 'Currents' },
];

export default function ParameterControl({ selectedParameter, onChange }) {
  return (
    <section className="parameter-control glass-panel" aria-label="Ocean variable">
      <span className="parameter-control__label">Ocean variable</span>
      <div className="parameter-control__options">
        {OPTIONS.map((option) => (
          <label key={option.value} className={selectedParameter === option.value ? 'is-selected' : ''}>
            <input type="radio" name="ocean-variable" value={option.value} checked={selectedParameter === option.value} onChange={() => onChange(option.value)} />
            <span>{option.label}</span>
          </label>
        ))}
      </div>
    </section>
  );
}
