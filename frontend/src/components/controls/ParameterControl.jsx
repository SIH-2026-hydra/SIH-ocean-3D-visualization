import './ParameterControl.css';

export default function ParameterControl({ variables = [], selectedParameter, onChange }) {
  return (
    <section className="parameter-control glass-panel" aria-label="Ocean variable">
      <span className="parameter-control__label">Ocean variable</span>
      <div className="parameter-control__options">
        {variables.map((option) => (
          <label key={option.variable_name} className={selectedParameter === option.variable_name ? 'is-selected' : ''}>
            <input type="radio" name="ocean-variable" value={option.variable_name} checked={selectedParameter === option.variable_name} onChange={() => onChange(option.variable_name)} />
            <span>{option.display_name || option.variable_name}</span>
          </label>
        ))}
      </div>
    </section>
  );
}
