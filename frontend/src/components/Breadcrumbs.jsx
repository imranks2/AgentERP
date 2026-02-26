import React from 'react';
import { ChevronRight, Home } from 'lucide-react';

/**
 * Breadcrumbs component with path items and optional icon.
 *
 * Usage:
 *  <Breadcrumbs items={[
 *    { label: 'Dashboard', onClick: () => navigate('/dashboard') },
 *    { label: 'Inventory', onClick: () => setTab('products') },
 *    { label: 'Products' },  // current (no onClick)
 *  ]} />
 */
function Breadcrumbs({ items = [], showHome = true }) {
  if (!items.length) return null;

  const allItems = showHome
    ? [{ label: 'Home', icon: Home, onClick: items[0]?.onClick }, ...items]
    : items;

  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb">
      {allItems.map((item, idx) => {
        const isLast = idx === allItems.length - 1;
        const Icon = item.icon;
        return (
          <span className="breadcrumb-item" key={idx}>
            {idx > 0 && <ChevronRight size={12} className="breadcrumb-separator" />}
            {isLast ? (
              <span className="breadcrumb-current">
                {Icon && <Icon size={13} style={{ marginRight: 3, verticalAlign: 'text-bottom' }} />}
                {item.label}
              </span>
            ) : (
              <button className="breadcrumb-link" onClick={item.onClick}>
                {Icon && <Icon size={13} style={{ marginRight: 3, verticalAlign: 'text-bottom' }} />}
                {item.label}
              </button>
            )}
          </span>
        );
      })}
    </nav>
  );
}

export default Breadcrumbs;
