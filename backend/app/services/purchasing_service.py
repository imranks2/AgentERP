"""Purchasing service – Suppliers, Purchase Orders, Goods Receipt.

Integration: Receiving goods auto-adjusts inventory stock via InventoryService.
"""
from datetime import datetime, timezone
from app import db
from app.models.purchasing import Supplier, PurchaseOrder, PurchaseOrderItem
from app.models.inventory import Product
from app.services.inventory_service import InventoryService


class PurchasingService:

    # ── Suppliers ────────────────────────────────────────────

    @staticmethod
    def list_suppliers(tenant_id, search=None, page=1, per_page=50):
        q = Supplier.query.filter_by(tenant_id=tenant_id, is_active=True)
        if search:
            like = f'%{search}%'
            q = q.filter(db.or_(
                Supplier.name.ilike(like),
                Supplier.email.ilike(like),
                Supplier.company.ilike(like),
            ))
        total = q.count()
        suppliers = q.order_by(Supplier.name)\
            .offset((page - 1) * per_page).limit(per_page).all()
        return suppliers, total

    @staticmethod
    def get_supplier(tenant_id, supplier_id):
        return Supplier.query.filter_by(id=supplier_id, tenant_id=tenant_id).first()

    @staticmethod
    def create_supplier(tenant_id, data):
        name = data.get('name', '').strip()
        if not name:
            raise ValueError('Supplier name is required')
        supplier = Supplier(
            tenant_id=tenant_id, name=name,
            email=data.get('email'), phone=data.get('phone'),
            company=data.get('company'), address=data.get('address'),
            tax_id=data.get('tax_id'),
            payment_terms=data.get('payment_terms'),
            notes=data.get('notes'),
        )
        db.session.add(supplier)
        db.session.commit()
        return supplier

    @staticmethod
    def update_supplier(tenant_id, supplier_id, data):
        sup = Supplier.query.filter_by(id=supplier_id, tenant_id=tenant_id).first()
        if not sup:
            return None
        for f in ['name', 'email', 'phone', 'company', 'address', 'tax_id',
                   'payment_terms', 'notes', 'is_active']:
            if f in data:
                setattr(sup, f, data[f])
        db.session.commit()
        return sup

    # ── Sequence number ──────────────────────────────────────

    @staticmethod
    def _next_number(tenant_id):
        last = db.session.query(db.func.max(PurchaseOrder.number))\
            .filter_by(tenant_id=tenant_id).scalar()
        prefix = 'PO-'
        if last and last.startswith(prefix):
            try:
                num = int(last[len(prefix):]) + 1
            except ValueError:
                num = 1
        else:
            num = 1
        return f'{prefix}{num:05d}'

    # ── Purchase Orders ──────────────────────────────────────

    @staticmethod
    def list_purchase_orders(tenant_id, status=None, supplier_id=None,
                              page=1, per_page=50):
        q = PurchaseOrder.query.filter_by(tenant_id=tenant_id)
        if status:
            q = q.filter_by(status=status)
        if supplier_id:
            q = q.filter_by(supplier_id=supplier_id)
        total = q.count()
        orders = q.order_by(PurchaseOrder.created_at.desc())\
            .offset((page - 1) * per_page).limit(per_page).all()
        return orders, total

    @staticmethod
    def get_purchase_order(tenant_id, po_id):
        return PurchaseOrder.query.filter_by(id=po_id, tenant_id=tenant_id).first()

    @staticmethod
    def create_purchase_order(tenant_id, data, user_id=None):
        supplier_id = data.get('supplier_id')
        if not supplier_id:
            raise ValueError('Supplier is required')
        sup = Supplier.query.filter_by(id=supplier_id, tenant_id=tenant_id).first()
        if not sup:
            raise ValueError('Supplier not found')

        warehouse_id = data.get('warehouse_id')
        if not warehouse_id:
            raise ValueError('Destination warehouse is required')

        number = PurchasingService._next_number(tenant_id)
        po = PurchaseOrder(
            tenant_id=tenant_id, supplier_id=supplier_id,
            warehouse_id=warehouse_id, number=number,
            date=data.get('date', datetime.now(timezone.utc).date()),
            expected_date=data.get('expected_date'),
            notes=data.get('notes'), terms=data.get('terms'),
            currency=data.get('currency', 'USD'),
            discount_amount=data.get('discount_amount', 0),
            created_by=user_id,
        )
        db.session.add(po)
        db.session.flush()

        for idx, item_data in enumerate(data.get('items', [])):
            product = Product.query.filter_by(
                id=item_data['product_id'], tenant_id=tenant_id
            ).first()
            if not product:
                raise ValueError(f"Product not found: {item_data['product_id']}")
            item = PurchaseOrderItem(
                purchase_order_id=po.id,
                product_id=product.id,
                description=item_data.get('description', product.name),
                quantity=item_data.get('quantity', 1),
                unit_price=item_data.get('unit_price', float(product.cost_price)),
                discount_pct=item_data.get('discount_pct', 0),
                tax_rate=item_data.get('tax_rate', float(product.tax_rate)),
                sort_order=idx,
            )
            item.calculate()
            db.session.add(item)

        db.session.flush()
        po.recalculate()
        db.session.commit()
        return po

    @staticmethod
    def update_purchase_order(tenant_id, po_id, data):
        po = PurchaseOrder.query.filter_by(id=po_id, tenant_id=tenant_id).first()
        if not po:
            return None
        if po.status not in ('draft', 'sent'):
            raise ValueError('Can only edit draft or sent purchase orders')
        for f in ['supplier_id', 'warehouse_id', 'date', 'expected_date',
                   'notes', 'terms', 'currency', 'discount_amount', 'status']:
            if f in data:
                setattr(po, f, data[f])

        if 'items' in data:
            PurchaseOrderItem.query.filter_by(purchase_order_id=po.id).delete()
            db.session.flush()
            for idx, item_data in enumerate(data['items']):
                product = Product.query.filter_by(
                    id=item_data['product_id'], tenant_id=tenant_id
                ).first()
                if not product:
                    raise ValueError(f"Product not found: {item_data['product_id']}")
                item = PurchaseOrderItem(
                    purchase_order_id=po.id,
                    product_id=product.id,
                    description=item_data.get('description', product.name),
                    quantity=item_data.get('quantity', 1),
                    unit_price=item_data.get('unit_price', float(product.cost_price)),
                    discount_pct=item_data.get('discount_pct', 0),
                    tax_rate=item_data.get('tax_rate', float(product.tax_rate)),
                    sort_order=idx,
                )
                item.calculate()
                db.session.add(item)
            db.session.flush()
            po.recalculate()

        db.session.commit()
        return po

    @staticmethod
    def receive_goods(tenant_id, po_id, received_items, user_id=None):
        """Receive goods for a purchase order – adjusts inventory stock.

        received_items = [{'item_id': ..., 'quantity': ...}, ...]
        Each received quantity is added to the PO item's received_qty and
        stock is increased in the PO's warehouse.
        """
        po = PurchaseOrder.query.filter_by(id=po_id, tenant_id=tenant_id).first()
        if not po:
            raise ValueError('Purchase order not found')
        if po.status in ('cancelled', 'received'):
            raise ValueError(f'Cannot receive goods for {po.status} PO')

        for entry in received_items:
            item = PurchaseOrderItem.query.filter_by(
                id=entry['item_id'], purchase_order_id=po.id
            ).first()
            if not item:
                raise ValueError(f"PO item not found: {entry['item_id']}")
            qty = float(entry.get('quantity', 0))
            if qty <= 0:
                raise ValueError('Receive quantity must be positive')
            remaining = float(item.quantity) - float(item.received_qty)
            if qty > remaining:
                raise ValueError(
                    f"Cannot receive {qty} for item {item.id}; "
                    f"only {remaining} remaining"
                )
            item.received_qty = float(item.received_qty) + qty

            # Add to inventory
            if item.product and item.product.product_type == 'goods':
                InventoryService.adjust_stock(
                    tenant_id, item.product_id, po.warehouse_id,
                    int(qty),
                    movement_type='purchase',
                    reference_type='purchase_order', reference_id=po.id,
                    notes=f'Received from PO {po.number}',
                    user_id=user_id,
                )

        # Update PO status
        all_received = all(
            float(i.received_qty) >= float(i.quantity) for i in po.items
        )
        any_received = any(float(i.received_qty) > 0 for i in po.items)
        if all_received:
            po.status = 'received'
        elif any_received:
            po.status = 'partial'

        db.session.commit()
        return po

    @staticmethod
    def get_purchasing_stats(tenant_id):
        suppliers = Supplier.query.filter_by(tenant_id=tenant_id, is_active=True).count()
        orders = PurchaseOrder.query.filter_by(tenant_id=tenant_id).count()
        total_value = db.session.query(
            db.func.coalesce(db.func.sum(PurchaseOrder.total), 0)
        ).filter_by(tenant_id=tenant_id).scalar()
        pending = PurchaseOrder.query.filter(
            PurchaseOrder.tenant_id == tenant_id,
            PurchaseOrder.status.in_(['draft', 'sent', 'partial']),
        ).count()
        return {
            'total_suppliers': suppliers,
            'total_orders': orders,
            'total_value': float(total_value),
            'pending_orders': pending,
        }
