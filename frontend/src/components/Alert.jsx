import React from 'react';
import { CheckCircle, AlertTriangle, Info, XCircle, X } from 'lucide-react';

const ICON_MAP = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
};

/**
 * Inline alert bar with icon, message, and optional dismiss.
 *
 * @param {Object}  props
 * @param {string}  props.type      - 'success' | 'error' | 'warning' | 'info'
 * @param {string}  props.message   - Alert text
 * @param {Function} [props.onClose] - If provided, shows a close button
 */
export default function Alert({ type = 'info', message, onClose }) {
  const Icon = ICON_MAP[type] || Info;

  return (
    <div className={`alert-bar ${type}`} role="alert">
      <Icon size={18} />
      <span className="alert-bar-msg">{message}</span>
      {onClose && (
        <button className="alert-bar-close" onClick={onClose} aria-label="Dismiss">
          <X size={16} />
        </button>
      )}
    </div>
  );
}
