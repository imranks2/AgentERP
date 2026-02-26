import React from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { formatCurrency } from '../utils/formatters';

/**
 * Editable line-items table with auto-calculated totals.
 *
 * @param {Object}   props
 * @param {Array}    props.columns   - [{ key, label, type?, options?, width?, readOnly? }]
 *   type: 'text' | 'number' | 'select' | 'computed'  (default 'text')
 * @param {Array}    props.rows      - Array of row objects
 * @param {Function} props.onChange  - (rowIndex, field, value) => void
 * @param {Function} props.onAdd    - () => void
 * @param {Function} props.onRemove - (rowIndex) => void
 * @param {string}   [props.currency] - Currency code for formatting (default 'USD')
 * @param {Array}    [props.totals]  - [{ label, value, grand? }]
 */
export default function LineItems({
  columns = [],
  rows = [],
  onChange,
  onAdd,
  onRemove,
  currency = 'USD',
  totals = [],
}) {
  const renderCell = (row, col, rowIdx) => {
    const val = row[col.key];

    if (col.type === 'computed') {
      return (
        <span className="text-right" style={{ display: 'block' }}>
          {typeof val === 'number' ? formatCurrency(val, currency) : val ?? '—'}
        </span>
      );
    }

    if (col.readOnly) {
      return <span>{val ?? ''}</span>;
    }

    if (col.type === 'select') {
      return (
        <select
          value={val ?? ''}
          onChange={(e) => onChange(rowIdx, col.key, e.target.value)}
        >
          <option value="">Select…</option>
          {(col.options || []).map((o) => (
            <option key={typeof o === 'string' ? o : o.value} value={typeof o === 'string' ? o : o.value}>
              {typeof o === 'string' ? o : o.label}
            </option>
          ))}
        </select>
      );
    }

    if (col.type === 'number') {
      return (
        <input
          type="number"
          min="0"
          step="any"
          value={val ?? ''}
          onChange={(e) => onChange(rowIdx, col.key, parseFloat(e.target.value) || 0)}
          style={{ textAlign: 'right' }}
        />
      );
    }

    // default: text
    return (
      <input
        type="text"
        value={val ?? ''}
        onChange={(e) => onChange(rowIdx, col.key, e.target.value)}
      />
    );
  };

  return (
    <div>
      <div className="li-table-wrap">
        <table className="li-table">
          <thead>
            <tr>
              <th style={{ width: 36 }}>#</th>
              {columns.map((c) => (
                <th key={c.key} style={c.width ? { width: c.width } : undefined}>
                  {c.label}
                </th>
              ))}
              <th style={{ width: 40 }} />
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => (
              <tr key={idx}>
                <td style={{ color: 'var(--gray-400)', fontSize: '0.75rem' }}>{idx + 1}</td>
                {columns.map((col) => (
                  <td key={col.key}>{renderCell(row, col, idx)}</td>
                ))}
                <td>
                  <button
                    className="remove-row"
                    onClick={() => onRemove(idx)}
                    title="Remove line"
                  >
                    <Trash2 size={15} />
                  </button>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td
                  colSpan={columns.length + 2}
                  style={{ textAlign: 'center', color: 'var(--gray-400)', padding: '1.5rem' }}
                >
                  No line items yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <button className="li-add-row" onClick={onAdd}>
        <Plus size={15} /> Add line
      </button>

      {totals.length > 0 && (
        <div className="li-totals">
          <table>
            <tbody>
              {totals.map((t, i) => (
                <tr key={i} className={t.grand ? 'grand' : ''}>
                  <td className="label">{t.label}</td>
                  <td className="value">
                    {typeof t.value === 'number' ? formatCurrency(t.value, currency) : t.value}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
