"""SQLite database connection, schema creation, and helpers."""
import sqlite3
import logging
from pathlib import Path
from app.config import DATABASE_PATH

logger = logging.getLogger(__name__)

_connection: sqlite3.Connection | None = None


def get_connection() -> sqlite3.Connection:
    """Return a shared SQLite connection (WAL mode, row factory)."""
    global _connection
    if _connection is None:
        db_path = Path(DATABASE_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _connection = sqlite3.connect(str(db_path), check_same_thread=False)
        _connection.execute("PRAGMA journal_mode=WAL")
        _connection.execute("PRAGMA foreign_keys=ON")
        _connection.row_factory = sqlite3.Row
        logger.info("Connected to SQLite at %s", db_path)
    return _connection


def create_schema():
    """Create all tables and indexes for the O2C dataset."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS business_partners (
            businessPartner TEXT PRIMARY KEY,
            customer TEXT,
            businessPartnerCategory TEXT,
            businessPartnerFullName TEXT,
            businessPartnerGrouping TEXT,
            businessPartnerName TEXT,
            correspondenceLanguage TEXT,
            createdByUser TEXT,
            creationDate TEXT,
            creationTime TEXT,
            firstName TEXT,
            formOfAddress TEXT,
            industry TEXT,
            lastChangeDate TEXT,
            lastName TEXT,
            organizationBpName1 TEXT,
            organizationBpName2 TEXT,
            businessPartnerIsBlocked INTEGER DEFAULT 0,
            isMarkedForArchiving INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS customer_company_assignments (
            customer TEXT,
            companyCode TEXT,
            accountingClerk TEXT,
            accountingClerkFaxNumber TEXT,
            accountingClerkInternetAddress TEXT,
            accountingClerkPhoneNumber TEXT,
            alternativePayerAccount TEXT,
            paymentBlockingReason TEXT,
            paymentMethodsList TEXT,
            paymentTerms TEXT,
            reconciliationAccount TEXT,
            deletionIndicator INTEGER DEFAULT 0,
            customerAccountGroup TEXT,
            PRIMARY KEY (customer, companyCode)
        );

        CREATE TABLE IF NOT EXISTS customer_sales_area_assignments (
            customer TEXT,
            salesOrganization TEXT,
            distributionChannel TEXT,
            division TEXT,
            billingIsBlockedForCustomer TEXT,
            completeDeliveryIsDefined INTEGER DEFAULT 0,
            creditControlArea TEXT,
            currency TEXT,
            customerPaymentTerms TEXT,
            deliveryPriority TEXT,
            incotermsClassification TEXT,
            incotermsLocation1 TEXT,
            salesGroup TEXT,
            salesOffice TEXT,
            shippingCondition TEXT,
            slsUnlmtdOvrdelivIsAllwd INTEGER DEFAULT 0,
            supplyingPlant TEXT,
            salesDistrict TEXT,
            exchangeRateType TEXT,
            PRIMARY KEY (customer, salesOrganization, distributionChannel, division)
        );

        CREATE TABLE IF NOT EXISTS sales_order_headers (
            salesOrder TEXT PRIMARY KEY,
            salesOrderType TEXT,
            salesOrganization TEXT,
            distributionChannel TEXT,
            organizationDivision TEXT,
            salesGroup TEXT,
            salesOffice TEXT,
            soldToParty TEXT,
            creationDate TEXT,
            createdByUser TEXT,
            lastChangeDateTime TEXT,
            totalNetAmount REAL,
            overallDeliveryStatus TEXT,
            overallOrdReltdBillgStatus TEXT,
            overallSdDocReferenceStatus TEXT,
            transactionCurrency TEXT,
            pricingDate TEXT,
            requestedDeliveryDate TEXT,
            headerBillingBlockReason TEXT,
            deliveryBlockReason TEXT,
            incotermsClassification TEXT,
            incotermsLocation1 TEXT,
            customerPaymentTerms TEXT,
            totalCreditCheckStatus TEXT
        );

        CREATE TABLE IF NOT EXISTS sales_order_items (
            salesOrder TEXT,
            salesOrderItem TEXT,
            salesOrderItemCategory TEXT,
            material TEXT,
            requestedQuantity REAL,
            requestedQuantityUnit TEXT,
            transactionCurrency TEXT,
            netAmount REAL,
            materialGroup TEXT,
            productionPlant TEXT,
            storageLocation TEXT,
            salesDocumentRjcnReason TEXT,
            itemBillingBlockReason TEXT,
            PRIMARY KEY (salesOrder, salesOrderItem)
        );

        CREATE TABLE IF NOT EXISTS outbound_delivery_headers (
            deliveryDocument TEXT PRIMARY KEY,
            actualGoodsMovementDate TEXT,
            actualGoodsMovementTime TEXT,
            creationDate TEXT,
            creationTime TEXT,
            deliveryBlockReason TEXT,
            hdrGeneralIncompletionStatus TEXT,
            headerBillingBlockReason TEXT,
            lastChangeDate TEXT,
            overallGoodsMovementStatus TEXT,
            overallPickingStatus TEXT,
            overallProofOfDeliveryStatus TEXT,
            shippingPoint TEXT
        );

        CREATE TABLE IF NOT EXISTS billing_documents (
            billingDocument TEXT PRIMARY KEY,
            billingDocumentType TEXT,
            creationDate TEXT,
            creationTime TEXT,
            lastChangeDateTime TEXT,
            billingDocumentDate TEXT,
            billingDocumentIsCancelled INTEGER DEFAULT 0,
            cancelledBillingDocument TEXT,
            totalNetAmount REAL,
            transactionCurrency TEXT,
            companyCode TEXT,
            fiscalYear TEXT,
            accountingDocument TEXT,
            soldToParty TEXT
        );

        CREATE TABLE IF NOT EXISTS journal_entries (
            companyCode TEXT,
            fiscalYear TEXT,
            accountingDocument TEXT,
            accountingDocumentItem TEXT,
            glAccount TEXT,
            referenceDocument TEXT,
            costCenter TEXT,
            profitCenter TEXT,
            transactionCurrency TEXT,
            amountInTransactionCurrency REAL,
            companyCodeCurrency TEXT,
            amountInCompanyCodeCurrency REAL,
            postingDate TEXT,
            documentDate TEXT,
            accountingDocumentType TEXT,
            assignmentReference TEXT,
            lastChangeDateTime TEXT,
            customer TEXT,
            financialAccountType TEXT,
            clearingDate TEXT,
            clearingAccountingDocument TEXT,
            clearingDocFiscalYear TEXT,
            PRIMARY KEY (companyCode, fiscalYear, accountingDocument, accountingDocumentItem)
        );

        CREATE TABLE IF NOT EXISTS payments (
            companyCode TEXT,
            fiscalYear TEXT,
            accountingDocument TEXT,
            accountingDocumentItem TEXT,
            clearingDate TEXT,
            clearingAccountingDocument TEXT,
            clearingDocFiscalYear TEXT,
            amountInTransactionCurrency REAL,
            transactionCurrency TEXT,
            amountInCompanyCodeCurrency REAL,
            companyCodeCurrency TEXT,
            customer TEXT,
            invoiceReference TEXT,
            invoiceReferenceFiscalYear TEXT,
            salesDocument TEXT,
            salesDocumentItem TEXT,
            postingDate TEXT,
            documentDate TEXT,
            assignmentReference TEXT,
            glAccount TEXT,
            financialAccountType TEXT,
            profitCenter TEXT,
            costCenter TEXT,
            PRIMARY KEY (companyCode, fiscalYear, accountingDocument, accountingDocumentItem)
        );

        CREATE TABLE IF NOT EXISTS plants (
            plant TEXT PRIMARY KEY,
            plantName TEXT,
            valuationArea TEXT,
            plantCustomer TEXT,
            plantSupplier TEXT,
            factoryCalendar TEXT,
            defaultPurchasingOrganization TEXT,
            salesOrganization TEXT,
            addressId TEXT,
            plantCategory TEXT,
            distributionChannel TEXT,
            division TEXT,
            language TEXT,
            isMarkedForArchiving INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS product_descriptions (
            product TEXT,
            language TEXT,
            productDescription TEXT,
            PRIMARY KEY (product, language)
        );

        CREATE TABLE IF NOT EXISTS product_plants (
            product TEXT,
            plant TEXT,
            countryOfOrigin TEXT,
            regionOfOrigin TEXT,
            productionInvtryManagedLoc TEXT,
            availabilityCheckType TEXT,
            fiscalYearVariant TEXT,
            profitCenter TEXT,
            mrpType TEXT,
            PRIMARY KEY (product, plant)
        );

        CREATE TABLE IF NOT EXISTS product_storage_locations (
            product TEXT,
            plant TEXT,
            storageLocation TEXT,
            physicalInventoryBlockInd TEXT,
            dateOfLastPostedCntUnRstrcdStk TEXT,
            PRIMARY KEY (product, plant, storageLocation)
        );

        -- Indexes for fast joins
        CREATE INDEX IF NOT EXISTS idx_soh_soldtoparty ON sales_order_headers(soldToParty);
        CREATE INDEX IF NOT EXISTS idx_soi_salesorder ON sales_order_items(salesOrder);
        CREATE INDEX IF NOT EXISTS idx_soi_material ON sales_order_items(material);
        CREATE INDEX IF NOT EXISTS idx_soi_plant ON sales_order_items(productionPlant);
        CREATE INDEX IF NOT EXISTS idx_bd_soldtoparty ON billing_documents(soldToParty);
        CREATE INDEX IF NOT EXISTS idx_bd_acctdoc ON billing_documents(accountingDocument);
        CREATE INDEX IF NOT EXISTS idx_je_refdoc ON journal_entries(referenceDocument);
        CREATE INDEX IF NOT EXISTS idx_je_customer ON journal_entries(customer);
        CREATE INDEX IF NOT EXISTS idx_je_clearingdoc ON journal_entries(clearingAccountingDocument);
        CREATE INDEX IF NOT EXISTS idx_pay_customer ON payments(customer);
        CREATE INDEX IF NOT EXISTS idx_pay_clearingdoc ON payments(clearingAccountingDocument);
        CREATE INDEX IF NOT EXISTS idx_pp_plant ON product_plants(plant);
        CREATE INDEX IF NOT EXISTS idx_pp_product ON product_plants(product);
        CREATE INDEX IF NOT EXISTS idx_psl_plant ON product_storage_locations(plant);
    """)
    conn.commit()
    logger.info("Database schema created successfully")


