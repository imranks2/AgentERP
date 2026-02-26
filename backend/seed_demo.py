"""
Comprehensive demo data seeder for AgentERP.

Creates realistic demo data across ALL modules/tables:
- Platform admin + 2 demo tenants (Acme Corp, Globex Inc)
- Users for every role (owner, admin, manager, user, viewer)
- Subscription plans + feature gates
- Organisation hierarchy (enterprise → departments → teams)
- Module definitions + tenant installations
- Inventory (categories, products, warehouses, stock, movements)
- Sales (customers, quotations, invoices, payments)
- Purchasing (suppliers, purchase orders)
- Accounting (chart of accounts, fiscal year & periods, journal entries, tax rates, currencies)
- CRM (leads, opportunities, activities)
- HR (employees, leave types, leave requests, payroll runs, pay slips, attendance)
- Events & notifications
- Analytics events
- AI conversations, messages, interaction logs
- AI advanced: suggestions, agent actions, workflow patterns, automated workflows, training datasets, model versions

Usage:
    cd backend
    python seed_demo.py          # seed demo data
    python seed_demo.py --reset  # drop all tables and re-seed from scratch
"""
import sys
import uuid
import random
from datetime import datetime, timezone, timedelta, date

from app import create_app, db

# ── Models ───────────────────────────────────────────────
from app.models.tenant import Tenant
from app.models.user import User
from app.models.subscription import SubscriptionPlan, PlanFeature, Subscription
from app.models.role import Role, Permission, AuditLog
from app.models.analytics import AnalyticsEvent
from app.models.organisation import OrganisationUnit
from app.models.module import ModuleDefinition, TenantModule
from app.models.inventory import ProductCategory, Product, Warehouse, StockEntry, StockMovement
from app.models.sales import Customer, Quotation, QuotationItem, Invoice, InvoiceItem, Payment
from app.models.purchasing import Supplier, PurchaseOrder, PurchaseOrderItem
from app.models.event import EventLog, Notification
from app.models.accounting import Account, FiscalYear, FiscalPeriod, JournalEntry, JournalLine, TaxRate, CurrencyRate
from app.models.crm import Lead, Opportunity, CRMActivity
from app.models.hr import Employee, LeaveType, LeaveRequest, PayrollRun, PaySlip, Attendance
from app.models.ai import Conversation, Message, AIInteractionLog
from app.models.ai_advanced import (
    AISuggestion, AgentAction, WorkflowPattern, AutomatedWorkflow,
    TrainingDataset, ModelVersion,
)
from app.services.user_service import UserService
from app.services.module_service import ModuleService

# ── Helpers ──────────────────────────────────────────────
_uid = lambda: str(uuid.uuid4())
_now = lambda: datetime.now(timezone.utc)
_days_ago = lambda d: _now() - timedelta(days=d)
_date_days_ago = lambda d: (date.today() - timedelta(days=d))

# Fixed UUIDs for deterministic references
TENANT1_ID = '00000000-0000-0000-0000-000000000001'
TENANT2_ID = '00000000-0000-0000-0000-000000000002'

# ── 1. Subscription Plans ───────────────────────────────
def seed_plans():
    """Create Free / Standard / Premium subscription plans."""
    from seed import seed_plans as _sp
    _sp()
    print("  ✓ Subscription plans")


# ── 2. Platform Admin ───────────────────────────────────
def seed_platform_admin():
    """Create the super-admin (no tenant) user."""
    existing = User.query.filter_by(email='admin@agenterp.com', is_platform_admin=True).first()
    if existing:
        print("  ✓ Platform admin (exists)")
        return existing
    admin = User(
        id=_uid(),
        tenant_id=None,
        email='admin@agenterp.com',
        first_name='Platform',
        last_name='Admin',
        role='platform_admin',
        is_platform_admin=True,
    )
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    print("  ✓ Platform admin: admin@agenterp.com / admin123")
    return admin


# ── 3. Tenants ──────────────────────────────────────────
def seed_tenants():
    """Create two demo tenant organisations."""
    tenants_data = [
        {
            'id': TENANT1_ID, 'name': 'Acme Corporation', 'slug': 'acme-corporation',
            'email': 'info@acme.com', 'phone': '+1-555-0100', 'status': 'active',
            'address': '123 Innovation Drive, San Francisco, CA 94105, USA',
            'settings': {'timezone': 'America/Los_Angeles', 'language': 'en', 'currency': 'USD'},
        },
        {
            'id': TENANT2_ID, 'name': 'Globex Inc', 'slug': 'globex-inc',
            'email': 'info@globex.com', 'phone': '+44-20-7946-0958', 'status': 'trial',
            'address': '45 Fleet Street, London EC4A 2DY, UK',
            'settings': {'timezone': 'Europe/London', 'language': 'en', 'currency': 'GBP'},
            'trial_ends_at': _now() + timedelta(days=10),
        },
    ]
    created = []
    for td in tenants_data:
        if Tenant.query.filter_by(slug=td['slug']).first():
            created.append(Tenant.query.filter_by(slug=td['slug']).first())
            continue
        t = Tenant(**td)
        db.session.add(t)
        created.append(t)
    db.session.commit()
    print(f"  ✓ Tenants: {', '.join(t.name for t in created)}")
    return created


# ── 4. Subscriptions ────────────────────────────────────
def seed_subscriptions(tenants):
    """Assign plans – Acme=Premium, Globex=Standard."""
    plan_map = {p.slug: p for p in SubscriptionPlan.query.all()}
    assignments = [
        (tenants[0].id, 'premium', 'yearly'),
        (tenants[1].id, 'standard', 'monthly'),
    ]
    for tid, plan_slug, cycle in assignments:
        if Subscription.query.filter_by(tenant_id=tid).first():
            continue
        sub = Subscription(
            id=_uid(), tenant_id=tid, plan_id=plan_map[plan_slug].id,
            billing_cycle=cycle, status='active',
            starts_at=_days_ago(90),
        )
        db.session.add(sub)
    db.session.commit()
    print("  ✓ Subscriptions assigned")


# ── 5. RBAC: Permissions & Roles ────────────────────────
def seed_rbac(tenants):
    """Seed system permissions and roles for each tenant."""
    for t in tenants:
        UserService.seed_roles(tenant_id=t.id)
    print("  ✓ Permissions & roles seeded")


# ── 6. Users (all roles) ────────────────────────────────
def seed_users(tenants):
    """Create demo users for every role in both tenants."""
    # Password for ALL demo users
    PASSWORD = 'demo1234'

    role_users = {
        # role_slug: [(first, last, email_prefix)]
        'owner':   [('Alice', 'Owner', 'alice.owner')],
        'admin':   [('Bob', 'Admin', 'bob.admin')],
        'manager': [('Charlie', 'Manager', 'charlie.manager'), ('Diana', 'Manager', 'diana.manager')],
        'user':    [('Eve', 'User', 'eve.user'), ('Frank', 'User', 'frank.user'), ('Grace', 'User', 'grace.user')],
        'viewer':  [('Hank', 'Viewer', 'hank.viewer')],
    }

    users_by_tenant = {}
    for t in tenants:
        domain = t.slug.replace('-', '') + '.com'
        tenant_users = []

        # Resolve role objects for this tenant
        roles = {r.slug: r for r in Role.query.filter(
            db.or_(Role.tenant_id == t.id, Role.tenant_id.is_(None))
        ).all()}

        for role_slug, people in role_users.items():
            for first, last, prefix in people:
                email = f'{prefix}@{domain}'
                existing = User.query.filter_by(tenant_id=t.id, email=email).first()
                if existing:
                    tenant_users.append(existing)
                    continue
                role_obj = roles.get(role_slug)
                u = User(
                    id=_uid(), tenant_id=t.id, email=email,
                    first_name=first, last_name=last,
                    role=role_slug,
                    role_id=role_obj.id if role_obj else None,
                    is_active=True,
                )
                u.set_password(PASSWORD)
                db.session.add(u)
                tenant_users.append(u)
        db.session.commit()
        users_by_tenant[t.id] = tenant_users

    print("  ✓ Users created (password for all demo users: demo1234)")
    print("    Roles: owner, admin, manager (×2), user (×3), viewer — per tenant")
    return users_by_tenant


