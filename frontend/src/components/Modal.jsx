import React, { useEffect, useCallback, useRef, useState } from 'react';
import { X } from 'lucide-react';

/**
 * Reusable Modal component with enter/exit animations.
 *
 * Props:
 *  - open       : boolean
 *  - onClose    : () => void
 *  - title      : string
 *  - size       : 'sm' | 'md' | 'lg' | 'xl'  (default 'md')
 *  - footer     : ReactNode (optional — rendered in the footer bar)
 *  - children   : ReactNode (body content)
 *  - closeOnOverlay : boolean (default true)
 *  - showClose  : boolean (default true)
 */
export default function Modal({
  open,
  onClose,
  title,
  size = 'md',
  footer,
  children,
  closeOnOverlay = true,
  showClose = true,
}) {
  const [visible, setVisible] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const backdropRef = useRef(null);

  // Enter / exit lifecycle
  useEffect(() => {
    if (open) {
      setVisible(true);
      setLeaving(false);
    } else if (visible) {
      setLeaving(true);
      const timer = setTimeout(() => {
        setVisible(false);
        setLeaving(false);
      }, 160);
      return () => clearTimeout(timer);
    }
  }, [open]); // eslint-disable-next-line

  // Close on Escape
  const handleKey = useCallback(
    (e) => {
      if (e.key === 'Escape') onClose?.();
    },
    [onClose],
  );

  useEffect(() => {
    if (visible) {
      document.addEventListener('keydown', handleKey);
      document.body.style.overflow = 'hidden';
      return () => {
        document.removeEventListener('keydown', handleKey);
        document.body.style.overflow = '';
      };
    }
  }, [visible, handleKey]);

  if (!visible) return null;

  return (
    <div
      className={`modal-backdrop${leaving ? ' leaving' : ''}`}
      ref={backdropRef}
      onClick={(e) => {
        if (closeOnOverlay && e.target === backdropRef.current) onClose?.();
      }}
    >
      <div className={`modal-dialog ${size}`} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-dialog-header">
          <h3>{title}</h3>
          {showClose && (
            <button className="modal-dialog-close" onClick={onClose} aria-label="Close">
              <X size={18} />
            </button>
          )}
        </div>

        {/* Body */}
        <div className="modal-dialog-body">{children}</div>

        {/* Footer */}
        {footer && <div className="modal-dialog-footer">{footer}</div>}
      </div>
    </div>
  );
}
