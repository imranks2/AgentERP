"""Phase 8 – Enterprise Core ERP Modules tests.

Covers: Accounting (accounts, journal entries, reports),
        CRM (leads, opportunities, activities, pipeline),
        HR (employees, leave, payroll, attendance).
"""
import pytest
from datetime import date


# ═══════════════════════════════════════════════════════════
#  ACCOUNTING
# ═══════════════════════════════════════════════════════════

class TestAccounting:

    def test_create_account(self, client, auth_headers):
        h, _ = auth_headers
        resp = client.post('/api/accounting/accounts', headers=h, json={
            'code': '1000', 'name': 'Cash', 'account_type': 'asset',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['code'] == '1000'
        assert data['account_type'] == 'asset'

    def test_list_accounts(self, client, auth_headers):
        h, _ = auth_headers
        client.post('/api/accounting/accounts', headers=h, json={
            'code': '1000', 'name': 'Cash', 'account_type': 'asset',
        })
        client.post('/api/accounting/accounts', headers=h, json={
            'code': '4000', 'name': 'Sales Revenue', 'account_type': 'revenue',
        })
        resp = client.get('/api/accounting/accounts', headers=h)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total'] == 2
        assert len(data['accounts']) == 2

    def test_create_account_validation(self, client, auth_headers):
        h, _ = auth_headers
        resp = client.post('/api/accounting/accounts', headers=h, json={
            'code': '', 'name': 'Bad', 'account_type': 'asset',
        })
        assert resp.status_code == 400

    def test_duplicate_account_code(self, client, auth_headers):
        h, _ = auth_headers
        client.post('/api/accounting/accounts', headers=h, json={
            'code': '1000', 'name': 'Cash', 'account_type': 'asset',
        })
        resp = client.post('/api/accounting/accounts', headers=h, json={
            'code': '1000', 'name': 'Cash 2', 'account_type': 'asset',
        })
        assert resp.status_code == 400

    def test_update_account(self, client, auth_headers):
        h, _ = auth_headers
        r1 = client.post('/api/accounting/accounts', headers=h, json={
            'code': '1000', 'name': 'Cash', 'account_type': 'asset',
        })
        acct_id = r1.get_json()['id']
        resp = client.put(f'/api/accounting/accounts/{acct_id}', headers=h,
                          json={'name': 'Cash & Equivalents'})
        assert resp.status_code == 200
        assert resp.get_json()['name'] == 'Cash & Equivalents'

    def test_delete_account(self, client, auth_headers):
        h, _ = auth_headers
        r1 = client.post('/api/accounting/accounts', headers=h, json={
            'code': '1000', 'name': 'Cash', 'account_type': 'asset',
        })
        acct_id = r1.get_json()['id']
        resp = client.delete(f'/api/accounting/accounts/{acct_id}', headers=h)
        assert resp.status_code == 200


class TestJournalEntries:

    def _make_accounts(self, client, headers):
        r1 = client.post('/api/accounting/accounts', headers=headers, json={
            'code': '1000', 'name': 'Cash', 'account_type': 'asset',
        })
        r2 = client.post('/api/accounting/accounts', headers=headers, json={
            'code': '4000', 'name': 'Revenue', 'account_type': 'revenue',
        })
        return r1.get_json()['id'], r2.get_json()['id']

    def test_create_journal_entry(self, client, auth_headers):
        h, _ = auth_headers
        cash_id, rev_id = self._make_accounts(client, h)
        resp = client.post('/api/accounting/journal-entries', headers=h, json={
            'description': 'Record sale',
            'lines': [
                {'account_id': cash_id, 'debit': 100, 'credit': 0},
                {'account_id': rev_id, 'debit': 0, 'credit': 100},
            ],
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['total_debit'] == 100
        assert data['total_credit'] == 100
        assert data['status'] == 'draft'

    def test_journal_entry_balance_check(self, client, auth_headers):
        h, _ = auth_headers
        cash_id, rev_id = self._make_accounts(client, h)
        resp = client.post('/api/accounting/journal-entries', headers=h, json={
            'lines': [
                {'account_id': cash_id, 'debit': 100, 'credit': 0},
                {'account_id': rev_id, 'debit': 0, 'credit': 50},
            ],
        })
        assert resp.status_code == 400
        assert 'equal' in resp.get_json()['error'].lower()

    def test_post_and_reverse_journal_entry(self, client, auth_headers):
        h, _ = auth_headers
        cash_id, rev_id = self._make_accounts(client, h)
        r = client.post('/api/accounting/journal-entries', headers=h, json={
            'description': 'Test', 'lines': [
                {'account_id': cash_id, 'debit': 50, 'credit': 0},
                {'account_id': rev_id, 'debit': 0, 'credit': 50},
            ],
        })
        je_id = r.get_json()['id']
        # Post
        resp = client.post(f'/api/accounting/journal-entries/{je_id}/post', headers=h)
        assert resp.status_code == 200
        assert resp.get_json()['status'] == 'posted'
        # Reverse
        resp = client.post(f'/api/accounting/journal-entries/{je_id}/reverse', headers=h)
        assert resp.status_code == 200
        assert resp.get_json()['status'] == 'posted'  # reversal is auto-posted

    def test_list_journal_entries(self, client, auth_headers):
        h, _ = auth_headers
        cash_id, rev_id = self._make_accounts(client, h)
        client.post('/api/accounting/journal-entries', headers=h, json={
            'lines': [
                {'account_id': cash_id, 'debit': 10, 'credit': 0},
                {'account_id': rev_id, 'debit': 0, 'credit': 10},
            ],
        })
        resp = client.get('/api/accounting/journal-entries', headers=h)
        assert resp.status_code == 200
        assert resp.get_json()['total'] >= 1


class TestAccountingReports:

    def _seed(self, client, headers):
        r1 = client.post('/api/accounting/accounts', headers=headers, json={
            'code': '1000', 'name': 'Cash', 'account_type': 'asset'})
        r2 = client.post('/api/accounting/accounts', headers=headers, json={
            'code': '4000', 'name': 'Revenue', 'account_type': 'revenue'})
        cash_id, rev_id = r1.get_json()['id'], r2.get_json()['id']
        r = client.post('/api/accounting/journal-entries', headers=headers, json={
            'lines': [
                {'account_id': cash_id, 'debit': 200, 'credit': 0},
                {'account_id': rev_id, 'debit': 0, 'credit': 200},
            ],
        })
        je_id = r.get_json()['id']
        client.post(f'/api/accounting/journal-entries/{je_id}/post', headers=headers)
        return cash_id, rev_id

    def test_trial_balance(self, client, auth_headers):
        h, _ = auth_headers
        self._seed(client, h)
        resp = client.get('/api/accounting/reports/trial-balance', headers=h)
        assert resp.status_code == 200
        tb = resp.get_json()['trial_balance']
        assert any(r['code'] == '1000' and r['total_debit'] == 200 for r in tb)

    def test_profit_and_loss(self, client, auth_headers):
        h, _ = auth_headers
        self._seed(client, h)
        resp = client.get('/api/accounting/reports/profit-loss', headers=h)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['revenue'] == 200

    def test_balance_sheet(self, client, auth_headers):
        h, _ = auth_headers
        self._seed(client, h)
        resp = client.get('/api/accounting/reports/balance-sheet', headers=h)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['assets'] == 200

    def test_accounting_stats(self, client, auth_headers):
        h, _ = auth_headers
        self._seed(client, h)
        resp = client.get('/api/accounting/stats', headers=h)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total_accounts'] == 2
        assert data['posted_entries'] >= 1


class TestTaxRatesAndCurrencies:

    def test_create_tax_rate(self, client, auth_headers):
        h, _ = auth_headers
        resp = client.post('/api/accounting/tax-rates', headers=h, json={
            'name': 'VAT 15%', 'code': 'VAT15', 'rate': 0.15,
        })
        assert resp.status_code == 201
        assert resp.get_json()['rate'] == 0.15

    def test_list_tax_rates(self, client, auth_headers):
        h, _ = auth_headers
        client.post('/api/accounting/tax-rates', headers=h, json={
            'name': 'VAT 15%', 'code': 'VAT15', 'rate': 0.15,
        })
        resp = client.get('/api/accounting/tax-rates', headers=h)
        assert resp.status_code == 200
        assert len(resp.get_json()['tax_rates']) >= 1

    def test_create_currency(self, client, auth_headers):
        h, _ = auth_headers
        resp = client.post('/api/accounting/currencies', headers=h, json={
            'code': 'EUR', 'name': 'Euro', 'symbol': '€', 'exchange_rate': 0.92,
        })
        assert resp.status_code == 201
        assert resp.get_json()['code'] == 'EUR'

    def test_list_currencies(self, client, auth_headers):
        h, _ = auth_headers
        client.post('/api/accounting/currencies', headers=h, json={
            'code': 'EUR', 'name': 'Euro', 'symbol': '€',
        })
        resp = client.get('/api/accounting/currencies', headers=h)
        assert resp.status_code == 200
        assert len(resp.get_json()['currencies']) >= 1


# ═══════════════════════════════════════════════════════════
#  CRM
# ═══════════════════════════════════════════════════════════

class TestCRMLeads:

    def test_create_lead(self, client, auth_headers):
        h, _ = auth_headers
        resp = client.post('/api/crm/leads', headers=h, json={
            'name': 'John Doe', 'email': 'john@example.com',
            'company': 'ACME', 'source': 'web',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['name'] == 'John Doe'
        assert data['status'] == 'new'

    def test_list_leads(self, client, auth_headers):
        h, _ = auth_headers
        client.post('/api/crm/leads', headers=h, json={'name': 'Lead1'})
        client.post('/api/crm/leads', headers=h, json={'name': 'Lead2'})
        resp = client.get('/api/crm/leads', headers=h)
        assert resp.status_code == 200
        assert resp.get_json()['total'] == 2

    def test_update_lead(self, client, auth_headers):
        h, _ = auth_headers
        r = client.post('/api/crm/leads', headers=h, json={'name': 'Lead1'})
        lid = r.get_json()['id']
        resp = client.put(f'/api/crm/leads/{lid}', headers=h,
                          json={'status': 'contacted', 'score': 50})
        assert resp.status_code == 200
        assert resp.get_json()['status'] == 'contacted'
        assert resp.get_json()['score'] == 50

    def test_delete_lead(self, client, auth_headers):
        h, _ = auth_headers
        r = client.post('/api/crm/leads', headers=h, json={'name': 'Del'})
        lid = r.get_json()['id']
        resp = client.delete(f'/api/crm/leads/{lid}', headers=h)
        assert resp.status_code == 200

    def test_create_lead_validation(self, client, auth_headers):
        h, _ = auth_headers
        resp = client.post('/api/crm/leads', headers=h, json={'name': ''})
        assert resp.status_code == 400


class TestCRMOpportunities:

    def test_create_opportunity(self, client, auth_headers):
        h, _ = auth_headers
        resp = client.post('/api/crm/opportunities', headers=h, json={
            'title': 'Big Deal', 'value': 50000, 'stage': 'proposal',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['value'] == 50000
        assert data['stage'] == 'proposal'

    def test_list_opportunities(self, client, auth_headers):
        h, _ = auth_headers
        client.post('/api/crm/opportunities', headers=h, json={'title': 'Deal1'})
        resp = client.get('/api/crm/opportunities', headers=h)
        assert resp.status_code == 200
        assert resp.get_json()['total'] >= 1

    def test_update_opportunity_stage(self, client, auth_headers):
        h, _ = auth_headers
        r = client.post('/api/crm/opportunities', headers=h, json={'title': 'D'})
        oid = r.get_json()['id']
        resp = client.put(f'/api/crm/opportunities/{oid}', headers=h,
                          json={'stage': 'won', 'probability': 100})
        assert resp.status_code == 200
        assert resp.get_json()['stage'] == 'won'

    def test_pipeline_stats(self, client, auth_headers):
        h, _ = auth_headers
        client.post('/api/crm/opportunities', headers=h, json={
            'title': 'A', 'value': 100, 'stage': 'prospecting',
        })
        client.post('/api/crm/opportunities', headers=h, json={
            'title': 'B', 'value': 200, 'stage': 'won',
        })
        resp = client.get('/api/crm/pipeline', headers=h)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total_pipeline_value'] == 300


class TestCRMActivities:

    def test_create_activity(self, client, auth_headers):
        h, _ = auth_headers
        resp = client.post('/api/crm/activities', headers=h, json={
            'activity_type': 'call', 'subject': 'Follow-up call',
        })
        assert resp.status_code == 201
        assert resp.get_json()['activity_type'] == 'call'

    def test_list_activities(self, client, auth_headers):
        h, _ = auth_headers
        client.post('/api/crm/activities', headers=h, json={
            'activity_type': 'email', 'subject': 'Pitch',
        })
        resp = client.get('/api/crm/activities', headers=h)
        assert resp.status_code == 200
        assert resp.get_json()['total'] >= 1


# ═══════════════════════════════════════════════════════════
#  HR
# ═══════════════════════════════════════════════════════════

class TestHREmployees:

    def test_create_employee(self, client, auth_headers):
        h, _ = auth_headers
        resp = client.post('/api/hr/employees', headers=h, json={
            'first_name': 'Jane', 'last_name': 'Smith',
            'hire_date': '2024-01-15', 'job_title': 'Engineer',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['first_name'] == 'Jane'
        assert data['employee_number'].startswith('EMP-')
        assert data['status'] == 'active'

    def test_list_employees(self, client, auth_headers):
        h, _ = auth_headers
        client.post('/api/hr/employees', headers=h, json={
            'first_name': 'A', 'last_name': 'B', 'hire_date': '2024-01-01',
        })
        resp = client.get('/api/hr/employees', headers=h)
        assert resp.status_code == 200
        assert resp.get_json()['total'] >= 1

    def test_update_employee(self, client, auth_headers):
        h, _ = auth_headers
        r = client.post('/api/hr/employees', headers=h, json={
            'first_name': 'A', 'last_name': 'B', 'hire_date': '2024-01-01',
        })
        eid = r.get_json()['id']
        resp = client.put(f'/api/hr/employees/{eid}', headers=h,
                          json={'job_title': 'Senior Engineer', 'salary': 120000})
        assert resp.status_code == 200
        assert resp.get_json()['job_title'] == 'Senior Engineer'
        assert resp.get_json()['salary'] == 120000

    def test_terminate_employee(self, client, auth_headers):
        h, _ = auth_headers
        r = client.post('/api/hr/employees', headers=h, json={
            'first_name': 'X', 'last_name': 'Y', 'hire_date': '2024-01-01',
        })
        eid = r.get_json()['id']
        resp = client.post(f'/api/hr/employees/{eid}/terminate', headers=h,
                           json={'termination_date': '2024-12-31'})
        assert resp.status_code == 200
        assert resp.get_json()['status'] == 'terminated'

    def test_create_employee_validation(self, client, auth_headers):
        h, _ = auth_headers
        resp = client.post('/api/hr/employees', headers=h, json={
            'first_name': '', 'last_name': 'B', 'hire_date': '2024-01-01',
        })
        assert resp.status_code == 400


class TestHRLeave:

    def _make_emp(self, client, headers):
        r = client.post('/api/hr/employees', headers=headers, json={
            'first_name': 'A', 'last_name': 'B', 'hire_date': '2024-01-01',
        })
        return r.get_json()['id']

    def _make_leave_type(self, client, headers):
        r = client.post('/api/hr/leave-types', headers=headers, json={
            'name': 'Annual Leave', 'code': 'AL', 'default_days': 20,
        })
        return r.get_json()['id']

    def test_create_leave_type(self, client, auth_headers):
        h, _ = auth_headers
        resp = client.post('/api/hr/leave-types', headers=h, json={
            'name': 'Sick Leave', 'code': 'SL', 'default_days': 10,
        })
        assert resp.status_code == 201
        assert resp.get_json()['code'] == 'SL'

    def test_list_leave_types(self, client, auth_headers):
        h, _ = auth_headers
        client.post('/api/hr/leave-types', headers=h, json={
            'name': 'Annual', 'code': 'AL', 'default_days': 20,
        })
        resp = client.get('/api/hr/leave-types', headers=h)
        assert resp.status_code == 200
        assert len(resp.get_json()['leave_types']) >= 1

    def test_create_and_approve_leave(self, client, auth_headers):
        h, _ = auth_headers
        emp_id = self._make_emp(client, h)
        lt_id = self._make_leave_type(client, h)
        r = client.post('/api/hr/leave-requests', headers=h, json={
            'employee_id': emp_id, 'leave_type_id': lt_id,
            'start_date': '2024-07-01', 'end_date': '2024-07-05', 'days': 5,
        })
        assert r.status_code == 201
        lr_id = r.get_json()['id']
        resp = client.post(f'/api/hr/leave-requests/{lr_id}/approve', headers=h)
        assert resp.status_code == 200
        assert resp.get_json()['status'] == 'approved'

    def test_reject_leave(self, client, auth_headers):
        h, _ = auth_headers
        emp_id = self._make_emp(client, h)
        lt_id = self._make_leave_type(client, h)
        r = client.post('/api/hr/leave-requests', headers=h, json={
            'employee_id': emp_id, 'leave_type_id': lt_id,
            'start_date': '2024-08-01', 'end_date': '2024-08-03', 'days': 3,
        })
        lr_id = r.get_json()['id']
        resp = client.post(f'/api/hr/leave-requests/{lr_id}/reject', headers=h)
        assert resp.status_code == 200
        assert resp.get_json()['status'] == 'rejected'


class TestHRPayroll:

    def test_create_payroll_run(self, client, auth_headers):
        h, _ = auth_headers
        # Create an employee first
        client.post('/api/hr/employees', headers=h, json={
            'first_name': 'A', 'last_name': 'B',
            'hire_date': '2024-01-01', 'salary': 60000,
        })
        resp = client.post('/api/hr/payroll-runs', headers=h, json={
            'period_start': '2024-01-01', 'period_end': '2024-01-31',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['status'] == 'draft'
        assert data['total_gross'] > 0

    def test_process_payroll(self, client, auth_headers):
        h, _ = auth_headers
        client.post('/api/hr/employees', headers=h, json={
            'first_name': 'X', 'last_name': 'Y',
            'hire_date': '2024-01-01', 'salary': 48000,
        })
        r = client.post('/api/hr/payroll-runs', headers=h, json={
            'period_start': '2024-02-01', 'period_end': '2024-02-29',
        })
        run_id = r.get_json()['id']
        resp = client.post(f'/api/hr/payroll-runs/{run_id}/process', headers=h)
        assert resp.status_code == 200
        assert resp.get_json()['status'] == 'completed'

    def test_get_payroll_with_slips(self, client, auth_headers):
        h, _ = auth_headers
        client.post('/api/hr/employees', headers=h, json={
            'first_name': 'P', 'last_name': 'Q',
            'hire_date': '2024-01-01', 'salary': 72000,
        })
        r = client.post('/api/hr/payroll-runs', headers=h, json={
            'period_start': '2024-03-01', 'period_end': '2024-03-31',
        })
        run_id = r.get_json()['id']
        resp = client.get(f'/api/hr/payroll-runs/{run_id}', headers=h)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'pay_slips' in data
        assert len(data['pay_slips']) >= 1


class TestHRAttendance:

    def test_record_attendance(self, client, auth_headers):
        h, _ = auth_headers
        r = client.post('/api/hr/employees', headers=h, json={
            'first_name': 'A', 'last_name': 'B', 'hire_date': '2024-01-01',
        })
        eid = r.get_json()['id']
        resp = client.post('/api/hr/attendance', headers=h, json={
            'employee_id': eid, 'date': '2024-06-01', 'status': 'present',
        })
        assert resp.status_code == 201
        assert resp.get_json()['status'] == 'present'

    def test_list_attendance(self, client, auth_headers):
        h, _ = auth_headers
        r = client.post('/api/hr/employees', headers=h, json={
            'first_name': 'C', 'last_name': 'D', 'hire_date': '2024-01-01',
        })
        eid = r.get_json()['id']
        client.post('/api/hr/attendance', headers=h, json={
            'employee_id': eid, 'date': '2024-06-01',
        })
        resp = client.get('/api/hr/attendance', headers=h)
        assert resp.status_code == 200
        assert resp.get_json()['total'] >= 1


class TestHRStats:

    def test_hr_stats(self, client, auth_headers):
        h, _ = auth_headers
        client.post('/api/hr/employees', headers=h, json={
            'first_name': 'S', 'last_name': 'T', 'hire_date': '2024-01-01',
        })
        resp = client.get('/api/hr/stats', headers=h)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total_employees'] >= 1
        assert data['active_employees'] >= 1
