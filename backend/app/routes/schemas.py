"""Schema endpoint — exposes form/table definitions for dynamic UI generation."""
from flask import Blueprint, jsonify

schemas_bp = Blueprint('schemas', __name__)

# ── Field Schema Definitions ──────────────────────────

SCHEMAS = {
    # ── Inventory ──────────────────────────────────────
    'product': {
        'title': 'Product',
        'sections': [
            {
                'title': 'Basic Information',
                'columns': 2,
                'fields': [
                    {'name': 'name',         'label': 'Product Name', 'type': 'text',   'required': True},
                    {'name': 'sku',          'label': 'SKU',          'type': 'text',   'required': True},
                    {'name': 'barcode',      'label': 'Barcode',      'type': 'text'},
                    {'name': 'product_type', 'label': 'Type',         'type': 'select', 'required': True,
                     'options': [
                         {'value': 'goods',      'label': 'Goods'},
                         {'value': 'service',    'label': 'Service'},
                         {'value': 'consumable', 'label': 'Consumable'},
                     ], 'default': 'goods'},
                    {'name': 'category_id',  'label': 'Category',     'type': 'select', 'dynamic': 'categories'},
                    {'name': 'uom',          'label': 'Unit of Measure', 'type': 'select',
                     'options': [
                         {'value': 'unit', 'label': 'Unit'}, {'value': 'kg', 'label': 'Kilogram'},
                         {'value': 'g', 'label': 'Gram'}, {'value': 'l', 'label': 'Litre'},
                         {'value': 'ml', 'label': 'Millilitre'}, {'value': 'm', 'label': 'Metre'},
                         {'value': 'cm', 'label': 'Centimetre'}, {'value': 'pcs', 'label': 'Pieces'},
                         {'value': 'box', 'label': 'Box'}, {'value': 'pack', 'label': 'Pack'},
                         {'value': 'hr', 'label': 'Hour'},
                     ], 'default': 'unit'},
                ],
            },
            {
                'title': 'Pricing',
                'columns': 3,
                'fields': [
                    {'name': 'sale_price', 'label': 'Sale Price', 'type': 'number', 'min': 0, 'step': '0.01'},
                    {'name': 'cost_price', 'label': 'Cost Price', 'type': 'number', 'min': 0, 'step': '0.01'},
                    {'name': 'currency',   'label': 'Currency',   'type': 'select',
                     'options': [
                         {'value': 'USD', 'label': 'USD'}, {'value': 'EUR', 'label': 'EUR'},
                         {'value': 'GBP', 'label': 'GBP'}, {'value': 'INR', 'label': 'INR'},
                         {'value': 'AED', 'label': 'AED'}, {'value': 'SAR', 'label': 'SAR'},
                     ], 'default': 'USD'},
                    {'name': 'tax_rate',   'label': 'Tax Rate (%)', 'type': 'number', 'min': 0, 'max': 100, 'step': '0.01'},
                ],
            },
            {
                'title': 'Inventory',
                'columns': 2,
                'fields': [
                    {'name': 'track_inventory', 'label': 'Track Inventory', 'type': 'checkbox', 'default': True},
                    {'name': 'reorder_point',   'label': 'Reorder Point',   'type': 'number', 'min': 0},
                ],
            },
            {
                'title': 'Details',
                'columns': 1,
                'fields': [
                    {'name': 'description', 'label': 'Description', 'type': 'textarea'},
                ],
            },
        ],
    },

    'product_category': {
        'title': 'Product Category',
        'sections': [
            {
                'columns': 2,
                'fields': [
                    {'name': 'name',      'label': 'Category Name', 'type': 'text', 'required': True},
                    {'name': 'parent_id', 'label': 'Parent Category', 'type': 'select', 'dynamic': 'categories'},
                ],
            },
        ],
    },

    'warehouse': {
        'title': 'Warehouse',
        'sections': [
            {
                'columns': 2,
                'fields': [
                    {'name': 'name',    'label': 'Warehouse Name', 'type': 'text', 'required': True},
                    {'name': 'code',    'label': 'Code',           'type': 'text', 'required': True},
                    {'name': 'address', 'label': 'Address',        'type': 'textarea'},
                    {'name': 'is_active', 'label': 'Active',       'type': 'checkbox', 'default': True},
                ],
            },
        ],
    },

    # ── Sales ──────────────────────────────────────────
    'customer': {
        'title': 'Customer',
        'sections': [
            {
                'title': 'Contact Information',
                'columns': 2,
                'fields': [
                    {'name': 'name',    'label': 'Customer Name', 'type': 'text',  'required': True},
                    {'name': 'email',   'label': 'Email',         'type': 'email'},
                    {'name': 'phone',   'label': 'Phone',         'type': 'text'},
                    {'name': 'company', 'label': 'Company',       'type': 'text'},
                    {'name': 'tax_id',  'label': 'Tax ID',        'type': 'text'},
                ],
            },
            {
                'title': 'Address',
                'columns': 1,
                'fields': [
                    {'name': 'address', 'label': 'Address', 'type': 'textarea'},
                ],
            },
        ],
    },

    'quotation': {
        'title': 'Quotation',
        'sections': [
            {
                'columns': 2,
                'fields': [
                    {'name': 'customer_id', 'label': 'Customer',     'type': 'select', 'required': True, 'dynamic': 'customers'},
                    {'name': 'status',      'label': 'Status',       'type': 'select',
                     'options': [
                         {'value': 'draft', 'label': 'Draft'}, {'value': 'sent', 'label': 'Sent'},
                         {'value': 'accepted', 'label': 'Accepted'}, {'value': 'rejected', 'label': 'Rejected'},
                         {'value': 'expired', 'label': 'Expired'},
                     ], 'default': 'draft'},
                    {'name': 'valid_until', 'label': 'Valid Until',  'type': 'date'},
                    {'name': 'notes',       'label': 'Notes',        'type': 'textarea'},
                ],
            },
        ],
        'line_items': {
            'entity': 'quotation_item',
            'columns': [
                {'key': 'product_id', 'label': 'Product',    'type': 'select', 'dynamic': 'products', 'width': '30%'},
                {'key': 'quantity',   'label': 'Qty',         'type': 'number', 'width': '10%'},
                {'key': 'unit_price', 'label': 'Unit Price',  'type': 'number', 'width': '15%'},
                {'key': 'discount_pct', 'label': 'Disc %',    'type': 'number', 'width': '10%'},
                {'key': 'tax_rate',   'label': 'Tax %',       'type': 'number', 'width': '10%'},
                {'key': 'total',      'label': 'Total',       'type': 'computed', 'width': '15%'},
            ],
        },
    },

    'invoice': {
        'title': 'Invoice',
        'sections': [
            {
                'columns': 2,
                'fields': [
                    {'name': 'customer_id', 'label': 'Customer',    'type': 'select', 'required': True, 'dynamic': 'customers'},
                    {'name': 'status',      'label': 'Status',      'type': 'select',
                     'options': [
                         {'value': 'draft', 'label': 'Draft'}, {'value': 'sent', 'label': 'Sent'},
                         {'value': 'partial', 'label': 'Partial'}, {'value': 'paid', 'label': 'Paid'},
                         {'value': 'overdue', 'label': 'Overdue'}, {'value': 'cancelled', 'label': 'Cancelled'},
                     ], 'default': 'draft'},
                    {'name': 'due_date', 'label': 'Due Date', 'type': 'date'},
                    {'name': 'notes',    'label': 'Notes',    'type': 'textarea'},
                ],
            },
        ],
        'line_items': {
            'entity': 'invoice_item',
            'columns': [
                {'key': 'product_id', 'label': 'Product',    'type': 'select', 'dynamic': 'products', 'width': '30%'},
                {'key': 'quantity',   'label': 'Qty',         'type': 'number', 'width': '10%'},
                {'key': 'unit_price', 'label': 'Unit Price',  'type': 'number', 'width': '15%'},
                {'key': 'discount_pct', 'label': 'Disc %',    'type': 'number', 'width': '10%'},
                {'key': 'tax_rate',   'label': 'Tax %',       'type': 'number', 'width': '10%'},
                {'key': 'total',      'label': 'Total',       'type': 'computed', 'width': '15%'},
            ],
        },
    },

    'payment': {
        'title': 'Payment',
        'sections': [
            {
                'columns': 2,
                'fields': [
                    {'name': 'invoice_id',     'label': 'Invoice',        'type': 'select', 'required': True, 'dynamic': 'invoices'},
                    {'name': 'amount',         'label': 'Amount',         'type': 'number', 'required': True, 'min': 0, 'step': '0.01'},
                    {'name': 'payment_method', 'label': 'Payment Method', 'type': 'select',
                     'options': [
                         {'value': 'bank_transfer', 'label': 'Bank Transfer'},
                         {'value': 'cash', 'label': 'Cash'},
                         {'value': 'credit_card', 'label': 'Credit Card'},
                         {'value': 'cheque', 'label': 'Cheque'},
                         {'value': 'other', 'label': 'Other'},
                     ], 'default': 'bank_transfer'},
                    {'name': 'reference', 'label': 'Reference',  'type': 'text'},
                    {'name': 'date',      'label': 'Date',        'type': 'date'},
                    {'name': 'notes',     'label': 'Notes',       'type': 'textarea'},
                ],
            },
        ],
    },

    # ── Purchasing ─────────────────────────────────────
    'supplier': {
        'title': 'Supplier',
        'sections': [
            {
                'title': 'Contact Information',
                'columns': 2,
                'fields': [
                    {'name': 'name',          'label': 'Supplier Name',  'type': 'text',  'required': True},
                    {'name': 'email',         'label': 'Email',          'type': 'email'},
                    {'name': 'phone',         'label': 'Phone',          'type': 'text'},
                    {'name': 'company',       'label': 'Company',        'type': 'text'},
                    {'name': 'tax_id',        'label': 'Tax ID',         'type': 'text'},
                    {'name': 'payment_terms', 'label': 'Payment Terms',  'type': 'text'},
                ],
            },
            {
                'title': 'Address',
                'columns': 1,
                'fields': [
                    {'name': 'address', 'label': 'Address', 'type': 'textarea'},
                ],
            },
        ],
    },

    'purchase_order': {
        'title': 'Purchase Order',
        'sections': [
            {
                'columns': 2,
                'fields': [
                    {'name': 'supplier_id',  'label': 'Supplier',  'type': 'select', 'required': True, 'dynamic': 'suppliers'},
                    {'name': 'warehouse_id', 'label': 'Warehouse', 'type': 'select', 'dynamic': 'warehouses'},
                    {'name': 'status',       'label': 'Status',    'type': 'select',
                     'options': [
                         {'value': 'draft', 'label': 'Draft'}, {'value': 'sent', 'label': 'Sent'},
                         {'value': 'partial', 'label': 'Partial'}, {'value': 'received', 'label': 'Received'},
                         {'value': 'cancelled', 'label': 'Cancelled'},
                     ], 'default': 'draft'},
                    {'name': 'terms',   'label': 'Terms',     'type': 'textarea'},
                    {'name': 'notes',   'label': 'Notes',     'type': 'textarea'},
                ],
            },
        ],
        'line_items': {
            'entity': 'purchase_order_item',
            'columns': [
                {'key': 'product_id',   'label': 'Product',    'type': 'select', 'dynamic': 'products', 'width': '30%'},
                {'key': 'quantity',     'label': 'Qty',         'type': 'number', 'width': '10%'},
                {'key': 'unit_price',   'label': 'Unit Price',  'type': 'number', 'width': '15%'},
                {'key': 'discount_pct', 'label': 'Disc %',      'type': 'number', 'width': '10%'},
                {'key': 'tax_rate',     'label': 'Tax %',       'type': 'number', 'width': '10%'},
                {'key': 'total',        'label': 'Total',       'type': 'computed', 'width': '15%'},
            ],
        },
    },

    # ── Organisation ───────────────────────────────────
    'organisation_unit': {
        'title': 'Organisation Unit',
        'sections': [
            {
                'columns': 2,
                'fields': [
                    {'name': 'name',      'label': 'Unit Name', 'type': 'text',   'required': True},
                    {'name': 'code',      'label': 'Code',      'type': 'text'},
                    {'name': 'unit_type', 'label': 'Type',      'type': 'select', 'required': True,
                     'options': [
                         {'value': 'enterprise',     'label': 'Enterprise'},
                         {'value': 'legal_entity',   'label': 'Legal Entity'},
                         {'value': 'business_unit',  'label': 'Business Unit'},
                         {'value': 'branch',         'label': 'Branch'},
                         {'value': 'department',     'label': 'Department'},
                         {'value': 'project',        'label': 'Project'},
                         {'value': 'cost_center',    'label': 'Cost Center'},
                         {'value': 'team',           'label': 'Team'},
                     ]},
                    {'name': 'parent_id', 'label': 'Parent Unit', 'type': 'select', 'dynamic': 'org_units'},
                    {'name': 'is_active', 'label': 'Active',      'type': 'checkbox', 'default': True},
                ],
            },
        ],
    },
}

