"""Phase 3 – Module system, Inventory, Sales, Purchasing API tests.

Covers:
 1. Module seed / install / uninstall / dependency resolution
 2. Inventory CRUD (categories, products, warehouses, stock)
 3. Sales workflow (customer → quotation → invoice conversion → payment)
 4. Purchasing workflow (supplier → PO → goods receipt → stock update)
 5. Module-gated access (403 when module not enabled)
"""
import pytest


# ── helpers ──────────────────────────────────────────────────

def _seed_and_install(client, headers):
    """Seed default modules and install all three."""
    client.post('/api/modules/seed', headers=headers)
    for slug in ['inventory', 'sales', 'purchasing']:
        client.post(f'/api/modules/{slug}/install', headers=headers)


# ════════════════════════════════════════════════════════════
#  1.  MODULE SYSTEM
# ════════════════════════════════════════════════════════════

class TestModules:

    def test_seed_modules(self, client, auth_headers):
        headers, _ = auth_headers
        resp = client.post('/api/modules/seed', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['message'] == 'Modules seeded'

    def test_list_available(self, client, auth_headers):
        headers, _ = auth_headers
        client.post('/api/modules/seed', headers=headers)
        resp = client.get('/api/modules/available', headers=headers)
        assert resp.status_code == 200
        modules = resp.get_json()['modules']
        assert len(modules) >= 3
        slugs = {m['slug'] for m in modules}
        assert {'inventory', 'sales', 'purchasing'} <= slugs

    def test_install_with_dependency(self, client, auth_headers):
        """Installing 'sales' should auto-install 'inventory' (dependency)."""
        headers, _ = auth_headers
        client.post('/api/modules/seed', headers=headers)
        resp = client.post('/api/modules/sales/install', headers=headers)
        assert resp.status_code == 201
        installed = resp.get_json()['installed']
        assert 'inventory' in installed
        assert 'sales' in installed

    def test_install_idempotent(self, client, auth_headers):
        headers, _ = auth_headers
        client.post('/api/modules/seed', headers=headers)
        client.post('/api/modules/inventory/install', headers=headers)
        resp = client.post('/api/modules/inventory/install', headers=headers)
        # Second install returns 201 with empty installed list (already installed)
        assert resp.status_code == 201

    def test_uninstall_blocked_by_dependency(self, client, auth_headers):
        """Cannot uninstall 'inventory' while 'sales' depends on it."""
        headers, _ = auth_headers
        _seed_and_install(client, headers)
        resp = client.post('/api/modules/inventory/uninstall', headers=headers)
        assert resp.status_code == 400
        assert 'depends on it' in resp.get_json()['error']

    def test_uninstall_success(self, client, auth_headers):
        headers, _ = auth_headers
        _seed_and_install(client, headers)
        # Uninstall sales first (depends on inventory)
        resp = client.post('/api/modules/sales/uninstall', headers=headers)
        assert resp.status_code == 200
        # Now uninstall purchasing (also depends on inventory)
        resp = client.post('/api/modules/purchasing/uninstall', headers=headers)
        assert resp.status_code == 200
        # Now inventory can be uninstalled
        resp = client.post('/api/modules/inventory/uninstall', headers=headers)
        assert resp.status_code == 200

    def test_list_installed(self, client, auth_headers):
        headers, _ = auth_headers
        _seed_and_install(client, headers)
        resp = client.get('/api/modules/installed', headers=headers)
        assert resp.status_code == 200
        modules = resp.get_json()['modules']
        assert len(modules) == 3


# ════════════════════════════════════════════════════════════
#  2.  INVENTORY MODULE
# ════════════════════════════════════════════════════════════

class TestInventory:

    def _setup(self, client, headers):
        _seed_and_install(client, headers)

    # ── Module-gated access ──────────────────────────────────

    def test_403_when_module_disabled(self, client, auth_headers):
        headers, _ = auth_headers
        client.post('/api/modules/seed', headers=headers)
        # Don't install inventory module
        resp = client.get('/api/inventory/categories', headers=headers)
        assert resp.status_code == 403

    # ── Categories ───────────────────────────────────────────

    def test_create_category(self, client, auth_headers):
        headers, _ = auth_headers
        self._setup(client, headers)
        resp = client.post('/api/inventory/categories', headers=headers, json={
            'name': 'Electronics',
        })
        assert resp.status_code == 201
        cat = resp.get_json()['category']
        assert cat['name'] == 'Electronics'
        assert cat['slug'] == 'electronics'

    def test_list_categories(self, client, auth_headers):
        headers, _ = auth_headers
        self._setup(client, headers)
        client.post('/api/inventory/categories', headers=headers,
                     json={'name': 'Cat A'})
        client.post('/api/inventory/categories', headers=headers,
                     json={'name': 'Cat B'})
        resp = client.get('/api/inventory/categories', headers=headers)
        assert resp.status_code == 200
        assert len(resp.get_json()['categories']) == 2

    def test_update_category(self, client, auth_headers):
        headers, _ = auth_headers
        self._setup(client, headers)
        r = client.post('/api/inventory/categories', headers=headers,
                         json={'name': 'Old'})
        cat_id = r.get_json()['category']['id']
        resp = client.put(f'/api/inventory/categories/{cat_id}', headers=headers,
                           json={'name': 'New'})
        assert resp.status_code == 200
        assert resp.get_json()['category']['name'] == 'New'

    def test_delete_category(self, client, auth_headers):
        headers, _ = auth_headers
        self._setup(client, headers)
        r = client.post('/api/inventory/categories', headers=headers,
                         json={'name': 'ToDelete'})
        cat_id = r.get_json()['category']['id']
        resp = client.delete(f'/api/inventory/categories/{cat_id}', headers=headers)
        assert resp.status_code == 200

    # ── Products ─────────────────────────────────────────────

    def test_create_product(self, client, auth_headers):
        headers, _ = auth_headers
        self._setup(client, headers)
        resp = client.post('/api/inventory/products', headers=headers, json={
            'name': 'Widget',
            'sku': 'WID-001',
            'sale_price': 29.99,
            'cost_price': 12.50,
            'tax_rate': 10,
            'product_type': 'goods',
        })
        assert resp.status_code == 201
        prod = resp.get_json()['product']
        assert prod['name'] == 'Widget'
        assert prod['sku'] == 'WID-001'
        assert prod['sale_price'] == 29.99

    def test_list_products_search(self, client, auth_headers):
        headers, _ = auth_headers
        self._setup(client, headers)
        client.post('/api/inventory/products', headers=headers,
                     json={'name': 'Alpha', 'sku': 'A1'})
        client.post('/api/inventory/products', headers=headers,
                     json={'name': 'Beta', 'sku': 'B1'})
        resp = client.get('/api/inventory/products?search=alpha', headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['total'] == 1

    def test_duplicate_sku_rejected(self, client, auth_headers):
        headers, _ = auth_headers
        self._setup(client, headers)
        client.post('/api/inventory/products', headers=headers,
                     json={'name': 'P1', 'sku': 'DUP'})
        resp = client.post('/api/inventory/products', headers=headers,
                            json={'name': 'P2', 'sku': 'DUP'})
        assert resp.status_code == 400

    # ── Warehouses ───────────────────────────────────────────

    def test_create_warehouse(self, client, auth_headers):
        headers, _ = auth_headers
        self._setup(client, headers)
        resp = client.post('/api/inventory/warehouses', headers=headers, json={
            'name': 'Main WH',
            'code': 'WH-01',
        })
        assert resp.status_code == 201
        wh = resp.get_json()['warehouse']
        assert wh['name'] == 'Main WH'

    # ── Stock ────────────────────────────────────────────────

    def test_adjust_stock(self, client, auth_headers):
        headers, _ = auth_headers
        self._setup(client, headers)
        # Create product + warehouse
        prod = client.post('/api/inventory/products', headers=headers,
                            json={'name': 'StockItem', 'product_type': 'goods'}).get_json()['product']
        wh = client.post('/api/inventory/warehouses', headers=headers,
                          json={'name': 'WH1', 'code': 'W1'}).get_json()['warehouse']
        # Adjust +50
        resp = client.post('/api/inventory/stock/adjust', headers=headers, json={
            'product_id': prod['id'],
            'warehouse_id': wh['id'],
            'quantity': 50,
            'notes': 'Initial stock',
        })
        assert resp.status_code == 201
        assert resp.get_json()['stock_entry']['quantity'] == 50

    def test_stock_movements(self, client, auth_headers):
        headers, _ = auth_headers
        self._setup(client, headers)
        prod = client.post('/api/inventory/products', headers=headers,
                            json={'name': 'MoveItem'}).get_json()['product']
        wh = client.post('/api/inventory/warehouses', headers=headers,
                          json={'name': 'WH2', 'code': 'W2'}).get_json()['warehouse']
        client.post('/api/inventory/stock/adjust', headers=headers, json={
            'product_id': prod['id'], 'warehouse_id': wh['id'], 'quantity': 10,
        })
        resp = client.get('/api/inventory/stock/movements', headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['total'] >= 1

    def test_inventory_stats(self, client, auth_headers):
        headers, _ = auth_headers
        self._setup(client, headers)
        resp = client.get('/api/inventory/stats', headers=headers)
        assert resp.status_code == 200
        stats = resp.get_json()['stats']
        assert 'total_products' in stats


# ════════════════════════════════════════════════════════════
#  3.  SALES MODULE
# ════════════════════════════════════════════════════════════

class TestSales:

    def _setup(self, client, headers):
        """Install modules and create a customer + product for use in tests."""
        _seed_and_install(client, headers)
        cust = client.post('/api/sales/customers', headers=headers, json={
            'name': 'Acme Corp', 'email': 'acme@example.com',
        }).get_json()['customer']
        prod = client.post('/api/inventory/products', headers=headers, json={
            'name': 'Test Product', 'sku': 'TP-001',
            'sale_price': 100, 'cost_price': 50, 'tax_rate': 10,
            'product_type': 'goods',
        }).get_json()['product']
        wh = client.post('/api/inventory/warehouses', headers=headers, json={
            'name': 'Sales WH', 'code': 'SWH',
        }).get_json()['warehouse']
        # Add initial stock
        client.post('/api/inventory/stock/adjust', headers=headers, json={
            'product_id': prod['id'], 'warehouse_id': wh['id'], 'quantity': 100,
        })
        return cust, prod, wh

    # ── Customers ────────────────────────────────────────────

    def test_customer_crud(self, client, auth_headers):
        headers, _ = auth_headers
        _seed_and_install(client, headers)
        # Create
        resp = client.post('/api/sales/customers', headers=headers, json={
            'name': 'NewCust', 'email': 'new@cust.com',
        })
        assert resp.status_code == 201
        cust_id = resp.get_json()['customer']['id']
        # Read
        resp = client.get(f'/api/sales/customers/{cust_id}', headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['customer']['name'] == 'NewCust'
        # Update
        resp = client.put(f'/api/sales/customers/{cust_id}', headers=headers,
                           json={'name': 'Updated'})
        assert resp.status_code == 200
        assert resp.get_json()['customer']['name'] == 'Updated'
        # List
        resp = client.get('/api/sales/customers', headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['total'] >= 1

    def test_customer_name_required(self, client, auth_headers):
        headers, _ = auth_headers
        _seed_and_install(client, headers)
        resp = client.post('/api/sales/customers', headers=headers, json={
            'email': 'noname@x.com',
        })
        assert resp.status_code == 400

    # ── Quotations ───────────────────────────────────────────

    def test_create_quotation_with_items(self, client, auth_headers):
        headers, _ = auth_headers
        cust, prod, wh = self._setup(client, headers)
        resp = client.post('/api/sales/quotations', headers=headers, json={
            'customer_id': cust['id'],
            'items': [
                {'product_id': prod['id'], 'quantity': 5, 'unit_price': 100},
            ],
        })
        assert resp.status_code == 201
        quote = resp.get_json()['quotation']
        assert quote['number'].startswith('QT-')
        assert quote['status'] == 'draft'
        assert len(quote['items']) == 1
        assert quote['subtotal'] == 500.0
        assert quote['tax_amount'] == 50.0  # 10% of 500
        assert quote['total'] == 550.0

    def test_list_quotations(self, client, auth_headers):
        headers, _ = auth_headers
        cust, prod, wh = self._setup(client, headers)
        client.post('/api/sales/quotations', headers=headers, json={
            'customer_id': cust['id'],
            'items': [{'product_id': prod['id'], 'quantity': 1}],
        })
        resp = client.get('/api/sales/quotations', headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['total'] == 1

    def test_update_quotation(self, client, auth_headers):
        headers, _ = auth_headers
        cust, prod, wh = self._setup(client, headers)
        r = client.post('/api/sales/quotations', headers=headers, json={
            'customer_id': cust['id'],
            'items': [{'product_id': prod['id'], 'quantity': 2}],
        })
        qid = r.get_json()['quotation']['id']
        resp = client.put(f'/api/sales/quotations/{qid}', headers=headers, json={
            'status': 'sent',
        })
        assert resp.status_code == 200
        assert resp.get_json()['quotation']['status'] == 'sent'

    # ── Quotation → Invoice conversion ───────────────────────

    def test_convert_quotation_to_invoice(self, client, auth_headers):
        """Core integration: convert quotation to invoice, check stock deduction."""
        headers, _ = auth_headers
        cust, prod, wh = self._setup(client, headers)
        # Create quotation
        qr = client.post('/api/sales/quotations', headers=headers, json={
            'customer_id': cust['id'],
            'items': [{'product_id': prod['id'], 'quantity': 10, 'unit_price': 100}],
        })
        qid = qr.get_json()['quotation']['id']
        # Convert to invoice (with warehouse → deducts stock)
        resp = client.post(f'/api/sales/quotations/{qid}/convert', headers=headers,
                            json={'warehouse_id': wh['id']})
        assert resp.status_code == 201
        invoice = resp.get_json()['invoice']
        assert invoice['number'].startswith('INV-')
        assert invoice['total'] == 1100.0  # 10 * 100 + 10% tax
        assert len(invoice['items']) == 1
        # Quotation should now be 'converted'
        qr2 = client.get(f'/api/sales/quotations/{qid}', headers=headers)
        assert qr2.get_json()['quotation']['status'] == 'converted'
        # Stock should be reduced by 10 (was 100, now 90)
        stock = client.get(f'/api/inventory/stock?product_id={prod["id"]}&warehouse_id={wh["id"]}',
                            headers=headers)
        assert stock.status_code == 200
        entries = stock.get_json()['stock']
        assert entries[0]['quantity'] == 90

    def test_convert_already_converted_fails(self, client, auth_headers):
        headers, _ = auth_headers
        cust, prod, wh = self._setup(client, headers)
        qr = client.post('/api/sales/quotations', headers=headers, json={
            'customer_id': cust['id'],
            'items': [{'product_id': prod['id'], 'quantity': 1}],
        })
        qid = qr.get_json()['quotation']['id']
        client.post(f'/api/sales/quotations/{qid}/convert', headers=headers, json={})
        resp = client.post(f'/api/sales/quotations/{qid}/convert', headers=headers, json={})
        assert resp.status_code == 400
        assert 'already converted' in resp.get_json()['error']

    # ── Invoices ─────────────────────────────────────────────

    def test_create_invoice_directly(self, client, auth_headers):
        headers, _ = auth_headers
        cust, prod, wh = self._setup(client, headers)
        resp = client.post('/api/sales/invoices', headers=headers, json={
            'customer_id': cust['id'],
            'warehouse_id': wh['id'],
            'items': [{'product_id': prod['id'], 'quantity': 3, 'unit_price': 100}],
        })
        assert resp.status_code == 201
        inv = resp.get_json()['invoice']
        assert inv['total'] == 330.0  # 3*100 + 10% tax
        assert inv['balance_due'] == 330.0
        assert inv['amount_paid'] == 0

    def test_update_invoice_status(self, client, auth_headers):
        headers, _ = auth_headers
        cust, prod, wh = self._setup(client, headers)
        r = client.post('/api/sales/invoices', headers=headers, json={
            'customer_id': cust['id'],
            'items': [{'product_id': prod['id'], 'quantity': 1}],
        })
        inv_id = r.get_json()['invoice']['id']
        resp = client.put(f'/api/sales/invoices/{inv_id}/status', headers=headers,
                           json={'status': 'sent'})
        assert resp.status_code == 200
        assert resp.get_json()['invoice']['status'] == 'sent'

    # ── Payments ─────────────────────────────────────────────

    def test_record_payment_partial_and_full(self, client, auth_headers):
        """Record partial payment → status=partial; full payment → status=paid."""
        headers, _ = auth_headers
        cust, prod, wh = self._setup(client, headers)
        r = client.post('/api/sales/invoices', headers=headers, json={
            'customer_id': cust['id'],
            'items': [{'product_id': prod['id'], 'quantity': 2, 'unit_price': 100}],
        })
        inv = r.get_json()['invoice']
        inv_id = inv['id']
        total = inv['total']  # 220.0 = 2*100 + 10% tax

        # Partial payment
        resp = client.post(f'/api/sales/invoices/{inv_id}/payments', headers=headers,
                            json={'amount': 100, 'payment_method': 'bank_transfer'})
        assert resp.status_code == 201
        assert resp.get_json()['invoice']['status'] == 'partial'
        assert resp.get_json()['invoice']['amount_paid'] == 100

        # Full remainder
        remaining = total - 100
        resp = client.post(f'/api/sales/invoices/{inv_id}/payments', headers=headers,
                            json={'amount': remaining, 'payment_method': 'cash'})
        assert resp.status_code == 201
        assert resp.get_json()['invoice']['status'] == 'paid'
        assert resp.get_json()['invoice']['balance_due'] == 0

    def test_overpayment_rejected(self, client, auth_headers):
        headers, _ = auth_headers
        cust, prod, wh = self._setup(client, headers)
        r = client.post('/api/sales/invoices', headers=headers, json={
            'customer_id': cust['id'],
            'items': [{'product_id': prod['id'], 'quantity': 1, 'unit_price': 100}],
        })
        inv_id = r.get_json()['invoice']['id']
        resp = client.post(f'/api/sales/invoices/{inv_id}/payments', headers=headers,
                            json={'amount': 99999})
        assert resp.status_code == 400
        assert 'exceeds' in resp.get_json()['error']

    def test_list_payments(self, client, auth_headers):
        headers, _ = auth_headers
        cust, prod, wh = self._setup(client, headers)
        r = client.post('/api/sales/invoices', headers=headers, json={
            'customer_id': cust['id'],
            'items': [{'product_id': prod['id'], 'quantity': 1, 'unit_price': 100}],
        })
        inv_id = r.get_json()['invoice']['id']
        client.post(f'/api/sales/invoices/{inv_id}/payments', headers=headers,
                     json={'amount': 50})
        resp = client.get(f'/api/sales/invoices/{inv_id}/payments', headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['total'] == 1

    def test_sales_stats(self, client, auth_headers):
        headers, _ = auth_headers
        cust, prod, wh = self._setup(client, headers)
        resp = client.get('/api/sales/stats', headers=headers)
        assert resp.status_code == 200
        stats = resp.get_json()['stats']
        assert 'total_customers' in stats
        assert 'total_revenue' in stats


# ════════════════════════════════════════════════════════════
#  4.  PURCHASING MODULE
# ════════════════════════════════════════════════════════════

class TestPurchasing:

    def _setup(self, client, headers):
        """Install modules and create supplier + product + warehouse."""
        _seed_and_install(client, headers)
        sup = client.post('/api/purchasing/suppliers', headers=headers, json={
            'name': 'SupplierOne', 'email': 'sup@one.com',
        }).get_json()['supplier']
        prod = client.post('/api/inventory/products', headers=headers, json={
            'name': 'Raw Material', 'sku': 'RM-001',
            'cost_price': 25, 'sale_price': 50, 'tax_rate': 5,
            'product_type': 'goods',
        }).get_json()['product']
        wh = client.post('/api/inventory/warehouses', headers=headers, json={
            'name': 'Purchase WH', 'code': 'PWH',
        }).get_json()['warehouse']
        return sup, prod, wh

    # ── Suppliers ────────────────────────────────────────────

    def test_supplier_crud(self, client, auth_headers):
        headers, _ = auth_headers
        _seed_and_install(client, headers)
        resp = client.post('/api/purchasing/suppliers', headers=headers, json={
            'name': 'SupA', 'payment_terms': 'Net 30',
        })
        assert resp.status_code == 201
        sid = resp.get_json()['supplier']['id']
        resp = client.get(f'/api/purchasing/suppliers/{sid}', headers=headers)
        assert resp.status_code == 200
        resp = client.put(f'/api/purchasing/suppliers/{sid}', headers=headers,
                           json={'name': 'SupA Updated'})
        assert resp.status_code == 200
        assert resp.get_json()['supplier']['name'] == 'SupA Updated'
        resp = client.get('/api/purchasing/suppliers', headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['total'] >= 1

    # ── Purchase Orders ──────────────────────────────────────

    def test_create_purchase_order(self, client, auth_headers):
        headers, _ = auth_headers
        sup, prod, wh = self._setup(client, headers)
        resp = client.post('/api/purchasing/orders', headers=headers, json={
            'supplier_id': sup['id'],
            'warehouse_id': wh['id'],
            'items': [{'product_id': prod['id'], 'quantity': 20, 'unit_price': 25}],
        })
        assert resp.status_code == 201
        po = resp.get_json()['order']
        assert po['number'].startswith('PO-')
        assert po['status'] == 'draft'
        assert len(po['items']) == 1
        assert po['subtotal'] == 500.0  # 20*25
        assert po['tax_amount'] == 25.0  # 5%
        assert po['total'] == 525.0

    def test_list_purchase_orders(self, client, auth_headers):
        headers, _ = auth_headers
        sup, prod, wh = self._setup(client, headers)
        client.post('/api/purchasing/orders', headers=headers, json={
            'supplier_id': sup['id'], 'warehouse_id': wh['id'],
            'items': [{'product_id': prod['id'], 'quantity': 5}],
        })
        resp = client.get('/api/purchasing/orders', headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['total'] == 1

    # ── Goods receipt → stock update ─────────────────────────

    def test_receive_goods(self, client, auth_headers):
        """Receiving goods should increase inventory stock."""
        headers, _ = auth_headers
        sup, prod, wh = self._setup(client, headers)
        # Create PO
        po_r = client.post('/api/purchasing/orders', headers=headers, json={
            'supplier_id': sup['id'],
            'warehouse_id': wh['id'],
            'items': [{'product_id': prod['id'], 'quantity': 50, 'unit_price': 25}],
        })
        po = po_r.get_json()['order']
        item_id = po['items'][0]['id']

        # Partial receive (20 of 50)
        resp = client.post(f"/api/purchasing/orders/{po['id']}/receive", headers=headers,
                            json={'items': [{'item_id': item_id, 'quantity': 20}]})
        assert resp.status_code == 200
        assert resp.get_json()['order']['status'] == 'partial'

        # Stock should be 20
        stock = client.get(f"/api/inventory/stock?product_id={prod['id']}&warehouse_id={wh['id']}",
                            headers=headers)
        entries = stock.get_json()['stock']
        assert entries[0]['quantity'] == 20

        # Receive remaining 30
        resp = client.post(f"/api/purchasing/orders/{po['id']}/receive", headers=headers,
                            json={'items': [{'item_id': item_id, 'quantity': 30}]})
        assert resp.status_code == 200
        assert resp.get_json()['order']['status'] == 'received'

        # Stock should be 50
        stock = client.get(f"/api/inventory/stock?product_id={prod['id']}&warehouse_id={wh['id']}",
                            headers=headers)
        entries = stock.get_json()['stock']
        assert entries[0]['quantity'] == 50

    def test_over_receive_rejected(self, client, auth_headers):
        headers, _ = auth_headers
        sup, prod, wh = self._setup(client, headers)
        po_r = client.post('/api/purchasing/orders', headers=headers, json={
            'supplier_id': sup['id'], 'warehouse_id': wh['id'],
            'items': [{'product_id': prod['id'], 'quantity': 10}],
        })
        po = po_r.get_json()['order']
        item_id = po['items'][0]['id']
        resp = client.post(f"/api/purchasing/orders/{po['id']}/receive", headers=headers,
                            json={'items': [{'item_id': item_id, 'quantity': 999}]})
        assert resp.status_code == 400
        assert 'remaining' in resp.get_json()['error']

    def test_purchasing_stats(self, client, auth_headers):
        headers, _ = auth_headers
        _seed_and_install(client, headers)
        resp = client.get('/api/purchasing/stats', headers=headers)
        assert resp.status_code == 200
        stats = resp.get_json()['stats']
        assert 'total_suppliers' in stats
        assert 'total_orders' in stats


# ════════════════════════════════════════════════════════════
#  5.  CROSS-MODULE INTEGRATION
# ════════════════════════════════════════════════════════════

class TestIntegration:

    def test_full_sales_cycle(self, client, auth_headers):
        """End-to-end: product → quotation → invoice → payment → stock check."""
        headers, _ = auth_headers
        _seed_and_install(client, headers)

        # Create customer
        cust = client.post('/api/sales/customers', headers=headers,
                            json={'name': 'E2E Customer'}).get_json()['customer']
        # Create product + warehouse + initial stock
        prod = client.post('/api/inventory/products', headers=headers, json={
            'name': 'E2E Widget', 'sku': 'E2E-1',
            'sale_price': 200, 'cost_price': 80, 'tax_rate': 15,
            'product_type': 'goods',
        }).get_json()['product']
        wh = client.post('/api/inventory/warehouses', headers=headers,
                          json={'name': 'E2E WH', 'code': 'E2EWH'}).get_json()['warehouse']
        client.post('/api/inventory/stock/adjust', headers=headers, json={
            'product_id': prod['id'], 'warehouse_id': wh['id'], 'quantity': 200,
        })

        # Create quotation (5 units @ $200)
        qr = client.post('/api/sales/quotations', headers=headers, json={
            'customer_id': cust['id'],
            'items': [{'product_id': prod['id'], 'quantity': 5, 'unit_price': 200}],
        })
        assert qr.status_code == 201
        quote = qr.get_json()['quotation']
        assert quote['total'] == 1150.0  # 5*200 + 15% tax

        # Convert quotation → invoice (auto-deducts stock)
        ir = client.post(f"/api/sales/quotations/{quote['id']}/convert", headers=headers,
                          json={'warehouse_id': wh['id']})
        assert ir.status_code == 201
        invoice = ir.get_json()['invoice']
        assert invoice['total'] == 1150.0
        assert invoice['balance_due'] == 1150.0

        # Stock should be 195 (200 - 5)
        stock = client.get(f"/api/inventory/stock?product_id={prod['id']}&warehouse_id={wh['id']}",
                            headers=headers)
        assert stock.get_json()['stock'][0]['quantity'] == 195

        # Partial payment
        pr1 = client.post(f"/api/sales/invoices/{invoice['id']}/payments", headers=headers,
                           json={'amount': 500, 'payment_method': 'bank_transfer'})
        assert pr1.status_code == 201
        assert pr1.get_json()['invoice']['status'] == 'partial'

        # Full payment
        pr2 = client.post(f"/api/sales/invoices/{invoice['id']}/payments", headers=headers,
                           json={'amount': 650, 'payment_method': 'credit_card'})
        assert pr2.status_code == 201
        assert pr2.get_json()['invoice']['status'] == 'paid'
        assert pr2.get_json()['invoice']['balance_due'] == 0

    def test_full_purchasing_cycle(self, client, auth_headers):
        """End-to-end: supplier → PO → goods receipt → stock increase."""
        headers, _ = auth_headers
        _seed_and_install(client, headers)

        sup = client.post('/api/purchasing/suppliers', headers=headers,
                           json={'name': 'E2E Supplier'}).get_json()['supplier']
        prod = client.post('/api/inventory/products', headers=headers, json={
            'name': 'E2E Material', 'sku': 'E2E-M1',
            'cost_price': 30, 'tax_rate': 8, 'product_type': 'goods',
        }).get_json()['product']
        wh = client.post('/api/inventory/warehouses', headers=headers,
                          json={'name': 'E2E PWH', 'code': 'E2EPWH'}).get_json()['warehouse']

        # Create PO (100 units @ $30)
        po_r = client.post('/api/purchasing/orders', headers=headers, json={
            'supplier_id': sup['id'], 'warehouse_id': wh['id'],
            'items': [{'product_id': prod['id'], 'quantity': 100, 'unit_price': 30}],
        })
        assert po_r.status_code == 201
        po = po_r.get_json()['order']
        assert po['total'] == 3240.0  # 100*30 + 8% tax
        item_id = po['items'][0]['id']

        # Receive all 100
        rr = client.post(f"/api/purchasing/orders/{po['id']}/receive", headers=headers,
                          json={'items': [{'item_id': item_id, 'quantity': 100}]})
        assert rr.status_code == 200
        assert rr.get_json()['order']['status'] == 'received'

        # Stock should be 100
        stock = client.get(f"/api/inventory/stock?product_id={prod['id']}&warehouse_id={wh['id']}",
                            headers=headers)
        assert stock.get_json()['stock'][0]['quantity'] == 100

        # Verify stock movements were recorded
        mvs = client.get('/api/inventory/stock/movements', headers=headers)
        assert mvs.get_json()['total'] >= 1
