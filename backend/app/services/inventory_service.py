"""Inventory service – Products, Categories, Warehouses, Stock operations."""
from app import db
from app.models.inventory import (
    Product, ProductCategory, Warehouse, StockEntry, StockMovement,
)


class InventoryService:

    # ── Categories ───────────────────────────────────────────

    @staticmethod
    def list_categories(tenant_id, parent_id=None):
        q = ProductCategory.query.filter_by(tenant_id=tenant_id, is_active=True)
        if parent_id == 'root':
            q = q.filter(ProductCategory.parent_id.is_(None))
        elif parent_id:
            q = q.filter_by(parent_id=parent_id)
        return q.order_by(ProductCategory.sort_order, ProductCategory.name).all()

    @staticmethod
    def create_category(tenant_id, data):
        name = data.get('name', '').strip()
        if not name:
            raise ValueError('Name is required')
        slug = data.get('slug', name.lower().replace(' ', '-'))
        existing = ProductCategory.query.filter_by(tenant_id=tenant_id, slug=slug).first()
        if existing:
            raise ValueError(f"Category slug '{slug}' already exists")
        cat = ProductCategory(
            tenant_id=tenant_id, name=name, slug=slug,
            parent_id=data.get('parent_id'),
            description=data.get('description'),
            sort_order=data.get('sort_order', 0),
        )
        db.session.add(cat)
        db.session.commit()
        return cat

    @staticmethod
    def update_category(tenant_id, cat_id, data):
        cat = ProductCategory.query.filter_by(id=cat_id, tenant_id=tenant_id).first()
        if not cat:
            return None
        for f in ['name', 'slug', 'description', 'is_active', 'sort_order', 'parent_id']:
            if f in data:
                setattr(cat, f, data[f])
        db.session.commit()
        return cat

    @staticmethod
    def delete_category(tenant_id, cat_id):
        cat = ProductCategory.query.filter_by(id=cat_id, tenant_id=tenant_id).first()
        if not cat:
            raise ValueError('Category not found')
        db.session.delete(cat)
        db.session.commit()

    # ── Products ─────────────────────────────────────────────

    @staticmethod
    def list_products(tenant_id, category_id=None, search=None,
                      product_type=None, page=1, per_page=50):
        q = Product.query.filter_by(tenant_id=tenant_id, is_active=True)
        if category_id:
            q = q.filter_by(category_id=category_id)
        if product_type:
            q = q.filter_by(product_type=product_type)
        if search:
            like = f'%{search}%'
            q = q.filter(db.or_(
                Product.name.ilike(like),
                Product.sku.ilike(like),
                Product.barcode.ilike(like),
            ))
        total = q.count()
        products = q.order_by(Product.name)\
            .offset((page - 1) * per_page).limit(per_page).all()
        return products, total

    @staticmethod
    def get_product(tenant_id, product_id):
        return Product.query.filter_by(id=product_id, tenant_id=tenant_id).first()

    @staticmethod
    def create_product(tenant_id, data):
        name = data.get('name', '').strip()
        if not name:
            raise ValueError('Product name is required')
        sku = data.get('sku', '').strip() or None
        if sku:
            existing = Product.query.filter_by(tenant_id=tenant_id, sku=sku).first()
            if existing:
                raise ValueError(f"SKU '{sku}' already exists")
        product = Product(
            tenant_id=tenant_id, name=name, sku=sku,
            barcode=data.get('barcode'),
            description=data.get('description'),
            product_type=data.get('product_type', 'goods'),
            category_id=data.get('category_id'),
            sale_price=data.get('sale_price', 0),
            cost_price=data.get('cost_price', 0),
            currency=data.get('currency', 'USD'),
            tax_rate=data.get('tax_rate', 0),
            track_inventory=data.get('track_inventory', True),
            reorder_point=data.get('reorder_point', 0),
            reorder_qty=data.get('reorder_qty', 0),
            uom=data.get('uom', 'unit'),
            image_url=data.get('image_url'),
        )
        db.session.add(product)
        db.session.commit()
        return product

    @staticmethod
    def update_product(tenant_id, product_id, data):
        product = Product.query.filter_by(id=product_id, tenant_id=tenant_id).first()
        if not product:
            return None
        updatable = [
            'name', 'sku', 'barcode', 'description', 'product_type',
            'category_id', 'sale_price', 'cost_price', 'currency', 'tax_rate',
            'track_inventory', 'reorder_point', 'reorder_qty', 'uom',
            'is_active', 'image_url',
        ]
        for f in updatable:
            if f in data:
                if f == 'sku' and data[f]:
                    dup = Product.query.filter(
                        Product.tenant_id == tenant_id,
                        Product.sku == data[f],
                        Product.id != product_id,
                    ).first()
                    if dup:
                        raise ValueError(f"SKU '{data[f]}' already exists")
                setattr(product, f, data[f])
        db.session.commit()
        return product

    @staticmethod
    def delete_product(tenant_id, product_id):
        product = Product.query.filter_by(id=product_id, tenant_id=tenant_id).first()
        if not product:
            raise ValueError('Product not found')
        product.is_active = False  # soft delete
        db.session.commit()

    # ── Warehouses ───────────────────────────────────────────

    @staticmethod
    def list_warehouses(tenant_id):
        return Warehouse.query.filter_by(tenant_id=tenant_id, is_active=True)\
            .order_by(Warehouse.name).all()

    @staticmethod
    def create_warehouse(tenant_id, data):
        name = data.get('name', '').strip()
        if not name:
            raise ValueError('Warehouse name is required')
        code = data.get('code', '').strip() or None
        if code:
            existing = Warehouse.query.filter_by(tenant_id=tenant_id, code=code).first()
            if existing:
                raise ValueError(f"Warehouse code '{code}' already exists")
        wh = Warehouse(
            tenant_id=tenant_id, name=name, code=code,
            address=data.get('address'),
        )
        db.session.add(wh)
        db.session.commit()
        return wh

    @staticmethod
    def update_warehouse(tenant_id, wh_id, data):
        wh = Warehouse.query.filter_by(id=wh_id, tenant_id=tenant_id).first()
        if not wh:
            return None
        for f in ['name', 'code', 'address', 'is_active']:
            if f in data:
                setattr(wh, f, data[f])
        db.session.commit()
        return wh

    # ── Stock operations ─────────────────────────────────────

    @staticmethod
    def get_stock(tenant_id, product_id=None, warehouse_id=None):
        q = StockEntry.query.filter_by(tenant_id=tenant_id)
        if product_id:
            q = q.filter_by(product_id=product_id)
        if warehouse_id:
            q = q.filter_by(warehouse_id=warehouse_id)
        return q.all()

    @staticmethod
    def adjust_stock(tenant_id, product_id, warehouse_id, quantity,
                     movement_type='adjustment', reference_type=None,
                     reference_id=None, notes=None, user_id=None):
        """Adjust stock and create a movement record.

        quantity: positive = add, negative = subtract
        """
        entry = StockEntry.query.filter_by(
            tenant_id=tenant_id, product_id=product_id,
            warehouse_id=warehouse_id,
        ).first()
        if not entry:
            entry = StockEntry(
                tenant_id=tenant_id, product_id=product_id,
                warehouse_id=warehouse_id, quantity=0,
            )
            db.session.add(entry)

        entry.quantity += quantity
        if entry.quantity < 0:
            entry.quantity = 0  # prevent negative stock

        movement = StockMovement(
            tenant_id=tenant_id, product_id=product_id,
            warehouse_id=warehouse_id, movement_type=movement_type,
            quantity=quantity, reference_type=reference_type,
            reference_id=reference_id, notes=notes,
            created_by=user_id,
        )
        db.session.add(movement)
        db.session.commit()
        return entry, movement

    @staticmethod
    def get_movements(tenant_id, product_id=None, warehouse_id=None,
                      page=1, per_page=50):
        q = StockMovement.query.filter_by(tenant_id=tenant_id)
        if product_id:
            q = q.filter_by(product_id=product_id)
        if warehouse_id:
            q = q.filter_by(warehouse_id=warehouse_id)
        total = q.count()
        movements = q.order_by(StockMovement.created_at.desc())\
            .offset((page - 1) * per_page).limit(per_page).all()
        return movements, total

    @staticmethod
    def get_inventory_stats(tenant_id):
        products = Product.query.filter_by(tenant_id=tenant_id, is_active=True).count()
        warehouses = Warehouse.query.filter_by(tenant_id=tenant_id, is_active=True).count()
        categories = ProductCategory.query.filter_by(tenant_id=tenant_id, is_active=True).count()
        total_stock = db.session.query(db.func.coalesce(db.func.sum(StockEntry.quantity), 0))\
            .filter_by(tenant_id=tenant_id).scalar()
        low_stock = db.session.query(db.func.count(Product.id))\
            .outerjoin(StockEntry, db.and_(
                StockEntry.product_id == Product.id,
                StockEntry.tenant_id == tenant_id,
            ))\
            .filter(
                Product.tenant_id == tenant_id,
                Product.is_active == True,  # noqa
                Product.track_inventory == True,  # noqa
                Product.reorder_point > 0,
                db.or_(
                    StockEntry.quantity.is_(None),
                    StockEntry.quantity <= Product.reorder_point,
                ),
            ).scalar()
        return {
            'total_products': products,
            'total_warehouses': warehouses,
            'total_categories': categories,
            'total_stock_qty': int(total_stock),
            'low_stock_items': int(low_stock or 0),
        }
