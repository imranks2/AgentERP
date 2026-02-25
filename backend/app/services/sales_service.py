"""Sales service – Customers, Quotations, Invoices, Payments.

Key integrated flows:
  - Quotation → Invoice conversion (copies items, links records)
  - Payment recording → auto-updates invoice status (partial/paid)
  - Invoice creation → stock deduction (when items are goods)
"""
from datetime import datetime, timezone
from app import db
from app.models.sales import (
    Customer, Quotation, QuotationItem, Invoice, InvoiceItem, Payment,
)
from app.models.inventory import Product
from app.services.inventory_service import InventoryService


class SalesService:

    # ── Customers ────────────────────────────────────────────

    @staticmethod
    def list_customers(tenant_id, search=None, page=1, per_page=50):
        q = Customer.query.filter_by(tenant_id=tenant_id, is_active=True)
        if search:
            like = f'%{search}%'
            q = q.filter(db.or_(
                Customer.name.ilike(like),
                Customer.email.ilike(like),
                Customer.company.ilike(like),
            ))
        total = q.count()
        customers = q.order_by(Customer.name)\
            .offset((page - 1) * per_page).limit(per_page).all()
        return customers, total

    @staticmethod
    def get_customer(tenant_id, customer_id):
        return Customer.query.filter_by(id=customer_id, tenant_id=tenant_id).first()

    @staticmethod
    def create_customer(tenant_id, data):
        name = data.get('name', '').strip()
        if not name:
            raise ValueError('Customer name is required')
        customer = Customer(
            tenant_id=tenant_id, name=name,
            email=data.get('email'), phone=data.get('phone'),
            company=data.get('company'), address=data.get('address'),
            tax_id=data.get('tax_id'), notes=data.get('notes'),
        )
        db.session.add(customer)
        db.session.commit()
        return customer

    @staticmethod
    def update_customer(tenant_id, customer_id, data):
        cust = Customer.query.filter_by(id=customer_id, tenant_id=tenant_id).first()
        if not cust:
            return None
        for f in ['name', 'email', 'phone', 'company', 'address', 'tax_id', 'notes', 'is_active']:
            if f in data:
                setattr(cust, f, data[f])
        db.session.commit()
        return cust

    # ── Sequence number generator ────────────────────────────

    @staticmethod
    def _next_number(tenant_id, prefix, model, field='number'):
        last = db.session.query(db.func.max(getattr(model, field)))\
            .filter_by(tenant_id=tenant_id).scalar()
        if last and last.startswith(prefix):
            try:
                num = int(last[len(prefix):]) + 1
            except ValueError:
                num = 1
        else:
            num = 1
        return f'{prefix}{num:05d}'

    # ── Quotations ───────────────────────────────────────────

    @staticmethod
    def list_quotations(tenant_id, status=None, customer_id=None, page=1, per_page=50):
        q = Quotation.query.filter_by(tenant_id=tenant_id)
        if status:
            q = q.filter_by(status=status)
        if customer_id:
            q = q.filter_by(customer_id=customer_id)
        total = q.count()
        quotations = q.order_by(Quotation.created_at.desc())\
            .offset((page - 1) * per_page).limit(per_page).all()
        return quotations, total

    @staticmethod
    def get_quotation(tenant_id, quote_id):
        return Quotation.query.filter_by(id=quote_id, tenant_id=tenant_id).first()

    @staticmethod
    def create_quotation(tenant_id, data, user_id=None):
        customer_id = data.get('customer_id')
        if not customer_id:
            raise ValueError('Customer is required')
        cust = Customer.query.filter_by(id=customer_id, tenant_id=tenant_id).first()
        if not cust:
            raise ValueError('Customer not found')

        number = SalesService._next_number(tenant_id, 'QT-', Quotation)
        quote = Quotation(
            tenant_id=tenant_id, customer_id=customer_id,
            number=number, created_by=user_id,
            date=data.get('date', datetime.now(timezone.utc).date()),
            valid_until=data.get('valid_until'),
            notes=data.get('notes'), terms=data.get('terms'),
            currency=data.get('currency', 'USD'),
            discount_amount=data.get('discount_amount', 0),
        )
        db.session.add(quote)
        db.session.flush()

        # Add line items
        for idx, item_data in enumerate(data.get('items', [])):
            product = Product.query.filter_by(
                id=item_data['product_id'], tenant_id=tenant_id
            ).first()
            if not product:
                raise ValueError(f"Product not found: {item_data['product_id']}")
            item = QuotationItem(
                quotation_id=quote.id,
                product_id=product.id,
                description=item_data.get('description', product.name),
                quantity=item_data.get('quantity', 1),
                unit_price=item_data.get('unit_price', float(product.sale_price)),
                discount_pct=item_data.get('discount_pct', 0),
                tax_rate=item_data.get('tax_rate', float(product.tax_rate)),
                sort_order=idx,
            )
            item.calculate()
            db.session.add(item)

        db.session.flush()
        quote.recalculate()
        db.session.commit()
        return quote

    @staticmethod
    def update_quotation(tenant_id, quote_id, data):
        quote = Quotation.query.filter_by(id=quote_id, tenant_id=tenant_id).first()
        if not quote:
            return None
        if quote.status not in ('draft', 'sent'):
            raise ValueError('Can only edit draft or sent quotations')
        for f in ['customer_id', 'date', 'valid_until', 'notes', 'terms',
                   'currency', 'discount_amount', 'status']:
            if f in data:
                if f == 'status' and data[f] not in Quotation.VALID_STATUSES:
                    raise ValueError(f"Invalid status: {data[f]}")
                setattr(quote, f, data[f])

        # Replace items if provided
        if 'items' in data:
            # Delete existing items
            QuotationItem.query.filter_by(quotation_id=quote.id).delete()
            db.session.flush()
            for idx, item_data in enumerate(data['items']):
                product = Product.query.filter_by(
                    id=item_data['product_id'], tenant_id=tenant_id
                ).first()
                if not product:
                    raise ValueError(f"Product not found: {item_data['product_id']}")
                item = QuotationItem(
                    quotation_id=quote.id,
                    product_id=product.id,
                    description=item_data.get('description', product.name),
                    quantity=item_data.get('quantity', 1),
                    unit_price=item_data.get('unit_price', float(product.sale_price)),
                    discount_pct=item_data.get('discount_pct', 0),
                    tax_rate=item_data.get('tax_rate', float(product.tax_rate)),
                    sort_order=idx,
                )
                item.calculate()
                db.session.add(item)
            db.session.flush()
            quote.recalculate()

        db.session.commit()
        return quote

    @staticmethod
    def convert_quotation_to_invoice(tenant_id, quote_id, user_id=None,
                                      warehouse_id=None):
        """Convert quotation to invoice – the core integration point.

        1. Creates invoice with same items
        2. Marks quotation as 'converted'
        3. Links the two records
        4. Optionally deducts stock for goods items
        """
        quote = Quotation.query.filter_by(id=quote_id, tenant_id=tenant_id).first()
        if not quote:
            raise ValueError('Quotation not found')
        if quote.status == 'converted':
            raise ValueError('Quotation already converted')
        if quote.status in ('rejected', 'expired'):
            raise ValueError(f'Cannot convert a {quote.status} quotation')

        inv_number = SalesService._next_number(tenant_id, 'INV-', Invoice)
        invoice = Invoice(
            tenant_id=tenant_id, customer_id=quote.customer_id,
            quotation_id=quote.id, number=inv_number,
            date=datetime.now(timezone.utc).date(),
            notes=quote.notes, terms=quote.terms,
            currency=quote.currency,
            discount_amount=quote.discount_amount,
            created_by=user_id,
        )
        db.session.add(invoice)
        db.session.flush()

        for q_item in quote.items:
            inv_item = InvoiceItem(
                invoice_id=invoice.id,
                product_id=q_item.product_id,
                description=q_item.description,
                quantity=q_item.quantity,
                unit_price=q_item.unit_price,
                discount_pct=q_item.discount_pct,
                tax_rate=q_item.tax_rate,
                sort_order=q_item.sort_order,
            )
            inv_item.calculate()
            db.session.add(inv_item)

            # Deduct stock for goods if warehouse provided
            if warehouse_id and q_item.product and q_item.product.product_type == 'goods':
                InventoryService.adjust_stock(
                    tenant_id, q_item.product_id, warehouse_id,
                    -int(float(q_item.quantity)),
                    movement_type='sale',
                    reference_type='invoice', reference_id=invoice.id,
                    notes=f'Sale from invoice {inv_number}',
                    user_id=user_id,
                )

        db.session.flush()
        invoice.recalculate()

        quote.status = 'converted'
        quote.invoice_id = invoice.id

        db.session.commit()
        return invoice

    # ── Invoices ─────────────────────────────────────────────

    @staticmethod
    def list_invoices(tenant_id, status=None, customer_id=None, page=1, per_page=50):
        q = Invoice.query.filter_by(tenant_id=tenant_id)
        if status:
            q = q.filter_by(status=status)
        if customer_id:
            q = q.filter_by(customer_id=customer_id)
        total = q.count()
        invoices = q.order_by(Invoice.created_at.desc())\
            .offset((page - 1) * per_page).limit(per_page).all()
        return invoices, total

    @staticmethod
    def get_invoice(tenant_id, invoice_id):
        return Invoice.query.filter_by(id=invoice_id, tenant_id=tenant_id).first()

    @staticmethod
    def create_invoice(tenant_id, data, user_id=None, warehouse_id=None):
        """Create invoice directly (not from quotation)."""
        customer_id = data.get('customer_id')
        if not customer_id:
            raise ValueError('Customer is required')

        number = SalesService._next_number(tenant_id, 'INV-', Invoice)
        invoice = Invoice(
            tenant_id=tenant_id, customer_id=customer_id,
            number=number, created_by=user_id,
            date=data.get('date', datetime.now(timezone.utc).date()),
            due_date=data.get('due_date'),
            notes=data.get('notes'), terms=data.get('terms'),
            currency=data.get('currency', 'USD'),
            discount_amount=data.get('discount_amount', 0),
        )
        db.session.add(invoice)
        db.session.flush()

        for idx, item_data in enumerate(data.get('items', [])):
            product = Product.query.filter_by(
                id=item_data['product_id'], tenant_id=tenant_id
            ).first()
            if not product:
                raise ValueError(f"Product not found: {item_data['product_id']}")
            item = InvoiceItem(
                invoice_id=invoice.id,
                product_id=product.id,
                description=item_data.get('description', product.name),
                quantity=item_data.get('quantity', 1),
                unit_price=item_data.get('unit_price', float(product.sale_price)),
                discount_pct=item_data.get('discount_pct', 0),
                tax_rate=item_data.get('tax_rate', float(product.tax_rate)),
                sort_order=idx,
            )
            item.calculate()
            db.session.add(item)

            # Deduct stock
            wh = warehouse_id or data.get('warehouse_id')
            if wh and product.product_type == 'goods':
                InventoryService.adjust_stock(
                    tenant_id, product.id, wh,
                    -int(float(item_data.get('quantity', 1))),
                    movement_type='sale',
                    reference_type='invoice', reference_id=invoice.id,
                    user_id=user_id,
                )

        db.session.flush()
        invoice.recalculate()
        db.session.commit()
        return invoice

    @staticmethod
    def update_invoice_status(tenant_id, invoice_id, status):
        invoice = Invoice.query.filter_by(id=invoice_id, tenant_id=tenant_id).first()
        if not invoice:
            raise ValueError('Invoice not found')
        if status not in Invoice.VALID_STATUSES:
            raise ValueError(f'Invalid status: {status}')
        invoice.status = status
        db.session.commit()
        return invoice

    # ── Payments ─────────────────────────────────────────────

    @staticmethod
    def record_payment(tenant_id, invoice_id, data, user_id=None):
        """Record a payment against an invoice — updates invoice status."""
        invoice = Invoice.query.filter_by(id=invoice_id, tenant_id=tenant_id).first()
        if not invoice:
            raise ValueError('Invoice not found')
        if invoice.status in ('cancelled', 'paid'):
            raise ValueError(f'Cannot add payment to {invoice.status} invoice')

        amount = float(data.get('amount', 0))
        if amount <= 0:
            raise ValueError('Payment amount must be positive')
        if amount > float(invoice.balance_due):
            raise ValueError(
                f'Payment amount ({amount}) exceeds balance due ({float(invoice.balance_due)})'
            )

        payment = Payment(
            tenant_id=tenant_id, invoice_id=invoice_id,
            amount=amount,
            payment_method=data.get('payment_method', 'bank_transfer'),
            reference=data.get('reference'),
            date=data.get('date', datetime.now(timezone.utc).date()),
            notes=data.get('notes'),
            created_by=user_id,
        )
        db.session.add(payment)
        db.session.flush()

        # Update invoice totals and status
        invoice.update_payment_status()
        db.session.commit()
        return payment, invoice

    @staticmethod
    def list_payments(tenant_id, invoice_id=None, page=1, per_page=50):
        q = Payment.query.filter_by(tenant_id=tenant_id)
        if invoice_id:
            q = q.filter_by(invoice_id=invoice_id)
        total = q.count()
        payments = q.order_by(Payment.created_at.desc())\
            .offset((page - 1) * per_page).limit(per_page).all()
        return payments, total

    @staticmethod
    def get_sales_stats(tenant_id):
        quotations = Quotation.query.filter_by(tenant_id=tenant_id).count()
        invoices = Invoice.query.filter_by(tenant_id=tenant_id).count()
        customers = Customer.query.filter_by(tenant_id=tenant_id, is_active=True).count()
        total_revenue = db.session.query(
            db.func.coalesce(db.func.sum(Invoice.total), 0)
        ).filter_by(tenant_id=tenant_id).scalar()
        total_paid = db.session.query(
            db.func.coalesce(db.func.sum(Invoice.amount_paid), 0)
        ).filter_by(tenant_id=tenant_id).scalar()
        outstanding = db.session.query(
            db.func.coalesce(db.func.sum(Invoice.balance_due), 0)
        ).filter(
            Invoice.tenant_id == tenant_id,
            Invoice.status.in_(['sent', 'partial', 'overdue']),
        ).scalar()
        return {
            'total_customers': customers,
            'total_quotations': quotations,
            'total_invoices': invoices,
            'total_revenue': float(total_revenue),
            'total_paid': float(total_paid),
            'total_outstanding': float(outstanding),
        }
