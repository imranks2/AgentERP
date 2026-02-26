"""Database models package."""
from app.models.tenant import Tenant
from app.models.subscription import SubscriptionPlan, Subscription, PlanFeature
from app.models.role import Role, Permission, AuditLog
from app.models.user import User
from app.models.analytics import AnalyticsEvent
from app.models.organisation import OrganisationUnit
from app.models.module import ModuleDefinition, TenantModule
from app.models.inventory import (
    ProductCategory, Product, Warehouse, StockEntry, StockMovement,
)
from app.models.sales import (
    Customer, Quotation, QuotationItem, Invoice, InvoiceItem, Payment,
)
from app.models.purchasing import Supplier, PurchaseOrder, PurchaseOrderItem
from app.models.event import EventLog, Notification
from app.models.ai import Conversation, Message, AIInteractionLog
from app.models.accounting import (
    Account, FiscalYear, FiscalPeriod, JournalEntry, JournalLine, TaxRate, CurrencyRate,
)
from app.models.crm import Lead, Opportunity, CRMActivity
from app.models.hr import (
    Employee, LeaveType, LeaveRequest, PayrollRun, PaySlip, Attendance,
)
from app.models.ai_advanced import (
    AISuggestion, AgentAction, WorkflowPattern, AutomatedWorkflow,
    TrainingDataset, ModelVersion,
)

__all__ = [
    'Tenant',
    'SubscriptionPlan',
    'Subscription',
    'PlanFeature',
    'Role',
    'Permission',
    'AuditLog',
    'User',
    'AnalyticsEvent',
    'OrganisationUnit',
    'ModuleDefinition',
    'TenantModule',
    'ProductCategory',
    'Product',
    'Warehouse',
    'StockEntry',
    'StockMovement',
    'Customer',
    'Quotation',
    'QuotationItem',
    'Invoice',
    'InvoiceItem',
    'Payment',
    'Supplier',
    'PurchaseOrder',
    'PurchaseOrderItem',
    'EventLog',
    'Notification',
    'Conversation',
    'Message',
    'AIInteractionLog',
    'Account',
    'FiscalYear',
    'FiscalPeriod',
    'JournalEntry',
    'JournalLine',
    'TaxRate',
    'CurrencyRate',
    'Lead',
    'Opportunity',
    'CRMActivity',
    'Employee',
    'LeaveType',
    'LeaveRequest',
    'PayrollRun',
    'PaySlip',
    'Attendance',
    'AISuggestion',
    'AgentAction',
    'WorkflowPattern',
    'AutomatedWorkflow',
    'TrainingDataset',
    'ModelVersion',
]
