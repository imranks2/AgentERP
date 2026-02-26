import React from 'react';

/**
 * Horizontal row of compact stat tiles.
 *
 * @param {Object}   props
 * @param {Array}    props.stats - [{ label, value, icon?, iconColor? }]
 *   iconColor: 'blue' | 'green' | 'orange' | 'purple' | 'red'
 */
export default function StatCards({ stats = [] }) {
  return (
    <div className="stat-row">
      {stats.map((s, i) => (
        <div key={i} className="stat-tile">
          {s.icon && (
            <div className={`stat-tile-icon ${s.iconColor || ''}`}>
              {s.icon}
            </div>
          )}
          <div className="stat-tile-data">
            <div className="stat-tile-value">{s.value ?? '—'}</div>
            <div className="stat-tile-label">{s.label}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
