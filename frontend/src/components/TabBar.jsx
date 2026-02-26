import React from 'react';

/**
 * Horizontal tab bar with optional counts.
 *
 * @param {Object}   props
 * @param {Array}    props.tabs       - [{ key, label, count?, icon? }]
 * @param {string}   props.active     - Currently selected tab key
 * @param {function} props.onChange    - Called with tab key
 * @param {string}   [props.size]     - 'sm' | 'md' (default)
 */
export default function TabBar({ tabs = [], active, onChange, size = 'md' }) {
  return (
    <div className={`tab-bar ${size === 'sm' ? 'tab-bar-sm' : ''}`} role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          role="tab"
          aria-selected={active === tab.key}
          className={`tab-item ${active === tab.key ? 'active' : ''}`}
          onClick={() => onChange(tab.key)}
        >
          {tab.icon && <span className="tab-icon">{tab.icon}</span>}
          <span>{tab.label}</span>
          {tab.count != null && <span className="tab-count">{tab.count}</span>}
        </button>
      ))}
    </div>
  );
}
