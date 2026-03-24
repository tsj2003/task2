# 📊 SAP Order-to-Cash Dataset — Full Schema Analysis

> **Dataset Format**: JSONL (JSON Lines) files, organized in 13 entity folders  
> **Total Records**: ~18,833 across all entities

---

## Entity Summary

| # | Entity Folder | Rows | Primary Key(s) | Description |
|---|---|---|---|---|
| 1 | `sales_order_headers` | 100 | `salesOrder` | Sales order master records |
| 2 | `sales_order_items` | 167 | `salesOrder` + `salesOrderItem` | Line items within sales orders |
| 3 | `outbound_delivery_headers` | 86 | `deliveryDocument` | Delivery documents for shipped goods |
| 4 | `billing_document_cancellations` | 80 | `billingDocument` | Billing/invoice documents (incl. cancellation flag) |
| 5 | `journal_entry_items_accounts_receivable` | 123 | `companyCode` + `fiscalYear` + `accountingDocument` + `accountingDocumentItem` | GL journal entries |
| 6 | `payments_accounts_receivable` | 120 | `companyCode` + `fiscalYear` + `accountingDocument` + `accountingDocumentItem` | Payment clearing records |
| 7 | `business_partners` | 8 | `businessPartner` | Customer/partner master data |
| 8 | `customer_company_assignments` | 8 | `customer` + `companyCode` | Customer-to-company code |
| 9 | `customer_sales_area_assignments` | 28 | `customer` + `salesOrganization` + `distributionChannel` + `division` | Customer sales area config |
| 10 | `plants` | 44 | `plant` | Manufacturing/distribution plants |
| 11 | `product_descriptions` | 69 | `product` + `language` | Product names |
| 12 | `product_plants` | 1,200 | `product` + `plant` | Product-plant assignments |
| 13 | `product_storage_locations` | 16,723 | `product` + `plant` + `storageLocation` | Product storage details |

---

## Entity-Relationship Diagram

```mermaid
erDiagram
    BUSINESS_PARTNERS {
        string businessPartner PK
        string customer
        string businessPartnerFullName
    }
    SALES_ORDER_HEADERS {
        string salesOrder PK
        string soldToParty FK
        string totalNetAmount
        string overallDeliveryStatus
    }
    SALES_ORDER_ITEMS {
        string salesOrder PK_FK
        string salesOrderItem PK
        string material FK
        string productionPlant FK
    }
    OUTBOUND_DELIVERY_HEADERS {
        string deliveryDocument PK
        string shippingPoint
        string overallGoodsMovementStatus
    }
    BILLING_DOCUMENTS {
        string billingDocument PK
        string soldToParty FK
        string accountingDocument FK
        boolean billingDocumentIsCancelled
    }
    JOURNAL_ENTRIES {
        string accountingDocument PK
        string referenceDocument FK
        string customer FK
        string clearingAccountingDocument
    }
    PAYMENTS {
        string accountingDocument PK
        string customer FK
        string clearingAccountingDocument
    }
    PLANTS {
        string plant PK
        string plantName
    }
    PRODUCT_DESCRIPTIONS {
        string product PK
        string productDescription
    }

    BUSINESS_PARTNERS ||--o{ SALES_ORDER_HEADERS : "customer = soldToParty"
    SALES_ORDER_HEADERS ||--o{ SALES_ORDER_ITEMS : "salesOrder"
    SALES_ORDER_ITEMS }o--|| PRODUCT_DESCRIPTIONS : "material = product"
    SALES_ORDER_ITEMS }o--|| PLANTS : "productionPlant = plant"
    BILLING_DOCUMENTS ||--o| JOURNAL_ENTRIES : "accountingDocument"
    JOURNAL_ENTRIES ||--o| BILLING_DOCUMENTS : "referenceDocument = billingDocument"
    JOURNAL_ENTRIES ||--o| PAYMENTS : "clearingAccountingDocument"
    BUSINESS_PARTNERS ||--o{ BILLING_DOCUMENTS : "customer = soldToParty"
    BUSINESS_PARTNERS ||--o{ JOURNAL_ENTRIES : "customer"
    BUSINESS_PARTNERS ||--o{ PAYMENTS : "customer"
```

---

## Relationship Map (All Edges for Graph)

| # | From | → | To | Join Key | Edge Label |
|---|---|---|---|---|---|
| 1 | SalesOrderHeader | → | SalesOrderItem | `salesOrder` | HAS_ITEM |
| 2 | SalesOrderHeader | → | BusinessPartner | `soldToParty = customer` | SOLD_TO |
| 3 | SalesOrderItem | → | Product | `material = product` | CONTAINS_MATERIAL |
| 4 | SalesOrderItem | → | Plant | `productionPlant = plant` | PRODUCED_AT |
| 5 | BillingDocument | → | BusinessPartner | `soldToParty = customer` | BILLED_TO |
| 6 | BillingDocument | → | JournalEntry | `accountingDocument` | GENERATES_JOURNAL |
| 7 | JournalEntry | → | BillingDocument | `referenceDocument = billingDocument` | REFERENCES_BILLING |
| 8 | JournalEntry | → | BusinessPartner | `customer` | POSTED_FOR |
| 9 | JournalEntry | → | Payment | `clearingAccountingDocument` | CLEARED_BY |
| 10 | Payment | → | BusinessPartner | `customer` | PAID_BY |
| 11 | BusinessPartner | → | CustCompanyAssign | `customer` | ASSIGNED_TO_COMPANY |
| 12 | BusinessPartner | → | CustSalesAreaAssign | `customer` | ASSIGNED_TO_SALES_AREA |
| 13 | Plant | → | ProductPlant | `plant` | STORES_PRODUCT |
| 14 | Product | → | ProductPlant | `product` | AVAILABLE_AT_PLANT |
| 15 | ProductPlant | → | ProductStorageLoc | `product + plant` | STORED_AT |

---

## Core O2C Business Flow

```
SalesOrder → SalesOrderItem → [Material/Product]
     ↓
OutboundDelivery → [shipped goods]
     ↓
BillingDocument → [invoice created]
     ↓
JournalEntry → [accounting posted]
     ↓
Payment → [cash received/cleared]
```

> [!WARNING]
> **Missing Link**: No direct FK between `sales_order_headers` ↔ `outbound_delivery_headers` ↔ `billing_document_cancellations`. SAP normally uses VBFA (document flow table) for this, which is **absent**. Must infer via customer + date matching or `referenceDocument`/`invoiceReference` fields.

---

## ⚠️ Data Quality Notes

1. **Numerics as strings**: `totalNetAmount`, `netAmount`, `requestedQuantity`, `amountInTransactionCurrency` — cast to `REAL`
2. **Time as nested objects**: `{hours, minutes, seconds}` — flatten to `HH:MM:SS`
3. **Missing O2C flow links**: Infer order→delivery→billing chain via customer + temporal proximity
4. **Mixed nulls**: Both `""` and `null` used — normalize to `NULL`
5. **`billingDocumentIsCancelled`**: Boolean — critical for anomaly detection
