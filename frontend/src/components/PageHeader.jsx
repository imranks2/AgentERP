import React from 'react';

/**
 * Page title bar with optional subtitle and action buttons.
 *
 * @param {Object}        props
 * @param {string}        props.title    - Page heading
 * @param {string}        [props.subtitle] - Optional description line
 * @param {React.ReactNode} [props.actions] - Right-side action buttons
 */
export default function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="page-title-bar">
      <div>
        <h1>{title}</h1>
        {subtitle && <div className="subtitle">{subtitle}</div>}
      </div>
      {actions && <div className="page-title-actions">{actions}</div>}
    </div>
  );
}
