"""Product & Category models – shared across Inventory, Sales, Purchasing."""
import uuid
from datetime import datetime, timezone
from app import db


class ProductCategory(db.Model):
    """Hierarchical product category."""
    __tablename__ = 'product_categories'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'),
                          nullable=False, index=True)
    parent_id = db.Column(db.String(36), db.ForeignKey('product_categories.id'),
                          nullable=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)

    children = db.relationship('ProductCategory',
                               backref=db.backref('parent', remote_side=[id]),
                               lazy='dynamic')
    products = db.relationship('Product', backref='category', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'slug', name='uq_category_tenant_slug'),
    )

    def to_dict(self):
        return {
            'id': self.id, 'tenant_id': self.tenant_id,
            'parent_id': self.parent_id,
            'parent_name': self.parent.name if self.parent else None,
            'name': self.name,
            'slug': self.slug, 'description': self.description,
            'is_active': self.is_active, 'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat(),
        }


class Product(db.Model):
    """Central product/item model used across all ERP modules."""
    __tablename__ = 'products'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'),
                          nullable=False, index=True)
    category_id = db.Column(db.String(36), db.ForeignKey('product_categories.id'),
                            nullable=True)

    # Identification
    name = db.Column(db.String(255), nullable=False)
    sku = db.Column(db.String(100), nullable=True)
    barcode = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    product_type = db.Column(db.String(20), nullable=False, default='goods',
                             doc='goods | service | consumable')

    # Pricing
    sale_price = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    cost_price = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    currency = db.Column(db.String(3), nullable=False, default='USD')
    tax_rate = db.Column(db.Numeric(5, 2), nullable=False, default=0)

    # Inventory
    track_inventory = db.Column(db.Boolean, nullable=False, default=True)
    reorder_point = db.Column(db.Integer, nullable=False, default=0)
    reorder_qty = db.Column(db.Integer, nullable=False, default=0)

    # UOM
    uom = db.Column(db.String(20), nullable=False, default='unit',
                     doc='unit | kg | liter | meter | box | dozen')

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    image_url = db.Column(db.String(500), nullable=True)
    metadata_ = db.Column('metadata', db.JSON, default=dict)

    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    stock_entries = db.relationship('StockEntry', backref='product', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'sku', name='uq_product_tenant_sku'),
    )

    VALID_TYPES = ['goods', 'service', 'consumable']
    VALID_UOMS = ['unit', 'kg', 'liter', 'meter', 'box', 'dozen', 'pair', 'set']

    def to_dict(self, include_stock=False):
        data = {
            'id': self.id, 'tenant_id': self.tenant_id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'name': self.name, 'sku': self.sku, 'barcode': self.barcode,
            'description': self.description, 'product_type': self.product_type,
            'sale_price': float(self.sale_price), 'cost_price': float(self.cost_price),
            'currency': self.currency, 'tax_rate': float(self.tax_rate),
            'track_inventory': self.track_inventory,
            'reorder_point': self.reorder_point, 'reorder_qty': self.reorder_qty,
            'uom': self.uom, 'is_active': self.is_active,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
        if include_stock:
            data['total_stock'] = sum(s.quantity for s in self.stock_entries.filter_by(tenant_id=self.tenant_id))
        return data


class Warehouse(db.Model):
    """Physical or logical warehouse / storage location."""
    __tablename__ = 'warehouses'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'),
                          nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(50), nullable=True)
    address = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)

    stock_entries = db.relationship('StockEntry', backref='warehouse', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'code', name='uq_warehouse_tenant_code'),
    )

    def to_dict(self):
        return {
            'id': self.id, 'tenant_id': self.tenant_id,
            'name': self.name, 'code': self.code,
            'address': self.address, 'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
        }


class StockEntry(db.Model):
    """Current stock level per product per warehouse."""
    __tablename__ = 'stock_entries'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'),
                          nullable=False, index=True)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    warehouse_id = db.Column(db.String(36), db.ForeignKey('warehouses.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    reserved_qty = db.Column(db.Integer, nullable=False, default=0)

    updated_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'product_id', 'warehouse_id',
                            name='uq_stock_product_warehouse'),
    )

    def to_dict(self):
        return {
            'id': self.id, 'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'warehouse_id': self.warehouse_id,
            'warehouse_name': self.warehouse.name if self.warehouse else None,
            'quantity': self.quantity,
            'reserved_qty': self.reserved_qty,
            'available_qty': self.quantity - self.reserved_qty,
        }


class StockMovement(db.Model):
    """Audit trail for every stock change."""
    __tablename__ = 'stock_movements'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'),
                          nullable=False, index=True)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    warehouse_id = db.Column(db.String(36), db.ForeignKey('warehouses.id'), nullable=False)
    movement_type = db.Column(db.String(30), nullable=False,
                              doc='in | out | adjustment | transfer | sale | purchase_receipt')
    quantity = db.Column(db.Integer, nullable=False)
    reference_type = db.Column(db.String(50), nullable=True, doc='invoice | purchase_order | manual')
    reference_id = db.Column(db.String(36), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)

    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)

    product = db.relationship('Product', backref='movements')
    warehouse = db.relationship('Warehouse')
    user = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id, 'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'warehouse_id': self.warehouse_id,
            'warehouse_name': self.warehouse.name if self.warehouse else None,
            'movement_type': self.movement_type,
            'quantity': self.quantity,
            'reference_type': self.reference_type,
            'reference_id': self.reference_id,
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
        }
