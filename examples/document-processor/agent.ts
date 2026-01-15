/**
 * Document Processor Agent
 *
 * Extracts structured data from documents (text, markdown, JSON) using
 * LLM-powered analysis. Supports schema-based extraction.
 *
 * Price: $0.04 per invocation
 */

import { agent } from "seren-agent";
import { getOpenAIClient } from "seren-agent/llm";

interface ExtractedField {
  name: string;
  value: string | number | boolean | null;
  confidence: number;
  source_text?: string;
}

interface ExtractionResult {
  fields: ExtractedField[];
  structured_data: Record<string, unknown>;
  summary: string;
  metadata: {
    document_type: string;
    fields_extracted: number;
    avg_confidence: number;
  };
}

interface DocumentInput {
  document: string;
  schema?: Record<string, string>;
  document_type?: string;
  extract_tables?: boolean;
}

export const run = agent(
  {
    name: "Document Processor",
    description:
      "Extract structured data from documents. Provide a document and optional " +
      "schema defining fields to extract. Supports text, markdown, and JSON.",
    price: "0.04",
  },
  async (
    input: DocumentInput,
  ): Promise<ExtractionResult | { error: string }> => {
    const { document, schema, document_type, extract_tables } = input;

    if (!document) {
      return { error: "Missing required field: document" };
    }

    const client = getOpenAIClient();

    // Build extraction prompt
    let schemaInstructions = "";
    if (schema) {
      schemaInstructions = `
Extract the following fields:
${Object.entries(schema)
  .map(([field, description]) => `- ${field}: ${description}`)
  .join("\n")}
`;
    } else {
      schemaInstructions = `
Automatically identify and extract all relevant structured data from the document.
Common fields to look for: names, dates, amounts, addresses, IDs, categories.
`;
    }

    const systemPrompt = `You are a document processing expert. Extract structured data from the provided document.

${schemaInstructions}

${extract_tables ? "Also extract any tabular data you find." : ""}

Return your response as valid JSON with this structure:
{
    "fields": [
        {
            "name": "field_name",
            "value": "extracted_value",
            "confidence": 0.95,
            "source_text": "relevant excerpt from document"
        }
    ],
    "structured_data": {
        "field1": "value1",
        "field2": "value2"
    },
    "summary": "Brief summary of what was extracted",
    "document_type": "invoice|contract|receipt|report|other"
}

Be precise and include confidence scores (0-1) for each extraction.`;

    try {
      const response = await client.chat.completions.create({
        model: "gpt-4o",
        messages: [
          { role: "system", content: systemPrompt },
          {
            role: "user",
            content: `Process this document:\n\n${document}`,
          },
        ],
        temperature: 0.2,
        response_format: { type: "json_object" },
      });

      const content = response.choices[0]?.message?.content;
      if (!content) {
        return { error: "Empty response from LLM" };
      }

      const result = JSON.parse(content);

      // Validate and normalize fields
      const fields: ExtractedField[] = (result.fields || []).map(
        (f: Partial<ExtractedField>) => ({
          name: f.name || "unknown",
          value: f.value ?? null,
          confidence: Math.min(1, Math.max(0, f.confidence ?? 0.5)),
          source_text: f.source_text,
        }),
      );

      // Calculate average confidence
      const avgConfidence =
        fields.length > 0
          ? fields.reduce((sum, f) => sum + f.confidence, 0) / fields.length
          : 0;

      return {
        fields,
        structured_data: result.structured_data || {},
        summary: result.summary || "Document processed successfully.",
        metadata: {
          document_type: document_type || result.document_type || "unknown",
          fields_extracted: fields.length,
          avg_confidence: Math.round(avgConfidence * 100) / 100,
        },
      };
    } catch (error) {
      return {
        error: `Processing failed: ${error instanceof Error ? error.message : String(error)}`,
      };
    }
  },
);

// Local testing (run with: npx ts-node agent.ts)
const isMainModule = typeof require !== "undefined" && require.main === module;
if (isMainModule) {
  const sampleDocument = `
INVOICE #INV-2024-001

Date: January 15, 2024
Due Date: February 15, 2024

Bill To:
Acme Corporation
123 Business St
San Francisco, CA 94102

Items:
- Software License (Annual): $1,200.00
- Support Package: $300.00
- Training (5 hours): $500.00

Subtotal: $2,000.00
Tax (8.5%): $170.00
Total: $2,170.00

Payment Terms: Net 30
`;

  run({
    document: sampleDocument,
    schema: {
      invoice_number: "The invoice ID or number",
      total_amount: "The total amount due",
      due_date: "When payment is due",
      customer_name: "The customer or company being billed",
    },
  }).then((result) => console.log(JSON.stringify(result, null, 2)));
}