def get_schema_description() -> str:
    """Return a human-readable description of the database schema for LLM context."""
    return """
DATABASE SCHEMA — SAP Order-to-Cash (O2C) System

TABLE: business_partners
  - businessPartner (PK): Unique partner ID (also used as customer ID)
  - customer: Customer number (same as businessPartner)
  - businessPartnerFullName: Company/person full name
  - businessPartnerIsBlocked: 0/1 flag

TABLE: sales_order_headers
  - salesOrder (PK): Sales order number (e.g., "740506")
  - soldToParty (FK → business_partners.customer): Customer who placed the order
  - totalNetAmount (REAL): Order total in transaction currency
  - transactionCurrency: Currency code (e.g., "INR")
  - overallDeliveryStatus: "C"=Complete, "B"=Partial, "A"=Not started, ""=Unknown
  - creationDate: When the order was created
  - requestedDeliveryDate: Requested delivery date

TABLE: sales_order_items
  - salesOrder (PK, FK → sales_order_headers): Parent order
  - salesOrderItem (PK): Item number within order (e.g., "10", "20")
  - material (FK → product_descriptions.product): Product/material number
  - requestedQuantity (REAL): Quantity ordered
  - netAmount (REAL): Line item amount
  - productionPlant (FK → plants.plant): Plant that produces/ships the item
  - storageLocation: Storage location code

TABLE: outbound_delivery_headers
  - deliveryDocument (PK): Delivery document number (e.g., "80737721")
  - shippingPoint: Shipping point code (may match a plant)
  - overallGoodsMovementStatus: "A"=Open, "B"=Partial, "C"=Complete
  - overallPickingStatus: Picking status
  - creationDate: Delivery creation date
  - NOTE: No direct FK to sales orders. Link via shippingPoint → plants or customer matching.

TABLE: billing_documents
  - billingDocument (PK): Billing/invoice document number (e.g., "90504274")
  - soldToParty (FK → business_partners.customer): Billed customer
  - accountingDocument (FK → journal_entries): Associated accounting document
  - billingDocumentIsCancelled: 0=Active, 1=Cancelled
  - cancelledBillingDocument: If this is a cancellation, references the original
  - totalNetAmount (REAL): Invoice amount
  - billingDocumentDate: Invoice date

TABLE: journal_entries
  - companyCode + fiscalYear + accountingDocument + accountingDocumentItem (composite PK)
  - referenceDocument (FK → billing_documents.billingDocument): Source billing doc
  - customer (FK → business_partners.customer): Customer for this entry
  - glAccount: General ledger account
  - amountInTransactionCurrency (REAL): Posted amount
  - clearingAccountingDocument: Document that cleared this entry (FK → payments)
  - accountingDocumentType: "RV"=Revenue, etc.
  - postingDate: When posted

TABLE: payments
  - companyCode + fiscalYear + accountingDocument + accountingDocumentItem (composite PK)
  - customer (FK → business_partners.customer): Paying customer
  - clearingAccountingDocument: References the cleared document
  - amountInTransactionCurrency (REAL): Payment amount
  - invoiceReference: May reference a billing document
  - salesDocument: May reference a sales order
  - postingDate: Payment date

TABLE: plants
  - plant (PK): Plant code (e.g., "1001")
  - plantName: Name (e.g., "Lake Christopher Plant")
  - salesOrganization: Associated sales org

TABLE: product_descriptions
  - product + language (composite PK)
  - product: Material/product number
  - productDescription: Human-readable name (e.g., "WB-CG CHARCOAL GANG")

TABLE: customer_company_assignments
  - customer + companyCode (composite PK)
  - reconciliationAccount: GL reconciliation account

TABLE: customer_sales_area_assignments
  - customer + salesOrganization + distributionChannel + division (composite PK)
  - customerPaymentTerms: Payment terms code
  - incotermsClassification: Shipping terms

TABLE: product_plants
  - product + plant (composite PK): Which products are at which plants
  - profitCenter: Profit center code

TABLE: product_storage_locations
  - product + plant + storageLocation (composite PK): Storage details

CORE O2C FLOW RELATIONSHIPS:
1. SalesOrderHeader.soldToParty → business_partners.customer (SOLD_TO)
2. SalesOrderItem.salesOrder → sales_order_headers.salesOrder (HAS_ITEM)
3. SalesOrderItem.material → product_descriptions.product (CONTAINS_MATERIAL)
4. SalesOrderItem.productionPlant → plants.plant (PRODUCED_AT)
5. BillingDocument.soldToParty → business_partners.customer (BILLED_TO)
6. BillingDocument.accountingDocument → journal_entries.accountingDocument (GENERATES_JOURNAL)
7. JournalEntry.referenceDocument → billing_documents.billingDocument (REFERENCES_BILLING)
8. JournalEntry.customer → business_partners.customer (POSTED_FOR)
9. JournalEntry.clearingAccountingDocument = Payment.clearingAccountingDocument (CLEARED_BY)
10. Payment.customer → business_partners.customer (PAID_BY)
""".strip()


def execute_readonly_sql(sql: str) -> list[dict]:
    """Execute a read-only SQL query and return results as list of dicts."""
    conn = get_connection()
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
        raise ValueError("Only SELECT/WITH queries are allowed")
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "REPLACE", "TRUNCATE"]
    for word in forbidden:
        if word in sql_upper.split():
            raise ValueError(f"Forbidden SQL keyword: {word}")
    cursor = conn.execute(sql)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    return [dict(zip(columns, row)) for row in rows]
