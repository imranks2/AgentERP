import React from 'react';
import { Inbox } from 'lucide-react';

/**
 * Empty-state placeholder with icon, heading, description, and optional CTA.
 *
 * @param {Object}          props
 * @param {React.ReactNode} [props.icon]    - Override icon (default: Inbox)
 * @param {string}          props.title     - Bold heading
 * @param {string}          [props.description] - Muted helper text
 * @param {React.ReactNode} [props.action]  - CTA button or link
 */
export default function EmptyState({ icon, title, description, action }) {
  return (
    <div className="empty-placeholder">
      {icon || <Inbox size={48} />}
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      {action}
    </div>
  );
}
