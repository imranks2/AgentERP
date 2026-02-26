/**
 * Formatting utilities used across all ERP modules.
 */

/**
 * Format a number as currency.
 * @param {number} amount
 * @param {string} currency - ISO currency code (default 'USD')
 * @returns {string}
 */
export function formatCurrency(amount, currency = 'USD') {
  if (amount == null || isNaN(amount)) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

/**
 * Format a date string to a readable format.
 * @param {string|Date} value
 * @param {'short'|'medium'|'long'} style
 * @returns {string}
 */
export function formatDate(value, style = 'medium') {
  if (!value) return '—';
  const d = typeof value === 'string' ? new Date(value) : value;
  if (isNaN(d.getTime())) return '—';
  const opts = {
    short: { month: 'numeric', day: 'numeric', year: '2-digit' },
    medium: { month: 'short', day: 'numeric', year: 'numeric' },
    long: { weekday: 'short', month: 'long', day: 'numeric', year: 'numeric' },
  };
  return d.toLocaleDateString('en-US', opts[style] || opts.medium);
}

/**
 * Format a date+time string.
 * @param {string|Date} value
 * @returns {string}
 */
export function formatDateTime(value) {
  if (!value) return '—';
  const d = typeof value === 'string' ? new Date(value) : value;
  if (isNaN(d.getTime())) return '—';
  return d.toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: 'numeric', minute: '2-digit',
  });
}

/**
 * Format a number with locale separators.
 * @param {number} value
 * @param {number} decimals
 * @returns {string}
 */
export function formatNumber(value, decimals = 0) {
  if (value == null || isNaN(value)) return '—';
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/**
 * Convert a number to a compact string (1.2K, 3.4M, etc.)
 * @param {number} value
 * @returns {string}
 */
export function formatCompact(value) {
  if (value == null || isNaN(value)) return '—';
  return new Intl.NumberFormat('en-US', { notation: 'compact' }).format(value);
}

/**
 * Truncate a string with ellipsis.
 * @param {string} str
 * @param {number} max
 * @returns {string}
 */
export function truncate(str, max = 40) {
  if (!str || str.length <= max) return str || '';
  return str.slice(0, max) + '…';
}

/**
 * Capitalise first letter of each word.
 * @param {string} str
 * @returns {string}
 */
export function titleCase(str) {
  if (!str) return '';
  return str.replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Return a human-readable time-ago string.
 * @param {string|Date} value
 * @returns {string}
 */
export function timeAgo(value) {
  if (!value) return '';
  const d = typeof value === 'string' ? new Date(value) : value;
  const seconds = Math.floor((Date.now() - d.getTime()) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return formatDate(d, 'short');
}