# ── 7. Organisation Hierarchy ───────────────────────────
def seed_org(tenants):
    """Build a realistic org tree for each tenant."""
    org_map = {}
    for t in tenants:
        if OrganisationUnit.query.filter_by(tenant_id=t.id).first():
            org_map[t.id] = OrganisationUnit.query.filter_by(tenant_id=t.id).all()
            continue

        root = OrganisationUnit(
            id=_uid(), tenant_id=t.id, name=t.name, code='ROOT',
            unit_type='enterprise', depth=0, path='/', sort_order=0,
            manager_name='Alice Owner', email=t.email,
        )
        db.session.add(root)
        db.session.flush()

        children_defs = [
            ('HQ', 'legal_entity', 'HQ', [
                ('Engineering', 'department', 'ENG', [
                    ('Backend Team', 'team', 'ENG-BE', []),
                    ('Frontend Team', 'team', 'ENG-FE', []),
                ]),
                ('Sales', 'department', 'SALES', [
                    ('Enterprise Sales', 'team', 'SALES-ENT', []),
                    ('SMB Sales', 'team', 'SALES-SMB', []),
                ]),
                ('Finance', 'department', 'FIN', []),
                ('Human Resources', 'department', 'HR', []),
            ]),
            ('West Coast Branch', 'branch', 'WEST', [
                ('Operations', 'department', 'WEST-OPS', []),
                ('Warehouse', 'department', 'WEST-WH', []),
            ]),
            ('Research Lab', 'project', 'R&D', []),
        ]

        def _create_units(parent, defs, depth):
            units = [parent]
            for name, utype, code, sub in defs:
                u = OrganisationUnit(
                    id=_uid(), tenant_id=t.id, parent_id=parent.id,
                    name=name, code=code, unit_type=utype,
                    depth=depth, path=f'{parent.path}{parent.code}/',
                    sort_order=len(units),
                )
                db.session.add(u)
                db.session.flush()
                units.append(u)
                if sub:
                    units.extend(_create_units(u, sub, depth + 1))
            return units

        all_units = _create_units(root, children_defs, 1)
        db.session.commit()
        org_map[t.id] = all_units

    print("  ✓ Organisation hierarchy")
    return org_map


# ── 8. Module Definitions & Installations ───────────────
def seed_modules(tenants):
    """Seed module definitions + install all for Acme, basic for Globex."""
    ModuleService.seed_modules()
    mods = {m.slug: m for m in ModuleDefinition.query.all()}

    # Also add accounting/hr/crm module definitions if missing
    extra_mods = [
        {'name': 'Accounting', 'slug': 'accounting', 'description': 'Double-entry accounting, chart of accounts, journal entries, tax management.',
         'icon': 'BookOpen', 'color': '#8b5cf6', 'category': 'finance', 'is_core': True, 'sort_order': 4, 'dependencies': []},
        {'name': 'Human Resources', 'slug': 'hr', 'description': 'Employee records, leave management, payroll processing, attendance tracking.',
         'icon': 'UserCheck', 'color': '#ec4899', 'category': 'hr', 'is_core': True, 'sort_order': 5, 'dependencies': []},
        {'name': 'CRM', 'slug': 'crm', 'description': 'Leads, opportunities, pipeline management, customer relationship tracking.',
         'icon': 'Target', 'color': '#f97316', 'category': 'sales', 'is_core': True, 'sort_order': 6, 'dependencies': []},
    ]
    for em in extra_mods:
        if em['slug'] not in mods:
            m = ModuleDefinition(**em)
            db.session.add(m)
            db.session.flush()
            mods[em['slug']] = m
    db.session.commit()

    # Install modules for tenants
    all_slugs = ['inventory', 'sales', 'purchasing', 'accounting', 'hr', 'crm']
    globex_slugs = ['inventory', 'sales', 'purchasing']

    for t_idx, t in enumerate(tenants):
        slugs = all_slugs if t_idx == 0 else globex_slugs
        for slug in slugs:
            mod = mods.get(slug)
            if not mod:
                continue
            existing = TenantModule.query.filter_by(tenant_id=t.id, module_id=mod.id).first()
            if not existing:
                db.session.add(TenantModule(
                    id=_uid(), tenant_id=t.id, module_id=mod.id,
                    is_enabled=True, installed_at=_days_ago(60),
                ))
    db.session.commit()
    print("  ✓ Module definitions & installations")
    return mods


