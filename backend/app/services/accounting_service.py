"""Accounting service – Chart of Accounts, Journal Entries, Fiscal Years,
Tax Rates, Currencies, and financial reports (Trial Balance, P&L, Balance Sheet).
"""
from datetime import datetime, timezone, date
from sqlalchemy import func, case
from app import db
from app.models.accounting import (
    Account, FiscalYear, FiscalPeriod,
    JournalEntry, JournalLine, TaxRate, CurrencyRate,
)


class AccountingService:

    # ── Chart of Accounts ────────────────────────────────────

    @staticmethod
    def list_accounts(tenant_id, account_type=None, parent_id=None, search=None,
                      active_only=True, page=1, per_page=50):
        q = Account.query.filter_by(tenant_id=tenant_id)
        if active_only:
            q = q.filter_by(is_active=True)
        if account_type:
            q = q.filter_by(account_type=account_type)
        if parent_id == 'root':
            q = q.filter(Account.parent_id.is_(None))
        elif parent_id:
            q = q.filter_by(parent_id=parent_id)
        if search:
            like = f'%{search}%'
            q = q.filter(db.or_(Account.name.ilike(like), Account.code.ilike(like)))
        total = q.count()
        accounts = q.order_by(Account.code).offset((page - 1) * per_page).limit(per_page).all()
        return accounts, total

    @staticmethod
    def get_account(tenant_id, account_id):
        return Account.query.filter_by(id=account_id, tenant_id=tenant_id).first()

    @staticmethod
    def create_account(tenant_id, data):
        code = data.get('code', '').strip()
        name = data.get('name', '').strip()
        atype = data.get('account_type', '').strip()
        if not code or not name or not atype:
            raise ValueError('code, name, and account_type are required')
        if atype not in ('asset', 'liability', 'equity', 'revenue', 'expense'):
            raise ValueError('Invalid account_type')
        existing = Account.query.filter_by(tenant_id=tenant_id, code=code).first()
        if existing:
            raise ValueError(f"Account code '{code}' already exists")
        acct = Account(
            tenant_id=tenant_id, code=code, name=name, account_type=atype,
            parent_id=data.get('parent_id'), currency=data.get('currency', 'USD'),
            description=data.get('description'),
        )
        db.session.add(acct)
        db.session.commit()
        return acct

    @staticmethod
    def update_account(tenant_id, account_id, data):
        acct = Account.query.filter_by(id=account_id, tenant_id=tenant_id).first()
        if not acct:
            return None
        for f in ['name', 'code', 'account_type', 'parent_id', 'currency',
                   'is_active', 'description']:
            if f in data:
                setattr(acct, f, data[f])
        db.session.commit()
        return acct

    @staticmethod
    def delete_account(tenant_id, account_id):
        acct = Account.query.filter_by(id=account_id, tenant_id=tenant_id).first()
        if not acct:
            raise ValueError('Account not found')
        if acct.journal_lines.count() > 0:
            raise ValueError('Cannot delete account with existing journal lines')
        db.session.delete(acct)
        db.session.commit()

    # ── Fiscal Years / Periods ───────────────────────────────

    @staticmethod
    def list_fiscal_years(tenant_id):
        return FiscalYear.query.filter_by(tenant_id=tenant_id)\
            .order_by(FiscalYear.start_date.desc()).all()

    @staticmethod
    def create_fiscal_year(tenant_id, data):
        fy = FiscalYear(
            tenant_id=tenant_id, name=data['name'],
            start_date=data['start_date'], end_date=data['end_date'],
        )
        db.session.add(fy)
        db.session.commit()
        return fy

    @staticmethod
    def get_fiscal_year(tenant_id, fy_id):
        return FiscalYear.query.filter_by(id=fy_id, tenant_id=tenant_id).first()

    @staticmethod
    def close_fiscal_year(tenant_id, fy_id):
        fy = FiscalYear.query.filter_by(id=fy_id, tenant_id=tenant_id).first()
        if not fy:
            raise ValueError('Fiscal year not found')
        fy.is_closed = True
        for p in fy.periods.all():
            p.is_closed = True
        db.session.commit()
        return fy

    # ── Journal Entries ──────────────────────────────────────

    @staticmethod
    def list_journal_entries(tenant_id, status=None, reference_type=None,
                             page=1, per_page=50):
        q = JournalEntry.query.filter_by(tenant_id=tenant_id)
        if status:
            q = q.filter_by(status=status)
        if reference_type:
            q = q.filter_by(reference_type=reference_type)
        total = q.count()
        entries = q.order_by(JournalEntry.date.desc(), JournalEntry.number.desc())\
            .offset((page - 1) * per_page).limit(per_page).all()
        return entries, total

    @staticmethod
    def get_journal_entry(tenant_id, entry_id):
        return JournalEntry.query.filter_by(id=entry_id, tenant_id=tenant_id).first()

    @staticmethod
    def _next_journal_number(tenant_id):
        last = JournalEntry.query.filter_by(tenant_id=tenant_id)\
            .order_by(JournalEntry.created_at.desc()).first()
        if last:
            try:
                seq = int(last.number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f'JE-{seq:06d}'

    @staticmethod
    def create_journal_entry(tenant_id, data, user_id=None):
        lines_data = data.get('lines', [])
        if len(lines_data) < 2:
            raise ValueError('At least two lines are required')
        total_debit = sum(l.get('debit', 0) for l in lines_data)
        total_credit = sum(l.get('credit', 0) for l in lines_data)
        if round(total_debit, 2) != round(total_credit, 2):
            raise ValueError('Total debits must equal total credits')
        number = data.get('number') or AccountingService._next_journal_number(tenant_id)
        je = JournalEntry(
            tenant_id=tenant_id, number=number,
            date=data.get('date', date.today()),
            reference_type=data.get('reference_type'),
            reference_id=data.get('reference_id'),
            description=data.get('description'),
            total_debit=round(total_debit, 2),
            total_credit=round(total_credit, 2),
            created_by=user_id,
        )
        db.session.add(je)
        db.session.flush()
        for ld in lines_data:
            line = JournalLine(
                journal_entry_id=je.id, account_id=ld['account_id'],
                debit=round(ld.get('debit', 0), 2),
                credit=round(ld.get('credit', 0), 2),
                description=ld.get('description'),
                currency=ld.get('currency', 'USD'),
                exchange_rate=ld.get('exchange_rate', 1.0),
            )
            db.session.add(line)
        db.session.commit()
        return je

    @staticmethod
    def post_journal_entry(tenant_id, entry_id):
        je = JournalEntry.query.filter_by(id=entry_id, tenant_id=tenant_id).first()
        if not je:
            raise ValueError('Journal entry not found')
        if je.status != 'draft':
            raise ValueError('Only draft entries can be posted')
        je.status = 'posted'
        je.posted_at = datetime.now(timezone.utc)
        db.session.commit()
        return je

    @staticmethod
    def reverse_journal_entry(tenant_id, entry_id, user_id=None):
        je = JournalEntry.query.filter_by(id=entry_id, tenant_id=tenant_id).first()
        if not je:
            raise ValueError('Journal entry not found')
        if je.status != 'posted':
            raise ValueError('Only posted entries can be reversed')
        reversal_lines = []
        for line in je.lines.all():
            reversal_lines.append({
                'account_id': line.account_id,
                'debit': line.credit, 'credit': line.debit,
                'description': f'Reversal of {je.number}',
                'currency': line.currency, 'exchange_rate': line.exchange_rate,
            })
        reversal = AccountingService.create_journal_entry(tenant_id, {
            'description': f'Reversal of {je.number}',
            'reference_type': 'reversal', 'reference_id': je.id,
            'lines': reversal_lines,
        }, user_id=user_id)
        reversal.status = 'posted'
        reversal.posted_at = datetime.now(timezone.utc)
        je.status = 'reversed'
        db.session.commit()
        return reversal

    # ── Tax Rates ────────────────────────────────────────────

    @staticmethod
    def list_tax_rates(tenant_id, active_only=True):
        q = TaxRate.query.filter_by(tenant_id=tenant_id)
        if active_only:
            q = q.filter_by(is_active=True)
        return q.order_by(TaxRate.code).all()

    @staticmethod
    def create_tax_rate(tenant_id, data):
        tr = TaxRate(
            tenant_id=tenant_id, name=data['name'], code=data['code'],
            rate=data['rate'], tax_type=data.get('tax_type', 'both'),
            jurisdiction=data.get('jurisdiction'),
        )
        db.session.add(tr)
        db.session.commit()
        return tr

    @staticmethod
    def update_tax_rate(tenant_id, tax_id, data):
        tr = TaxRate.query.filter_by(id=tax_id, tenant_id=tenant_id).first()
        if not tr:
            return None
        for f in ['name', 'code', 'rate', 'tax_type', 'jurisdiction', 'is_active']:
            if f in data:
                setattr(tr, f, data[f])
        db.session.commit()
        return tr

    # ── Currencies ───────────────────────────────────────────

    @staticmethod
    def list_currencies(tenant_id):
        return CurrencyRate.query.filter_by(tenant_id=tenant_id)\
            .order_by(CurrencyRate.code).all()

    @staticmethod
    def create_currency(tenant_id, data):
        cr = CurrencyRate(
            tenant_id=tenant_id, code=data['code'].upper(),
            name=data['name'], symbol=data.get('symbol', ''),
            exchange_rate=data.get('exchange_rate', 1.0),
            is_base=data.get('is_base', False),
        )
        db.session.add(cr)
        db.session.commit()
        return cr

    @staticmethod
    def update_currency(tenant_id, currency_id, data):
        cr = CurrencyRate.query.filter_by(id=currency_id, tenant_id=tenant_id).first()
        if not cr:
            return None
        for f in ['name', 'symbol', 'exchange_rate', 'is_base']:
            if f in data:
                setattr(cr, f, data[f])
        cr.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return cr

    # ── Reports ──────────────────────────────────────────────

    @staticmethod
    def trial_balance(tenant_id, as_of=None):
        """Return list of accounts with total debit/credit from posted entries."""
        q = db.session.query(
            Account.id, Account.code, Account.name, Account.account_type,
            func.coalesce(func.sum(JournalLine.debit), 0).label('total_debit'),
            func.coalesce(func.sum(JournalLine.credit), 0).label('total_credit'),
        ).outerjoin(JournalLine, JournalLine.account_id == Account.id)\
         .outerjoin(JournalEntry, JournalLine.journal_entry_id == JournalEntry.id)\
         .filter(Account.tenant_id == tenant_id)\
         .filter(db.or_(JournalEntry.status == 'posted', JournalEntry.id.is_(None)))
        if as_of:
            q = q.filter(db.or_(JournalEntry.date <= as_of, JournalEntry.id.is_(None)))
        rows = q.group_by(Account.id, Account.code, Account.name, Account.account_type)\
                .order_by(Account.code).all()
        result = []
        for r in rows:
            balance = r.total_debit - r.total_credit
            result.append({
                'account_id': r.id, 'code': r.code, 'name': r.name,
                'account_type': r.account_type,
                'total_debit': round(r.total_debit, 2),
                'total_credit': round(r.total_credit, 2),
                'balance': round(balance, 2),
            })
        return result

    @staticmethod
    def profit_and_loss(tenant_id, start_date=None, end_date=None):
        """Revenue - Expense summary."""
        q = db.session.query(
            Account.account_type,
            func.coalesce(func.sum(JournalLine.credit - JournalLine.debit), 0).label('net'),
        ).join(JournalLine, JournalLine.account_id == Account.id)\
         .join(JournalEntry, JournalLine.journal_entry_id == JournalEntry.id)\
         .filter(Account.tenant_id == tenant_id, JournalEntry.status == 'posted')\
         .filter(Account.account_type.in_(['revenue', 'expense']))
        if start_date:
            q = q.filter(JournalEntry.date >= start_date)
        if end_date:
            q = q.filter(JournalEntry.date <= end_date)
        rows = q.group_by(Account.account_type).all()
        revenue = 0
        expense = 0
        for r in rows:
            if r.account_type == 'revenue':
                revenue = round(r.net, 2)
            elif r.account_type == 'expense':
                expense = round(-r.net, 2)  # expenses are debits
        return {'revenue': revenue, 'expense': expense, 'net_income': round(revenue - expense, 2)}

    @staticmethod
    def balance_sheet(tenant_id, as_of=None):
        """Assets = Liabilities + Equity summary."""
        tb = AccountingService.trial_balance(tenant_id, as_of=as_of)
        assets = sum(r['balance'] for r in tb if r['account_type'] == 'asset')
        liabilities = sum(-r['balance'] for r in tb if r['account_type'] == 'liability')
        equity = sum(-r['balance'] for r in tb if r['account_type'] == 'equity')
        return {
            'assets': round(assets, 2),
            'liabilities': round(liabilities, 2),
            'equity': round(equity, 2),
            'accounts': tb,
        }

    @staticmethod
    def get_stats(tenant_id):
        """Quick accounting statistics."""
        account_count = Account.query.filter_by(tenant_id=tenant_id, is_active=True).count()
        je_count = JournalEntry.query.filter_by(tenant_id=tenant_id).count()
        posted_count = JournalEntry.query.filter_by(tenant_id=tenant_id, status='posted').count()
        return {
            'total_accounts': account_count,
            'total_journal_entries': je_count,
            'posted_entries': posted_count,
            'draft_entries': je_count - posted_count,
        }
