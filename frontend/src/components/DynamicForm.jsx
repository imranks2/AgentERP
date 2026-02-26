import React from 'react';

/**
 * Schema-driven form renderer.
 *
 * Props:
 *  schema  : array of field definitions (see below)
 *  values  : { [fieldName]: value }
 *  onChange: (fieldName, value) => void
 *  onSubmit: () => void
 *  errors  : { [fieldName]: string }  (optional)
 *  columns : 1 | 2 | 3 | 4 (default auto)
 *  disabled: boolean
 *  sections: [{ title, fields }] — alternative grouped layout
 *
 * Field definition:
 *  { name, label, type, required?, placeholder?, options?, help?,
 *    full?, disabled?, hidden?, step?, min?, max?, rows? }
 *
 *  type: 'text' | 'email' | 'number' | 'password' | 'date' | 'select' |
 *        'textarea' | 'hidden' | 'custom'
 *  options (for select): [{ value, label }]
 *  render (for custom): (value, onChange, field) => ReactNode
 */
export default function DynamicForm({
  schema = [],
  values = {},
  onChange,
  errors = {},
  columns,
  disabled = false,
  sections,
}) {
  const renderField = (field) => {
    if (field.hidden) return null;

    const val = values[field.name] ?? '';
    const err = errors[field.name];
    const isDisabled = disabled || field.disabled;
    const cls = err ? ' error' : '';

    let input;
    switch (field.type) {
      case 'select':
        input = (
          <select
            className={`df-select${cls}`}
            value={val}
            onChange={(e) => onChange?.(field.name, e.target.value)}
            disabled={isDisabled}
          >
            {field.placeholder && <option value="">{field.placeholder}</option>}
            {(field.options || []).map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        );
        break;

      case 'textarea':
        input = (
          <textarea
            className={`df-textarea${cls}`}
            value={val}
            onChange={(e) => onChange?.(field.name, e.target.value)}
            placeholder={field.placeholder}
            rows={field.rows || 3}
            disabled={isDisabled}
          />
        );
        break;

      case 'custom':
        input = field.render?.(val, (v) => onChange?.(field.name, v), field) || null;
        break;

      case 'hidden':
        return null;

      default:
        input = (
          <input
            className={`df-input${cls}`}
            type={field.type || 'text'}
            value={val}
            onChange={(e) => onChange?.(field.name, e.target.value)}
            placeholder={field.placeholder}
            disabled={isDisabled}
            step={field.step}
            min={field.min}
            max={field.max}
          />
        );
    }

    return (
      <div key={field.name} className={`df-field${field.full ? ' full' : ''}`}>
        {field.label && (
          <label className="df-label">
            {field.label}
            {field.required && <span className="required">*</span>}
          </label>
        )}
        {input}
        {err && <span className="df-error">{err}</span>}
        {field.help && !err && <span className="df-help">{field.help}</span>}
      </div>
    );
  };

  const gridCls = columns ? `df-grid cols-${columns}` : 'df-grid';

  if (sections?.length) {
    return (
      <div className="df-form">
        {sections.map((section, idx) => (
          <div key={idx} className="df-section">
            {section.title && <div className="df-section-title">{section.title}</div>}
            <div className={gridCls}>
              {(section.fields || []).map(renderField)}
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="df-form">
      <div className={gridCls}>
        {schema.map(renderField)}
      </div>
    </div>
  );
}