# ── 9. Inventory ────────────────────────────────────────
def seed_inventory(tenant_id, users):
    """Create categories, products, warehouses, stock entries, movements."""
    if Product.query.filter_by(tenant_id=tenant_id).first():
        print("  ✓ Inventory (exists)")
        return

    user_id = users[0].id if users else None

    # Categories
    cats = {}
    for name, slug, desc in [
        ('Electronics', 'electronics', 'Consumer and commercial electronics'),
        ('Office Supplies', 'office-supplies', 'Stationery, paper, and office essentials'),
        ('Furniture', 'furniture', 'Desks, chairs, and office furniture'),
        ('Software', 'software', 'Software licenses and subscriptions'),
        ('Raw Materials', 'raw-materials', 'Manufacturing inputs'),
    ]:
        c = ProductCategory(id=_uid(), tenant_id=tenant_id, name=name, slug=slug, description=desc)
        db.session.add(c)
        cats[slug] = c
    db.session.flush()

    # Sub-categories for electronics
    for name, slug in [('Laptops', 'laptops'), ('Monitors', 'monitors'), ('Accessories', 'accessories')]:
        sc = ProductCategory(id=_uid(), tenant_id=tenant_id, parent_id=cats['electronics'].id, name=name, slug=slug)
        db.session.add(sc)
        cats[slug] = sc
    db.session.flush()

    # Products
    products_data = [
        ('MacBook Pro 16"', 'MBP-16', 'laptops', 'goods', 2499.99, 1800.00, 10, 5, 'unit'),
        ('Dell XPS 15', 'DELL-XPS15', 'laptops', 'goods', 1799.99, 1200.00, 15, 10, 'unit'),
        ('ThinkPad X1 Carbon', 'TP-X1C', 'laptops', 'goods', 1649.99, 1100.00, 12, 8, 'unit'),
        ('LG UltraWide 34"', 'LG-UW34', 'monitors', 'goods', 699.99, 450.00, 20, 10, 'unit'),
        ('Samsung 27" 4K', 'SAM-27-4K', 'monitors', 'goods', 449.99, 280.00, 25, 15, 'unit'),
        ('Logitech MX Master 3S', 'LOG-MXM3S', 'accessories', 'goods', 99.99, 55.00, 50, 25, 'unit'),
        ('Keychron K3 Keyboard', 'KEY-K3', 'accessories', 'goods', 84.99, 40.00, 40, 20, 'unit'),
        ('USB-C Hub 10-in-1', 'USBC-HUB10', 'accessories', 'goods', 59.99, 22.00, 100, 50, 'unit'),
        ('A4 Copy Paper (Box)', 'PAPER-A4', 'office-supplies', 'consumable', 29.99, 15.00, 200, 100, 'box'),
        ('Whiteboard Markers (Set)', 'WB-MARKERS', 'office-supplies', 'consumable', 12.99, 5.00, 150, 75, 'set'),
        ('Standing Desk Pro', 'DESK-STD', 'furniture', 'goods', 899.99, 500.00, 8, 3, 'unit'),
        ('Ergonomic Chair Elite', 'CHAIR-ERGO', 'furniture', 'goods', 649.99, 350.00, 10, 5, 'unit'),
        ('Office 365 License', 'O365-LIC', 'software', 'service', 12.99, 10.00, 0, 0, 'unit'),
        ('Adobe CC License', 'ADOBE-CC', 'software', 'service', 54.99, 40.00, 0, 0, 'unit'),
        ('Steel Sheets (kg)', 'STEEL-SH', 'raw-materials', 'goods', 3.50, 2.00, 500, 200, 'kg'),
        ('Copper Wire (meter)', 'COPPER-W', 'raw-materials', 'goods', 1.25, 0.70, 1000, 500, 'meter'),
    ]
    products = []
    for name, sku, cat_slug, ptype, sale, cost, reorder, rqty, uom in products_data:
        p = Product(
            id=_uid(), tenant_id=tenant_id, category_id=cats[cat_slug].id,
            name=name, sku=sku, product_type=ptype,
            sale_price=sale, cost_price=cost, currency='USD',
            tax_rate=10.0, track_inventory=(ptype == 'goods' or ptype == 'consumable'),
            reorder_point=reorder, reorder_qty=rqty, uom=uom,
        )
        db.session.add(p)
        products.append(p)
    db.session.flush()

    # Warehouses
    wh_data = [
        ('Main Warehouse', 'WH-MAIN', '100 Warehouse Blvd, San Jose, CA'),
        ('East Coast DC', 'WH-EAST', '200 Distribution Way, Newark, NJ'),
        ('Returns Center', 'WH-RET', '50 Return Lane, Dallas, TX'),
    ]
    warehouses = []
    for name, code, addr in wh_data:
        w = Warehouse(id=_uid(), tenant_id=tenant_id, name=name, code=code, address=addr)
        db.session.add(w)
        warehouses.append(w)
    db.session.flush()

    # Stock entries (random stock levels in main warehouse)
    for p in products:
        if not p.track_inventory:
            continue
        qty = random.randint(p.reorder_point, p.reorder_point * 5)
        se = StockEntry(
            id=_uid(), tenant_id=tenant_id, product_id=p.id,
            warehouse_id=warehouses[0].id, quantity=qty, reserved_qty=0,
        )
        db.session.add(se)
        # Also some stock in east coast warehouse
        se2 = StockEntry(
            id=_uid(), tenant_id=tenant_id, product_id=p.id,
            warehouse_id=warehouses[1].id, quantity=random.randint(0, qty // 2),
        )
        db.session.add(se2)
    db.session.flush()

    # Stock movements (recent history)
    move_types = ['in', 'out', 'adjustment']
    for i in range(30):
        p = random.choice([pr for pr in products if pr.track_inventory])
        sm = StockMovement(
            id=_uid(), tenant_id=tenant_id, product_id=p.id,
            warehouse_id=warehouses[0].id,
            movement_type=random.choice(move_types),
            quantity=random.randint(1, 50),
            reference_type='manual', notes=f'Demo movement #{i+1}',
            created_by=user_id, created_at=_days_ago(random.randint(0, 60)),
        )
        db.session.add(sm)
    db.session.commit()
    print("  ✓ Inventory (categories, products, warehouses, stock, movements)")
    return products, warehouses


# ── 10. Sales ───────────────────────────────────────────
def seed_sales(tenant_id, users, products):
    """Create customers, quotations, invoices, payments."""
    if Customer.query.filter_by(tenant_id=tenant_id).first():
        print("  ✓ Sales (exists)")
        return

    user_id = users[0].id if users else None

    # Customers
    customers_data = [
        ('TechStart Solutions', 'contact@techstart.io', '+1-555-0201', 'TechStart Inc.', '500 Startup Ave, Palo Alto, CA'),
        ('Global Enterprises', 'procurement@globalent.com', '+1-555-0202', 'Global Enterprises Ltd', '1 Commerce Plaza, New York, NY'),
        ('Green Valley School', 'admin@greenvalley.edu', '+1-555-0203', 'Green Valley ISD', '300 School Rd, Austin, TX'),
        ('CloudNine Media', 'orders@cloudnine.media', '+1-555-0204', 'CloudNine Media LLC', '88 Media Circle, Los Angeles, CA'),
        ('Summit Healthcare', 'supply@summithealth.org', '+1-555-0205', 'Summit Health Systems', '700 Medical Dr, Chicago, IL'),
        ('Riverside Manufacturing', 'purchasing@riverside-mfg.com', '+1-555-0206', 'Riverside Mfg Co', '45 Industrial Park, Detroit, MI'),
        ('Blue Ocean Consulting', 'office@blueocean.consulting', '+1-555-0207', 'Blue Ocean Group', '12 Harbor View, Miami, FL'),
        ('Nordic Design Studio', 'studio@nordicdesign.co', '+46-8-1234567', 'Nordic Design AB', 'Storgatan 10, Stockholm, Sweden'),
    ]
    customers = []
    for name, email, phone, company, address in customers_data:
        c = Customer(
            id=_uid(), tenant_id=tenant_id, name=name, email=email,
            phone=phone, company=company, address=address,
        )
        db.session.add(c)
        customers.append(c)
    db.session.flush()

    # Quotations (some draft, some sent, some accepted/converted)
    quotations = []
    statuses = ['draft', 'sent', 'accepted', 'rejected', 'converted']
    for i in range(8):
        cust = customers[i % len(customers)]
        status = statuses[i % len(statuses)]
        q = Quotation(
            id=_uid(), tenant_id=tenant_id, customer_id=cust.id,
            number=f'QT-2026-{i+1:04d}', status=status,
            date=_date_days_ago(30 - i * 3),
            valid_until=_date_days_ago(30 - i * 3 - 30),
            notes=f'Demo quotation for {cust.name}', currency='USD',
            created_by=user_id,
        )
        # Add 2-4 line items
        subtotal = 0
        items = []
        for j in range(random.randint(2, 4)):
            p = products[j % len(products)] if products else None
            if not p:
                continue
            qty = random.randint(1, 10)
            unit_price = float(p.sale_price)
            tax_rate = 10.0
            line_total = qty * unit_price
            tax_amt = line_total * tax_rate / 100
            items.append(QuotationItem(
                id=_uid(), product_id=p.id, description=p.name,
                quantity=qty, unit_price=unit_price, tax_rate=tax_rate,
                tax_amount=round(tax_amt, 2), total=round(line_total + tax_amt, 2),
                sort_order=j,
            ))
            subtotal += line_total
        tax_total = round(subtotal * 0.10, 2)
        q.subtotal = round(subtotal, 2)
        q.tax_amount = tax_total
        q.total = round(subtotal + tax_total, 2)
        db.session.add(q)
        db.session.flush()
        for item in items:
            item.quotation_id = q.id
            db.session.add(item)
        quotations.append(q)
    db.session.flush()

    # Invoices (various statuses)
    inv_statuses = ['draft', 'sent', 'partial', 'paid', 'overdue', 'paid', 'sent', 'paid']
    invoices = []
    for i in range(8):
        cust = customers[i % len(customers)]
        status = inv_statuses[i]
        inv = Invoice(
            id=_uid(), tenant_id=tenant_id, customer_id=cust.id,
            number=f'INV-2026-{i+1:04d}', status=status,
            date=_date_days_ago(45 - i * 5),
            due_date=_date_days_ago(45 - i * 5 - 30),
            notes=f'Invoice for {cust.name}', currency='USD',
            created_by=user_id,
        )
        subtotal = 0
        inv_items = []
        for j in range(random.randint(1, 5)):
            p = products[(i + j) % len(products)] if products else None
            if not p:
                continue
            qty = random.randint(1, 8)
            unit_price = float(p.sale_price)
            tax_rate = 10.0
            line_total = qty * unit_price
            tax_amt = line_total * tax_rate / 100
            inv_items.append(InvoiceItem(
                id=_uid(), product_id=p.id, description=p.name,
                quantity=qty, unit_price=unit_price, tax_rate=tax_rate,
                tax_amount=round(tax_amt, 2), total=round(line_total + tax_amt, 2),
                sort_order=j,
            ))
            subtotal += line_total
        tax_total = round(subtotal * 0.10, 2)
        total = round(subtotal + tax_total, 2)
        inv.subtotal = round(subtotal, 2)
        inv.tax_amount = tax_total
        inv.total = total

        # Set payment amounts based on status
        if status == 'paid':
            inv.amount_paid = total
            inv.balance_due = 0
        elif status == 'partial':
            inv.amount_paid = round(total * 0.5, 2)
            inv.balance_due = round(total - inv.amount_paid, 2)
        else:
            inv.amount_paid = 0
            inv.balance_due = total

        db.session.add(inv)
        db.session.flush()
        for item in inv_items:
            item.invoice_id = inv.id
            db.session.add(item)
        invoices.append(inv)
    db.session.flush()

    # Payments for paid/partial invoices
    for inv in invoices:
        if inv.status in ('paid', 'partial'):
            pmt = Payment(
                id=_uid(), tenant_id=tenant_id, invoice_id=inv.id,
                amount=float(inv.amount_paid),
                payment_method=random.choice(['bank_transfer', 'credit_card', 'cash']),
                reference=f'PMT-{random.randint(10000, 99999)}',
                status='completed',
                date=_date_days_ago(random.randint(1, 20)),
                notes='Demo payment', created_by=user_id,
            )
            db.session.add(pmt)
    db.session.commit()
    print("  ✓ Sales (customers, quotations, invoices, payments)")
    return customers, invoices


# ── 11. Purchasing ──────────────────────────────────────
def seed_purchasing(tenant_id, users, products, warehouses):
    """Create suppliers and purchase orders."""
    if Supplier.query.filter_by(tenant_id=tenant_id).first():
        print("  ✓ Purchasing (exists)")
        return

    user_id = users[0].id if users else None
    wh_id = warehouses[0].id if warehouses else None

    suppliers_data = [
        ('Taiwan Semiconductor Supply', 'orders@tss-supply.tw', '+886-2-1234-5678', 'TSS Ltd', 'Hsinchu Science Park, Taiwan', 'Net 30'),
        ('German Industrial Parts', 'verkauf@gip.de', '+49-89-123456', 'GIP GmbH', 'Industriestraße 12, Munich, Germany', 'Net 45'),
        ('Pacific Logistics Corp', 'procurement@paclog.com', '+1-555-0310', 'PacLog Corp', '900 Port Way, Long Beach, CA', 'Net 15'),
        ('QuickShip Paper Co', 'sales@quickshippaper.com', '+1-555-0311', 'QuickShip Inc', '200 Paper Mill Rd, Portland, OR', 'Net 30'),
        ('Nordic Furniture Supply', 'order@nordicfurniture.se', '+46-8-9876543', 'Nordic FS AB', 'Möbelvägen 5, Malmö, Sweden', 'Net 60'),
    ]
    suppliers = []
    for name, email, phone, company, address, terms in suppliers_data:
        s = Supplier(
            id=_uid(), tenant_id=tenant_id, name=name, email=email,
            phone=phone, company=company, address=address, payment_terms=terms,
        )
        db.session.add(s)
        suppliers.append(s)
    db.session.flush()

    # Purchase orders
    po_statuses = ['draft', 'sent', 'partial', 'received', 'sent']
    for i in range(5):
        supplier = suppliers[i % len(suppliers)]
        status = po_statuses[i]
        po = PurchaseOrder(
            id=_uid(), tenant_id=tenant_id, supplier_id=supplier.id,
            number=f'PO-2026-{i+1:04d}', status=status,
            date=_date_days_ago(40 - i * 7),
            expected_date=_date_days_ago(40 - i * 7 - 14),
            warehouse_id=wh_id, notes=f'Purchase order from {supplier.name}',
            currency='USD', created_by=user_id,
        )
        subtotal = 0
        po_items = []
        for j in range(random.randint(2, 5)):
            p = products[(i + j + 5) % len(products)] if products else None
            if not p:
                continue
            qty = random.randint(10, 100)
            unit_price = float(p.cost_price)
            tax_rate = 10.0
            line_total = qty * unit_price
            tax_amt = line_total * tax_rate / 100
            received = qty if status == 'received' else (qty // 2 if status == 'partial' else 0)
            po_items.append(PurchaseOrderItem(
                id=_uid(), product_id=p.id, description=p.name,
                quantity=qty, received_qty=received, unit_price=unit_price,
                tax_rate=tax_rate, tax_amount=round(tax_amt, 2),
                total=round(line_total + tax_amt, 2), sort_order=j,
            ))
            subtotal += line_total
        tax_total = round(subtotal * 0.10, 2)
        po.subtotal = round(subtotal, 2)
        po.tax_amount = tax_total
        po.total = round(subtotal + tax_total, 2)
        db.session.add(po)
        db.session.flush()
        for item in po_items:
            item.purchase_order_id = po.id
            db.session.add(item)
    db.session.commit()
    print("  ✓ Purchasing (suppliers, purchase orders)")


# ── 12. Accounting ──────────────────────────────────────
def seed_accounting(tenant_id, users):
    """Chart of accounts, fiscal year, journal entries, tax rates, currencies."""
    if Account.query.filter_by(tenant_id=tenant_id).first():
        print("  ✓ Accounting (exists)")
        return

    user_id = users[0].id if users else None

    # Chart of Accounts
    accounts_data = [
        # (code, name, type, parent_code)
        ('1000', 'Assets', 'asset', None),
        ('1100', 'Cash & Bank', 'asset', '1000'),
        ('1110', 'Petty Cash', 'asset', '1100'),
        ('1120', 'Business Checking', 'asset', '1100'),
        ('1130', 'Savings Account', 'asset', '1100'),
        ('1200', 'Accounts Receivable', 'asset', '1000'),
        ('1300', 'Inventory Asset', 'asset', '1000'),
        ('1400', 'Prepaid Expenses', 'asset', '1000'),
        ('1500', 'Fixed Assets', 'asset', '1000'),
        ('1510', 'Equipment', 'asset', '1500'),
        ('1520', 'Vehicles', 'asset', '1500'),
        ('1530', 'Accumulated Depreciation', 'asset', '1500'),
        ('2000', 'Liabilities', 'liability', None),
        ('2100', 'Accounts Payable', 'liability', '2000'),
        ('2200', 'Accrued Expenses', 'liability', '2000'),
        ('2300', 'Sales Tax Payable', 'liability', '2000'),
        ('2400', 'Short-term Loans', 'liability', '2000'),
        ('2500', 'Long-term Debt', 'liability', '2000'),
        ('3000', 'Equity', 'equity', None),
        ('3100', 'Owner\'s Capital', 'equity', '3000'),
        ('3200', 'Retained Earnings', 'equity', '3000'),
        ('3300', 'Drawings', 'equity', '3000'),
        ('4000', 'Revenue', 'revenue', None),
        ('4100', 'Product Sales', 'revenue', '4000'),
        ('4200', 'Service Revenue', 'revenue', '4000'),
        ('4300', 'Interest Income', 'revenue', '4000'),
        ('4400', 'Other Income', 'revenue', '4000'),
        ('5000', 'Cost of Goods Sold', 'expense', None),
        ('5100', 'Material Costs', 'expense', '5000'),
        ('5200', 'Direct Labour', 'expense', '5000'),
        ('6000', 'Operating Expenses', 'expense', None),
        ('6100', 'Salaries & Wages', 'expense', '6000'),
        ('6200', 'Rent', 'expense', '6000'),
        ('6300', 'Utilities', 'expense', '6000'),
        ('6400', 'Office Supplies', 'expense', '6000'),
        ('6500', 'Depreciation', 'expense', '6000'),
        ('6600', 'Insurance', 'expense', '6000'),
        ('6700', 'Marketing & Advertising', 'expense', '6000'),
        ('6800', 'Travel & Entertainment', 'expense', '6000'),
        ('6900', 'Professional Fees', 'expense', '6000'),
    ]
    accts = {}
    for code, name, atype, parent_code in accounts_data:
        a = Account(
            id=_uid(), tenant_id=tenant_id, code=code, name=name,
            account_type=atype, parent_id=accts[parent_code].id if parent_code else None,
        )
        db.session.add(a)
        db.session.flush()
        accts[code] = a

    # Fiscal Year & Periods
    fy = FiscalYear(
        id=_uid(), tenant_id=tenant_id, name='FY 2026',
        start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
    )
    db.session.add(fy)
    db.session.flush()

    for m in range(1, 13):
        import calendar
        last_day = calendar.monthrange(2026, m)[1]
        fp = FiscalPeriod(
            id=_uid(), tenant_id=tenant_id, fiscal_year_id=fy.id,
            period_number=m, name=f'{date(2026, m, 1):%B %Y}',
            start_date=date(2026, m, 1), end_date=date(2026, m, last_day),
            is_closed=(m < _now().month) if _now().year == 2026 else False,
        )
        db.session.add(fp)

    # Journal Entries (sample posted entries)
    je_data = [
        ('JE-2026-0001', 'Initial capital investment', 'manual',
         [('1120', 100000, 0), ('3100', 0, 100000)]),
        ('JE-2026-0002', 'Office rent payment', 'manual',
         [('6200', 5000, 0), ('1120', 0, 5000)]),
        ('JE-2026-0003', 'Inventory purchase', 'purchase',
         [('1300', 25000, 0), ('2100', 0, 25000)]),
        ('JE-2026-0004', 'Sales revenue recognised', 'invoice',
         [('1200', 15000, 0), ('4100', 0, 13636.36), ('2300', 0, 1363.64)]),
        ('JE-2026-0005', 'Customer payment received', 'payment',
         [('1120', 15000, 0), ('1200', 0, 15000)]),
        ('JE-2026-0006', 'Salary expense', 'manual',
         [('6100', 45000, 0), ('1120', 0, 45000)]),
        ('JE-2026-0007', 'Utility bill', 'manual',
         [('6300', 1200, 0), ('1120', 0, 1200)]),
        ('JE-2026-0008', 'Equipment purchase', 'manual',
         [('1510', 8500, 0), ('1120', 0, 8500)]),
    ]
    for i, (number, desc, ref_type, lines) in enumerate(je_data):
        total_debit = sum(d for _, d, _ in lines)
        total_credit = sum(c for _, _, c in lines)
        je = JournalEntry(
            id=_uid(), tenant_id=tenant_id, number=number, description=desc,
            date=_date_days_ago(60 - i * 7), reference_type=ref_type,
            status='posted', total_debit=total_debit, total_credit=total_credit,
            created_by=user_id, posted_at=_days_ago(60 - i * 7),
        )
        db.session.add(je)
        db.session.flush()
        for acct_code, debit, credit in lines:
            jl = JournalLine(
                id=_uid(), journal_entry_id=je.id, account_id=accts[acct_code].id,
                debit=debit, credit=credit, description=desc,
            )
            db.session.add(jl)

    # Tax Rates
    tax_rates_data = [
        ('Standard VAT', 'VAT-STD', 0.20, 'both', 'United States'),
        ('Reduced VAT', 'VAT-RED', 0.10, 'both', 'United States'),
        ('Zero Rate', 'VAT-ZERO', 0.0, 'both', 'United States'),
        ('Sales Tax CA', 'ST-CA', 0.0725, 'sales', 'California, US'),
        ('Import Duty', 'IMP-DUTY', 0.05, 'purchase', 'Federal'),
    ]
    for name, code, rate, ttype, juris in tax_rates_data:
        tr = TaxRate(
            id=_uid(), tenant_id=tenant_id, name=name, code=code,
            rate=rate, tax_type=ttype, jurisdiction=juris,
        )
        db.session.add(tr)

    # Currency Rates
    currency_data = [
        ('USD', 'US Dollar', '$', 1.0, True),
        ('EUR', 'Euro', '€', 0.92, False),
        ('GBP', 'British Pound', '£', 0.79, False),
        ('JPY', 'Japanese Yen', '¥', 149.50, False),
        ('CAD', 'Canadian Dollar', 'C$', 1.36, False),
        ('AUD', 'Australian Dollar', 'A$', 1.53, False),
        ('CHF', 'Swiss Franc', 'CHF', 0.88, False),
    ]
    for code, name, symbol, rate, is_base in currency_data:
        cr = CurrencyRate(
            id=_uid(), tenant_id=tenant_id, code=code, name=name,
            symbol=symbol, exchange_rate=rate, is_base=is_base,
        )
        db.session.add(cr)

    db.session.commit()
    print("  ✓ Accounting (chart of accounts, fiscal year, journal entries, tax rates, currencies)")


# ── 13. CRM ─────────────────────────────────────────────
def seed_crm(tenant_id, users, customers):
    """Create leads, opportunities, and activities."""
    if Lead.query.filter_by(tenant_id=tenant_id).first():
        print("  ✓ CRM (exists)")
        return

    user_ids = [u.id for u in users] if users else [None]

    leads_data = [
        ('James Wilson', 'james@wilsontech.com', '+1-555-0401', 'Wilson Technologies', 'web', 'new', 85),
        ('Sarah Chen', 'sarah.chen@innovate.co', '+1-555-0402', 'Innovate Corp', 'referral', 'contacted', 72),
        ('Michael Brown', 'mbrown@enterprise.biz', '+1-555-0403', 'Brown Enterprise', 'campaign', 'qualified', 90),
        ('Emily Davis', 'emily@davisgroup.com', '+1-555-0404', 'Davis Group', 'web', 'contacted', 65),
        ('Robert Taylor', 'rtaylor@taylorind.com', '+1-555-0405', 'Taylor Industries', 'other', 'new', 40),
        ('Lisa Anderson', 'lisa@andersonlaw.com', '+1-555-0406', 'Anderson & Associates', 'referral', 'qualified', 88),
        ('David Martinez', 'david@martinez.io', '+1-555-0407', 'Martinez Consulting', 'campaign', 'converted', 95),
        ('Jennifer Lee', 'jlee@leedesigns.com', '+1-555-0408', 'Lee Design Studio', 'web', 'lost', 30),
        ('Christopher Wright', 'chris@wrighteng.com', '+1-555-0409', 'Wright Engineering', 'referral', 'new', 55),
        ('Amanda Phillips', 'amanda@phillips.co', '+1-555-0410', 'Phillips & Co', 'campaign', 'contacted', 70),
    ]
    leads = []
    for name, email, phone, company, source, status, score in leads_data:
        l = Lead(
            id=_uid(), tenant_id=tenant_id, name=name, email=email,
            phone=phone, company=company, source=source, status=status,
            assigned_to=random.choice(user_ids), score=score,
            notes=f'Demo lead - {company}',
            created_at=_days_ago(random.randint(5, 60)),
        )
        db.session.add(l)
        leads.append(l)
    db.session.flush()

    # Opportunities
    stages = ['prospecting', 'proposal', 'negotiation', 'won', 'lost']
    customer_ids = [c.id for c in customers] if customers else [None]
    opps = []
    for i in range(8):
        lead = leads[i % len(leads)]
        stage = stages[i % len(stages)]
        prob_map = {'prospecting': 20, 'proposal': 50, 'negotiation': 75, 'won': 100, 'lost': 0}
        opp = Opportunity(
            id=_uid(), tenant_id=tenant_id, lead_id=lead.id,
            customer_id=customer_ids[i % len(customer_ids)] if customers else None,
            title=f'{lead.company} - Deal #{i+1}',
            value=random.randint(5000, 150000), currency='USD',
            stage=stage, probability=prob_map.get(stage, 50),
            expected_close_date=_date_days_ago(-random.randint(10, 90)),
            assigned_to=random.choice(user_ids),
            notes=f'Opportunity from {lead.name}',
        )
        db.session.add(opp)
        opps.append(opp)
    db.session.flush()

    # CRM Activities
    activity_types = ['call', 'email', 'meeting', 'note']
    subjects = [
        'Initial discovery call', 'Follow-up email sent', 'Product demo meeting',
        'Price negotiation', 'Contract review', 'Quarterly check-in',
        'Technical requirements discussion', 'Proposal sent', 'Onboarding kickoff',
        'Feedback collection', 'Renewal discussion', 'Upsell opportunity assessment',
    ]
    for i in range(20):
        act = CRMActivity(
            id=_uid(), tenant_id=tenant_id,
            activity_type=random.choice(activity_types),
            subject=subjects[i % len(subjects)],
            description=f'Demo activity #{i+1}',
            date=_days_ago(random.randint(0, 45)),
            lead_id=leads[i % len(leads)].id,
            opportunity_id=opps[i % len(opps)].id if i < len(opps) else None,
            user_id=random.choice(user_ids),
        )
        db.session.add(act)
    db.session.commit()
    print("  ✓ CRM (leads, opportunities, activities)")


# ── 14. HR ──────────────────────────────────────────────
def seed_hr(tenant_id, users, org_units):
    """Employees, leave types, leave requests, payroll, attendance."""
    if Employee.query.filter_by(tenant_id=tenant_id).first():
        print("  ✓ HR (exists)")
        return

    user_id = users[0].id if users else None
    dept_ids = [u.id for u in org_units if u.unit_type == 'department'][:4] if org_units else [None]

    # Employees
    employees_data = [
        ('EMP001', 'Alice', 'Owner', 'alice@company.com', '+1-555-1001', 90, 'CEO', 'full_time', 180000),
        ('EMP002', 'Bob', 'Admin', 'bob@company.com', '+1-555-1002', 85, 'CTO', 'full_time', 160000),
        ('EMP003', 'Charlie', 'Manager', 'charlie@company.com', '+1-555-1003', 60, 'Engineering Manager', 'full_time', 130000),
        ('EMP004', 'Diana', 'Manager', 'diana@company.com', '+1-555-1004', 55, 'Sales Manager', 'full_time', 120000),
        ('EMP005', 'Eve', 'User', 'eve@company.com', '+1-555-1005', 30, 'Software Engineer', 'full_time', 95000),
        ('EMP006', 'Frank', 'User', 'frank@company.com', '+1-555-1006', 25, 'Frontend Developer', 'full_time', 90000),
        ('EMP007', 'Grace', 'User', 'grace@company.com', '+1-555-1007', 20, 'Sales Representative', 'full_time', 65000),
        ('EMP008', 'Hank', 'Viewer', 'hank@company.com', '+1-555-1008', 10, 'Junior Analyst', 'part_time', 35000),
        ('EMP009', 'Ivy', 'Contractor', 'ivy@external.com', '+1-555-1009', 5, 'UX Designer', 'contract', 80000),
        ('EMP010', 'Jake', 'Intern', 'jake@university.edu', '+1-555-1010', 2, 'Engineering Intern', 'intern', 25000),
        ('EMP011', 'Karen', 'AccountantSr', 'karen@company.com', '+1-555-1011', 40, 'Senior Accountant', 'full_time', 85000),
        ('EMP012', 'Leo', 'HR Specialist', 'leo@company.com', '+1-555-1012', 35, 'HR Business Partner', 'full_time', 75000),
    ]
    employees = []
    for emp_num, first, last, email, phone, days_ago, title, etype, salary in employees_data:
        emp = Employee(
            id=_uid(), tenant_id=tenant_id,
            user_id=users[len(employees) % len(users)].id if users else None,
            employee_number=emp_num, first_name=first, last_name=last,
            email=email, phone=phone,
            hire_date=_date_days_ago(days_ago * 5),
            department_id=dept_ids[len(employees) % len(dept_ids)] if dept_ids[0] else None,
            job_title=title, employment_type=etype,
            status='active', salary=salary, currency='USD',
        )
        db.session.add(emp)
        employees.append(emp)
    db.session.flush()

    # Leave Types
    leave_types_data = [
        ('Annual Leave', 'AL', 21, True),
        ('Sick Leave', 'SL', 10, True),
        ('Personal Leave', 'PL', 5, True),
        ('Maternity Leave', 'ML', 90, True),
        ('Paternity Leave', 'PTL', 14, True),
        ('Unpaid Leave', 'UL', 30, False),
        ('Work From Home', 'WFH', 52, True),
    ]
    leave_types = []
    for name, code, days, is_paid in leave_types_data:
        lt = LeaveType(
            id=_uid(), tenant_id=tenant_id, name=name, code=code,
            default_days=days, is_paid=is_paid,
        )
        db.session.add(lt)
        leave_types.append(lt)
    db.session.flush()

    # Leave Requests
    lr_statuses = ['pending', 'approved', 'rejected', 'approved', 'pending', 'approved']
    for i in range(6):
        emp = employees[i % len(employees)]
        lt = leave_types[i % 3]  # AL, SL, PL
        start = _date_days_ago(random.randint(5, 30))
        days = random.randint(1, 5)
        lr = LeaveRequest(
            id=_uid(), tenant_id=tenant_id, employee_id=emp.id,
            leave_type_id=lt.id, start_date=start,
            end_date=start + timedelta(days=days - 1),
            days=days, reason=f'Demo leave request #{i+1}',
            status=lr_statuses[i],
            approved_by=user_id if lr_statuses[i] in ('approved', 'rejected') else None,
        )
        db.session.add(lr)

    # Payroll Run + Pay Slips
    pr = PayrollRun(
        id=_uid(), tenant_id=tenant_id,
        period_start=date(2026, 1, 1), period_end=date(2026, 1, 31),
        status='completed', processed_by=user_id, processed_at=_days_ago(25),
    )
    total_gross = 0
    total_ded = 0
    total_net = 0
    db.session.add(pr)
    db.session.flush()

    for emp in employees:
        monthly = emp.salary / 12
        deductions = round(monthly * 0.22, 2)  # ~22% taxes + benefits
        net = round(monthly - deductions, 2)
        gross = round(monthly, 2)
        ps = PaySlip(
            id=_uid(), tenant_id=tenant_id, payroll_run_id=pr.id,
            employee_id=emp.id, gross_pay=gross, deductions=deductions,
            net_pay=net, details={
                'basic': round(gross * 0.7, 2),
                'housing_allowance': round(gross * 0.2, 2),
                'transport_allowance': round(gross * 0.1, 2),
                'income_tax': round(deductions * 0.6, 2),
                'social_security': round(deductions * 0.25, 2),
                'health_insurance': round(deductions * 0.15, 2),
            },
        )
        db.session.add(ps)
        total_gross += gross
        total_ded += deductions
        total_net += net

    pr.total_gross = round(total_gross, 2)
    pr.total_deductions = round(total_ded, 2)
    pr.total_net = round(total_net, 2)

    # Attendance records (past 5 work days)
    att_statuses = ['present', 'present', 'present', 'remote', 'half_day', 'absent']
    for emp in employees[:8]:  # First 8 employees
        for d in range(5):
            att_date = _date_days_ago(d)
            if att_date.weekday() >= 5:
                continue  # Skip weekends
            status = random.choice(att_statuses)
            check_in = _days_ago(d).replace(hour=random.randint(8, 9), minute=random.randint(0, 30))
            check_out = check_in + timedelta(hours=random.randint(7, 9), minutes=random.randint(0, 59))
            att = Attendance(
                id=_uid(), tenant_id=tenant_id, employee_id=emp.id,
                date=att_date, check_in=check_in, check_out=check_out if status != 'absent' else None,
                status=status,
            )
            db.session.add(att)

    db.session.commit()
    print("  ✓ HR (employees, leave types, leave requests, payroll, attendance)")
    return employees


# ── 15. Events & Notifications ──────────────────────────
def seed_events(tenant_id, users):
    """Create event logs and notifications."""
    if EventLog.query.filter_by(tenant_id=tenant_id).first():
        print("  ✓ Events (exists)")
        return

    user_ids = [u.id for u in users] if users else [None]

    event_types = [
        'tenant.created', 'user.logged_in', 'user.invited',
        'module.installed', 'module.enabled',
        'inventory.product.created', 'inventory.stock.adjusted',
        'sales.invoice.created', 'sales.payment.received',
        'purchasing.order.created', 'purchasing.goods.received',
        'accounting.journal.posted', 'hr.leave.approved',
        'crm.lead.created', 'crm.opportunity.won',
    ]

    for i in range(25):
        ev = EventLog(
            id=_uid(), event_type=event_types[i % len(event_types)],
            tenant_id=tenant_id, user_id=random.choice(user_ids),
            data={'detail': f'Demo event #{i+1}', 'module': event_types[i % len(event_types)].split('.')[0]},
            source='api', correlation_id=_uid() if i % 3 == 0 else None,
            created_at=_days_ago(random.randint(0, 30)),
        )
        db.session.add(ev)

    # Notifications
    notif_data = [
        ('sales.invoice.paid', 'Invoice Paid', 'Invoice INV-2026-0004 has been paid in full'),
        ('inventory.stock.low', 'Low Stock Alert', 'Dell XPS 15 is below reorder point (15 units remaining)'),
        ('hr.leave.requested', 'New Leave Request', 'Charlie Manager requested 3 days of annual leave'),
        ('crm.opportunity.won', 'Deal Won!', 'Wilson Technologies deal worth $45,000 has been won'),
        ('purchasing.order.received', 'Goods Received', 'PO-2026-0004 from Pacific Logistics has been received'),
        ('accounting.journal.posted', 'Journal Posted', 'Journal entry JE-2026-0008 has been posted'),
        ('system.update', 'System Update', 'New AI suggestions are available for your review'),
    ]
    for uid in user_ids[:3]:
        for evt, title, msg in notif_data:
            notif = Notification(
                id=_uid(), tenant_id=tenant_id, user_id=uid,
                event_type=evt, title=title, message=msg,
                is_read=random.choice([True, False]),
                created_at=_days_ago(random.randint(0, 14)),
            )
            db.session.add(notif)

    db.session.commit()
    print("  ✓ Events & notifications")


# ── 16. Analytics Events ────────────────────────────────
def seed_analytics(tenant_id, users):
    """Create analytics event history."""
    if AnalyticsEvent.query.filter_by(tenant_id=tenant_id).first():
        print("  ✓ Analytics (exists)")
        return

    user_ids = [u.id for u in users] if users else [None]

    event_combos = [
        ('page_view', 'navigation', 'view_page', '/dashboard'),
        ('page_view', 'navigation', 'view_page', '/inventory'),
        ('page_view', 'navigation', 'view_page', '/sales'),
        ('page_view', 'navigation', 'view_page', '/accounting'),
        ('api_call', 'inventory', 'list_products', '/api/inventory/products'),
        ('api_call', 'sales', 'create_invoice', '/api/sales/invoices'),
        ('api_call', 'purchasing', 'create_order', '/api/purchasing/orders'),
        ('user_action', 'inventory', 'adjust_stock', '/api/inventory/stock'),
        ('user_action', 'sales', 'record_payment', '/api/sales/payments'),
        ('user_action', 'crm', 'update_lead', '/api/crm/leads'),
        ('user_action', 'hr', 'approve_leave', '/api/hr/leave'),
        ('ai_interaction', 'ai', 'chat_message', '/api/ai/chat'),
        ('ai_interaction', 'ai', 'tool_execution', '/api/ai/tools'),
        ('system_event', 'system', 'module_loaded', None),
    ]

    session_id = _uid()
    for i in range(50):
        if i % 10 == 0:
            session_id = _uid()
        evt_type, cat, action, endpoint = event_combos[i % len(event_combos)]
        ae = AnalyticsEvent(
            id=_uid(), tenant_id=tenant_id,
            user_id=random.choice(user_ids), session_id=session_id,
            event_type=evt_type, event_category=cat, event_action=action,
            endpoint=endpoint, method='GET' if 'view' in action or 'list' in action else 'POST',
            status_code=200, duration_ms=random.randint(50, 2000),
            source='api', created_at=_days_ago(random.randint(0, 30)),
        )
        db.session.add(ae)
    db.session.commit()
    print("  ✓ Analytics events")


# ── 17. AI: Conversations, Messages, Interaction Logs ───
def seed_ai(tenant_id, users):
    """Create AI conversations, messages, and interaction logs."""
    if Conversation.query.filter_by(tenant_id=tenant_id).first():
        print("  ✓ AI conversations (exists)")
        return

    user_id = users[0].id if users else None

    # Conversations
    convos = [
        ('Inventory Analysis', [
            ('user', 'Show me products that are below reorder point'),
            ('assistant', 'I found 3 products below their reorder points:\n1. Dell XPS 15 — 12 units (reorder at 15)\n2. Standing Desk Pro — 6 units (reorder at 8)\n3. Copper Wire — 450m (reorder at 500m)\n\nWould you like me to create purchase orders for these items?'),
            ('user', 'Yes, create a PO for the Dell XPS 15'),
            ('assistant', 'I\'ve created Purchase Order PO-2026-0006 for 10 units of Dell XPS 15 from Taiwan Semiconductor Supply at $1,200/unit. Total: $13,200 (incl. tax). The order is in draft status — would you like me to send it?'),
        ]),
        ('Sales Report', [
            ('user', 'What are our overdue invoices?'),
            ('assistant', 'You have 1 overdue invoice:\n\n- **INV-2026-0005** — Green Valley School — $3,245.50 — Due 15 days ago\n\nTotal overdue: $3,245.50. Would you like me to send a payment reminder?'),
        ]),
        ('HR Question', [
            ('user', 'How many pending leave requests do we have?'),
            ('assistant', 'You currently have **2 pending leave requests**:\n\n1. **Alice Owner** — 3 days Annual Leave (Mar 1-3)\n2. **Eve User** — 2 days Personal Leave (Mar 5-6)\n\nWould you like to approve or reject any of these?'),
        ]),
    ]

    for title, messages in convos:
        conv = Conversation(
            id=_uid(), tenant_id=tenant_id, user_id=user_id,
            title=title, status='active',
        )
        db.session.add(conv)
        db.session.flush()
        for role, content in messages:
            msg = Message(
                id=_uid(), conversation_id=conv.id, role=role, content=content,
                tokens_used=len(content.split()) * 2, model='mock-llm',
            )
            db.session.add(msg)

    # AI Interaction Logs
    action_types = ['chat', 'suggestion', 'nl_query']
    tools = ['list_products', 'create_invoice', 'get_stock_levels', 'list_customers', 'search_orders']
    feedbacks = ['thumbs_up', 'thumbs_up', 'thumbs_down', None, None]

    for i in range(15):
        log = AIInteractionLog(
            id=_uid(), tenant_id=tenant_id, user_id=user_id,
            action_type=action_types[i % len(action_types)],
            input_summary=f'Demo query #{i+1}',
            output_summary=f'Demo response #{i+1}',
            tools_used=[random.choice(tools)] if i % 2 == 0 else None,
            feedback=random.choice(feedbacks),
            latency_ms=random.randint(100, 3000),
            tokens_in=random.randint(50, 200),
            tokens_out=random.randint(100, 500),
            model='mock-llm',
            created_at=_days_ago(random.randint(0, 20)),
        )
        db.session.add(log)

    db.session.commit()
    print("  ✓ AI conversations, messages, interaction logs")


# ── 18. AI Advanced (Phase 9) ───────────────────────────
def seed_ai_advanced(tenant_id, users):
    """Create suggestions, agent actions, workflow patterns, workflows, training data."""
    if AISuggestion.query.filter_by(tenant_id=tenant_id).first():
        print("  ✓ AI Advanced (exists)")
        return

    user_id = users[0].id if users else None

    # AI Suggestions
    suggestions_data = [
        ('action', 'inventory', 'Reorder Dell XPS 15', 'Stock is below reorder point. Recommend ordering 10 units.', 0.92, 'high',
         'Based on current stock level (12) being below reorder point (15) and average monthly sales of 8 units.',
         {'tool_name': 'create_purchase_order', 'arguments': {'product_sku': 'DELL-XPS15', 'quantity': 10}}),
        ('insight', 'sales', 'Revenue trending up 15%', 'Monthly revenue increased 15% compared to last month.', 0.88, 'medium',
         'Calculated from paid invoices in current vs previous 30-day period.', None),
        ('warning', 'hr', 'Burnout risk detected', '3 employees have not taken leave in over 90 days.', 0.75, 'high',
         'Pattern detected from attendance and leave records showing no leave taken.', None),
        ('automation', 'accounting', 'Auto-reconcile payments', 'Detected recurring pattern of matching payments to invoices.', 0.85, 'medium',
         'Based on analysis of 50+ payment-invoice matching operations in the last 30 days.',
         {'tool_name': 'reconcile_payments', 'arguments': {'auto': True}}),
        ('action', 'crm', 'Follow up stale leads', '5 leads have not been contacted in over 14 days.', 0.78, 'medium',
         'Leads scored above 60 with last activity older than 14 days.', None),
        ('insight', 'inventory', 'Seasonal demand forecast', 'Electronics demand expected to spike 30% next month based on historical data.', 0.70, 'low',
         'ML model prediction based on 12 months of historical sales data.', None),
        ('warning', 'sales', 'Customer payment delay', 'Global Enterprises has 2 overdue invoices totalling $12,500.', 0.95, 'critical',
         'Both invoices are 20+ days overdue, compared to their usual 10-day payment cycle.', None),
    ]
    for stype, cat, title, desc, conf, priority, reasoning, action_data in suggestions_data:
        s = AISuggestion(
            id=_uid(), tenant_id=tenant_id, user_id=user_id,
            suggestion_type=stype, category=cat, title=title,
            description=desc, confidence=conf, reasoning=reasoning,
            action_data=action_data, status='pending', priority=priority,
        )
        db.session.add(s)

    # Agent Actions
    actions_data = [
        ('create_record', 'Create purchase order for low-stock items', 'create_purchase_order',
         {'supplier_id': 'auto', 'items': [{'sku': 'DELL-XPS15', 'qty': 10}]},
         0.88, 'medium', 'proposed'),
        ('update_record', 'Update lead status to qualified', 'update_lead',
         {'lead_id': 'auto', 'status': 'qualified'},
         0.92, 'low', 'executed'),
        ('notification', 'Send payment reminder to Global Enterprises', 'send_notification',
         {'customer': 'Global Enterprises', 'template': 'payment_reminder'},
         0.85, 'low', 'approved'),
        ('workflow', 'Auto-close resolved support tickets', 'close_tickets',
         {'filter': 'resolved', 'days_old': 7},
         0.78, 'medium', 'proposed'),
        ('create_record', 'Generate monthly financial report', 'generate_report',
         {'type': 'financial', 'period': '2026-01'},
         0.95, 'low', 'executed'),
    ]
    for atype, desc, tool, params, conf, risk, status in actions_data:
        aa = AgentAction(
            id=_uid(), tenant_id=tenant_id, user_id=user_id,
            action_type=atype, description=desc, tool_name=tool,
            parameters=params, confidence=conf, risk_level=risk,
            reasoning=f'Automated action based on detected patterns',
            requires_approval=(risk != 'low'),
            status=status,
            executed_at=_days_ago(2) if status == 'executed' else None,
        )
        db.session.add(aa)

    # Workflow Patterns
    patterns_data = [
        ('Create Invoice → Record Payment', [
            {'action': 'create_invoice', 'resource_type': 'invoices'},
            {'action': 'record_payment', 'resource_type': 'payments'},
        ], 25, 0.85, 'activated'),
        ('Create Lead → Create Opportunity', [
            {'action': 'create_lead', 'resource_type': 'leads'},
            {'action': 'create_opportunity', 'resource_type': 'opportunities'},
        ], 18, 0.78, 'detected'),
        ('Approve Leave → Update Attendance', [
            {'action': 'approve_leave', 'resource_type': 'leave_requests'},
            {'action': 'update_attendance', 'resource_type': 'attendances'},
        ], 12, 0.72, 'suggested'),
        ('Receive Goods → Adjust Stock → Post Journal', [
            {'action': 'receive_goods', 'resource_type': 'purchase_orders'},
            {'action': 'adjust_stock', 'resource_type': 'stock_entries'},
            {'action': 'post_journal', 'resource_type': 'journal_entries'},
        ], 8, 0.68, 'detected'),
    ]
    patterns = []
    for name, steps, freq, conf, status in patterns_data:
        wp = WorkflowPattern(
            id=_uid(), tenant_id=tenant_id, name=name,
            description=f'Detected pattern: {name}', steps=steps,
            frequency=freq, confidence=conf, status=status,
        )
        db.session.add(wp)
        patterns.append(wp)
    db.session.flush()

    # Automated Workflows
    workflows_data = [
        (patterns[0].id, 'Auto-create payment on invoice', 'sales.invoice.paid',
         [{'tool_name': 'record_payment', 'parameters': {'auto_match': True}}], True, 15),
        (None, 'Weekly inventory report', 'system.cron.weekly',
         [{'tool_name': 'generate_report', 'parameters': {'type': 'inventory_summary'}}], True, 8),
        (None, 'Welcome email for new leads', 'crm.lead.created',
         [{'tool_name': 'send_notification', 'parameters': {'template': 'welcome_lead'}}], False, 0),
    ]
    for pid, name, trigger, steps, active, exec_count in workflows_data:
        aw = AutomatedWorkflow(
            id=_uid(), tenant_id=tenant_id, pattern_id=pid,
            name=name, description=f'Automated: {name}',
            trigger_event=trigger, steps=steps, is_active=active,
            execution_count=exec_count, created_by=user_id,
            last_executed_at=_days_ago(1) if exec_count > 0 else None,
        )
        db.session.add(aw)

    # Training Datasets
    ds = TrainingDataset(
        id=_uid(), version='1.0.0', record_count=500,
        source_types=['ai_interaction_log', 'analytics_event'],
        anonymised=True, status='ready',
        date_range_start=_days_ago(90), date_range_end=_days_ago(0),
        metadata_info={
            'feedback_distribution': {'thumbs_up': 320, 'thumbs_down': 45, 'none': 135},
            'tool_usage': {'list_products': 120, 'create_invoice': 85, 'get_stock_levels': 95},
        },
    )
    db.session.add(ds)
    db.session.flush()

    ds2 = TrainingDataset(
        id=_uid(), version='0.9.0', record_count=200,
        source_types=['ai_interaction_log'],
        anonymised=True, status='archived',
        date_range_start=_days_ago(180), date_range_end=_days_ago(90),
        metadata_info={'feedback_distribution': {'thumbs_up': 140, 'thumbs_down': 30, 'none': 30}},
    )
    db.session.add(ds2)
    db.session.flush()

    # Model Versions
    models_data = [
        ('1.0.0', 'intent_classifier', ds.id,
         {'accuracy': 0.91, 'precision': 0.89, 'recall': 0.93, 'f1': 0.91},
         {'epochs': 10, 'learning_rate': 0.001, 'batch_size': 32}, 'active', True),
        ('0.9.0', 'intent_classifier', ds2.id,
         {'accuracy': 0.85, 'precision': 0.83, 'recall': 0.87, 'f1': 0.85},
         {'epochs': 8, 'learning_rate': 0.001, 'batch_size': 32}, 'retired', False),
        ('1.0.0', 'recommendation', ds.id,
         {'accuracy': 0.88, 'precision': 0.86, 'recall': 0.90, 'f1': 0.88},
         {'epochs': 15, 'learning_rate': 0.0005, 'batch_size': 64}, 'active', True),
        ('1.0.0', 'anomaly_detector', ds.id,
         {'accuracy': 0.82, 'precision': 0.79, 'recall': 0.85, 'f1': 0.82},
         {'epochs': 20, 'learning_rate': 0.0001, 'batch_size': 16}, 'evaluating', False),
    ]
    for ver, mtype, dsid, metrics, params, status, active in models_data:
        mv = ModelVersion(
            id=_uid(), version=ver, model_type=mtype,
            training_dataset_id=dsid, metrics=metrics, parameters=params,
            status=status, is_active=active,
            trained_at=_days_ago(10),
            activated_at=_days_ago(5) if active else None,
        )
        db.session.add(mv)

    db.session.commit()
    print("  ✓ AI Advanced (suggestions, actions, patterns, workflows, training, models)")


# ── 19. Audit Logs ──────────────────────────────────────
def seed_audit_logs(tenant_id, users):
    """Create audit trail entries."""
    if AuditLog.query.filter_by(tenant_id=tenant_id).first():
        print("  ✓ Audit logs (exists)")
        return

    user_ids = [u.id for u in users] if users else [None]

    audit_entries = [
        ('user.login', 'user', 'User logged in from Chrome'),
        ('user.invite', 'user', 'Invited eve.user@acmecorporation.com'),
        ('product.create', 'product', 'Created product MacBook Pro 16"'),
        ('product.update', 'product', 'Updated price of Dell XPS 15'),
        ('invoice.create', 'invoice', 'Created invoice INV-2026-0001'),
        ('invoice.send', 'invoice', 'Invoice INV-2026-0001 sent to customer'),
        ('payment.record', 'payment', 'Payment of $5,499.97 recorded'),
        ('leave.approve', 'leave_request', 'Approved 3-day annual leave for Charlie'),
        ('journal.post', 'journal_entry', 'Posted journal entry JE-2026-0006'),
        ('module.install', 'module', 'Installed Accounting module'),
        ('role.assign', 'user', 'Assigned Manager role to Diana'),
        ('stock.adjust', 'stock_entry', 'Adjusted stock for Logitech MX Master'),
        ('lead.create', 'lead', 'Created new lead James Wilson'),
        ('opportunity.update', 'opportunity', 'Moved deal to negotiation stage'),
        ('report.generate', 'report', 'Generated trial balance report'),
    ]
    for action, rtype, detail in audit_entries:
        al = AuditLog(
            id=_uid(), tenant_id=tenant_id, user_id=random.choice(user_ids),
            action=action, resource_type=rtype, resource_id=_uid(),
            details={'description': detail},
            ip_address=f'192.168.1.{random.randint(10, 200)}',
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            created_at=_days_ago(random.randint(0, 30)),
        )
        db.session.add(al)
    db.session.commit()
    print("  ✓ Audit logs")


# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════
def seed_demo():
    """Run all demo data seeders."""
    print("=" * 60)
    print("  AgentERP — Demo Data Seeder")
    print("=" * 60)

    # ── Foundation ──
    print("\n📦 Foundation")
    seed_plans()
    admin = seed_platform_admin()
    tenants = seed_tenants()
    seed_subscriptions(tenants)
    seed_rbac(tenants)
    users_map = seed_users(tenants)

    # ── Per-tenant data (Acme — full dataset) ──
    t1 = tenants[0]
    t1_users = users_map[t1.id]
    print(f"\n🏢 {t1.name} (full demo data)")
    org_map = seed_org(tenants)
    seed_modules(tenants)

    inv_result = seed_inventory(t1.id, t1_users)
    products = inv_result[0] if inv_result else Product.query.filter_by(tenant_id=t1.id).all()
    warehouses = inv_result[1] if inv_result else Warehouse.query.filter_by(tenant_id=t1.id).all()

    sales_result = seed_sales(t1.id, t1_users, products)
    customers = sales_result[0] if sales_result else Customer.query.filter_by(tenant_id=t1.id).all()

    seed_purchasing(t1.id, t1_users, products, warehouses)
    seed_accounting(t1.id, t1_users)
    seed_crm(t1.id, t1_users, customers)
    seed_hr(t1.id, t1_users, org_map.get(t1.id, []))
    seed_events(t1.id, t1_users)
    seed_analytics(t1.id, t1_users)
    seed_ai(t1.id, t1_users)
    seed_ai_advanced(t1.id, t1_users)
    seed_audit_logs(t1.id, t1_users)

    # ── Per-tenant data (Globex — lightweight) ──
    t2 = tenants[1]
    t2_users = users_map[t2.id]
    print(f"\n🏢 {t2.name} (lightweight demo data)")
    inv_result2 = seed_inventory(t2.id, t2_users)
    products2 = inv_result2[0] if inv_result2 else Product.query.filter_by(tenant_id=t2.id).all()
    warehouses2 = inv_result2[1] if inv_result2 else Warehouse.query.filter_by(tenant_id=t2.id).all()
    seed_sales(t2.id, t2_users, products2)
    seed_purchasing(t2.id, t2_users, products2, warehouses2)

    # ── Summary ──
    print("\n" + "=" * 60)
    print("  ✅ Demo data seeding complete!")
    print("=" * 60)
    print("\n  Login credentials:")
    print("  ┌──────────────────┬────────────────────────────────┬──────────┐")
    print("  │ Role             │ Email                          │ Password │")
    print("  ├──────────────────┼────────────────────────────────┼──────────┤")
    print("  │ Platform Admin   │ admin@agenterp.com             │ admin123 │")
    print("  │ Owner (Acme)     │ alice.owner@acmecorporation.com│ demo1234 │")
    print("  │ Admin (Acme)     │ bob.admin@acmecorporation.com  │ demo1234 │")
    print("  │ Manager (Acme)   │ charlie.manager@acmecorporation.com │ demo1234 │")
    print("  │ User (Acme)      │ eve.user@acmecorporation.com   │ demo1234 │")
    print("  │ Viewer (Acme)    │ hank.viewer@acmecorporation.com│ demo1234 │")
    print("  │ Owner (Globex)   │ alice.owner@globexinc.com      │ demo1234 │")
    print("  │ Admin (Globex)   │ bob.admin@globexinc.com        │ demo1234 │")
    print("  └──────────────────┴────────────────────────────────┴──────────┘")
    print()


if __name__ == '__main__':
    reset = '--reset' in sys.argv

    app = create_app()
    with app.app_context():
        if reset:
            print("⚠️  Dropping all tables...")
            db.drop_all()
            print("   Creating fresh tables...")

        db.create_all()
        seed_demo()
