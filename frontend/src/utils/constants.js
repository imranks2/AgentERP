/**
 * Shared constants for the ERP application.
 */

/** Document status configurations with labels, colors, icons. */
export const STATUS_CONFIG = {
  // Generic
  draft:     { label: 'Draft',     color: 'secondary', bg: 'var(--gray-100)',    text: 'var(--gray-700)'   },
  active:    { label: 'Active',    color: 'success',   bg: 'var(--success-light)', text: '#065F46'         },
  inactive:  { label: 'Inactive',  color: 'secondary', bg: 'var(--gray-100)',    text: 'var(--gray-500)'   },

  // Sales / Quotation
  sent:      { label: 'Sent',      color: 'info',      bg: 'var(--info-light)',  text: '#1E40AF'           },
  accepted:  { label: 'Accepted',  color: 'success',   bg: 'var(--success-light)', text: '#065F46'         },
  rejected:  { label: 'Rejected',  color: 'danger',    bg: 'var(--danger-light)', text: '#991B1B'          },
  converted: { label: 'Converted', color: 'info',      bg: '#E0E7FF',           text: '#3730A3'           },
  expired:   { label: 'Expired',   color: 'secondary', bg: 'var(--gray-100)',    text: 'var(--gray-500)'   },

  // Invoice / Payment
  partial:   { label: 'Partial',   color: 'warning',   bg: 'var(--warning-light)', text: '#92400E'         },
  paid:      { label: 'Paid',      color: 'success',   bg: 'var(--success-light)', text: '#065F46'         },
  overdue:   { label: 'Overdue',   color: 'danger',    bg: 'var(--danger-light)', text: '#991B1B'          },
  cancelled: { label: 'Cancelled', color: 'secondary', bg: 'var(--gray-100)',    text: 'var(--gray-500)'   },

  // PO
  received:  { label: 'Received',  color: 'success',   bg: 'var(--success-light)', text: '#065F46'         },

  // Tenant
  trial:     { label: 'Trial',     color: 'info',      bg: 'var(--info-light)',  text: '#1E40AF'           },
  suspended: { label: 'Suspended', color: 'warning',   bg: 'var(--warning-light)', text: '#92400E'         },
  churned:   { label: 'Churned',   color: 'danger',    bg: 'var(--danger-light)', text: '#991B1B'          },
};

/** Payment method options */
export const PAYMENT_METHODS = [
  { value: 'bank_transfer', label: 'Bank Transfer' },
  { value: 'cash',          label: 'Cash' },
  { value: 'credit_card',   label: 'Credit Card' },
  { value: 'cheque',        label: 'Cheque' },
  { value: 'other',         label: 'Other' },
];

/** Product type options */
export const PRODUCT_TYPES = [
  { value: 'goods',      label: 'Goods' },
  { value: 'service',    label: 'Service' },
  { value: 'consumable', label: 'Consumable' },
];

/** Unit of measure options */
export const UOM_OPTIONS = [
  { value: 'unit',  label: 'Unit' },
  { value: 'kg',    label: 'Kilogram' },
  { value: 'g',     label: 'Gram' },
  { value: 'l',     label: 'Litre' },
  { value: 'ml',    label: 'Millilitre' },
  { value: 'm',     label: 'Metre' },
  { value: 'cm',    label: 'Centimetre' },
  { value: 'pcs',   label: 'Pieces' },
  { value: 'box',   label: 'Box' },
  { value: 'pack',  label: 'Pack' },
  { value: 'hr',    label: 'Hour' },
];

/** Currency options */
export const CURRENCIES = [
  { value: 'USD', label: 'USD – US Dollar' },
  { value: 'EUR', label: 'EUR – Euro' },
  { value: 'GBP', label: 'GBP – British Pound' },
  { value: 'INR', label: 'INR – Indian Rupee' },
  { value: 'AED', label: 'AED – UAE Dirham' },
  { value: 'SAR', label: 'SAR – Saudi Riyal' },
  { value: 'CAD', label: 'CAD – Canadian Dollar' },
  { value: 'AUD', label: 'AUD – Australian Dollar' },
  { value: 'JPY', label: 'JPY – Japanese Yen' },
  { value: 'CNY', label: 'CNY – Chinese Yuan' },
];

/** Sidebar navigation structure */
export const NAV_ITEMS = [
  { key: 'overview',      label: 'Dashboard',     icon: 'LayoutDashboard', path: '/dashboard' },
  { key: 'organisation',  label: 'Organisation',  icon: 'Network',         path: '/organisation' },
  { key: 'modules',       label: 'Modules',       icon: 'Puzzle',          path: '/modules' },
  { type: 'divider' },
  { type: 'label', label: 'ERP Modules' },
  { key: 'inventory',     label: 'Inventory',     icon: 'Box',             path: '/inventory' },
  { key: 'sales',         label: 'Sales',         icon: 'ShoppingCart',    path: '/sales' },
  { key: 'purchasing',    label: 'Purchasing',    icon: 'Truck',           path: '/purchasing' },
  { key: 'accounting',    label: 'Accounting',    icon: 'BookOpen',        path: '/accounting' },
  { key: 'crm',           label: 'CRM',           icon: 'Target',          path: '/crm' },
  { key: 'hr',            label: 'HR',            icon: 'UserCheck',       path: '/hr' },
  { type: 'divider' },
  { type: 'label', label: 'Administration' },
  { key: 'users',         label: 'Users & Access', icon: 'Users',          path: '/users' },
  { key: 'activity',      label: 'Activity',      icon: 'Activity',        path: '/activity' },
  { key: 'subscription',  label: 'Subscription',  icon: 'CreditCard',     path: '/dashboard' },
  { key: 'settings',      label: 'Settings',      icon: 'Settings',       path: '/dashboard' },
  { type: 'divider' },
  { key: 'profile',       label: 'My Profile',    icon: 'User',           path: '/profile' },
];

/** Keyboard shortcuts */
export const SHORTCUTS = {
  COMMAND_PALETTE: { key: 'k', meta: true, label: '⌘K' },
  SEARCH:         { key: '/', label: '/' },
  ESCAPE:         { key: 'Escape', label: 'Esc' },
};