# ── Table column definitions ──────────────────────────

TABLE_SCHEMAS = {
    'product': {
        'columns': [
            {'key': 'name',         'label': 'Product',  'sortable': True, 'primary': True},
            {'key': 'sku',          'label': 'SKU',       'sortable': True},
            {'key': 'product_type', 'label': 'Type',      'sortable': True},
            {'key': 'sale_price',   'label': 'Sale Price', 'sortable': True, 'format': 'currency'},
            {'key': 'cost_price',   'label': 'Cost Price', 'sortable': True, 'format': 'currency'},
            {'key': 'uom',          'label': 'UOM'},
        ],
        'searchable': ['name', 'sku', 'barcode'],
    },
    'customer': {
        'columns': [
            {'key': 'name',    'label': 'Customer', 'sortable': True, 'primary': True},
            {'key': 'email',   'label': 'Email',    'sortable': True},
            {'key': 'phone',   'label': 'Phone'},
            {'key': 'company', 'label': 'Company',  'sortable': True},
        ],
        'searchable': ['name', 'email', 'company'],
    },
    'quotation': {
        'columns': [
            {'key': 'number',        'label': 'Number',   'sortable': True, 'primary': True},
            {'key': 'customer_name', 'label': 'Customer', 'sortable': True},
            {'key': 'status',        'label': 'Status',   'sortable': True, 'format': 'status'},
            {'key': 'total',         'label': 'Total',    'sortable': True, 'format': 'currency'},
            {'key': 'created_at',    'label': 'Date',     'sortable': True, 'format': 'date'},
        ],
        'searchable': ['number', 'customer_name'],
    },
    'invoice': {
        'columns': [
            {'key': 'number',        'label': 'Number',   'sortable': True, 'primary': True},
            {'key': 'customer_name', 'label': 'Customer', 'sortable': True},
            {'key': 'status',        'label': 'Status',   'sortable': True, 'format': 'status'},
            {'key': 'total',         'label': 'Total',    'sortable': True, 'format': 'currency'},
            {'key': 'balance_due',   'label': 'Balance',  'sortable': True, 'format': 'currency'},
            {'key': 'created_at',    'label': 'Date',     'sortable': True, 'format': 'date'},
        ],
        'searchable': ['number', 'customer_name'],
    },
    'supplier': {
        'columns': [
            {'key': 'name',    'label': 'Supplier', 'sortable': True, 'primary': True},
            {'key': 'email',   'label': 'Email',    'sortable': True},
            {'key': 'phone',   'label': 'Phone'},
            {'key': 'company', 'label': 'Company',  'sortable': True},
        ],
        'searchable': ['name', 'email', 'company'],
    },
    'purchase_order': {
        'columns': [
            {'key': 'number',        'label': 'Number',   'sortable': True, 'primary': True},
            {'key': 'supplier_name', 'label': 'Supplier', 'sortable': True},
            {'key': 'status',        'label': 'Status',   'sortable': True, 'format': 'status'},
            {'key': 'total',         'label': 'Total',    'sortable': True, 'format': 'currency'},
            {'key': 'created_at',    'label': 'Date',     'sortable': True, 'format': 'date'},
        ],
        'searchable': ['number', 'supplier_name'],
    },
}


@schemas_bp.route('/', methods=['GET'])
def list_schemas():
    """Return a list of available schema names."""
    return jsonify({
        'forms': list(SCHEMAS.keys()),
        'tables': list(TABLE_SCHEMAS.keys()),
    })


@schemas_bp.route('/forms/<entity>', methods=['GET'])
def get_form_schema(entity):
    """Return the form field schema for a given entity type."""
    schema = SCHEMAS.get(entity)
    if not schema:
        return jsonify({'error': f'Unknown entity: {entity}'}), 404
    return jsonify(schema)


@schemas_bp.route('/tables/<entity>', methods=['GET'])
def get_table_schema(entity):
    """Return the table column schema for a given entity type."""
    schema = TABLE_SCHEMAS.get(entity)
    if not schema:
        return jsonify({'error': f'Unknown entity: {entity}'}), 404
    return jsonify(schema)
