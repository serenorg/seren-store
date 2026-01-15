# Document Processor Agent

Extract structured data from documents using LLM-powered analysis.

## Usage

```typescript
// Input
{
    "document": "INVOICE #INV-2024-001\nDate: Jan 15, 2024\n...",
    "schema": {                           // optional: fields to extract
        "invoice_number": "The invoice ID",
        "total_amount": "Total amount due",
        "due_date": "Payment due date"
    },
    "document_type": "invoice",           // optional hint
    "extract_tables": true                // optional: extract tabular data
}

// Output
{
    "fields": [
        {
            "name": "invoice_number",
            "value": "INV-2024-001",
            "confidence": 0.98,
            "source_text": "INVOICE #INV-2024-001"
        },
        {
            "name": "total_amount",
            "value": 2170.00,
            "confidence": 0.95,
            "source_text": "Total: $2,170.00"
        }
    ],
    "structured_data": {
        "invoice_number": "INV-2024-001",
        "total_amount": 2170.00,
        "due_date": "2024-02-15"
    },
    "summary": "Invoice from Acme Corp for $2,170.00 due Feb 15, 2024",
    "metadata": {
        "document_type": "invoice",
        "fields_extracted": 4,
        "avg_confidence": 0.94
    }
}
```

## Supported Document Types

- **Invoices** - Extract line items, totals, dates, parties
- **Contracts** - Extract parties, terms, dates, clauses
- **Receipts** - Extract items, amounts, merchant info
- **Reports** - Extract key metrics, summaries, dates
- **General text** - Auto-detect and extract relevant fields

## Pricing

- **$0.04 per invocation**

## Schema-Based Extraction

Provide a schema to extract specific fields:

```json
{
    "document": "...",
    "schema": {
        "field_name": "Description of what to extract",
        "another_field": "Another description"
    }
}
```

Without a schema, the agent auto-detects relevant fields.

## Local Testing

```bash
cd examples/document-processor
OPENAI_API_KEY=your-key npx ts-node agent.ts
```
