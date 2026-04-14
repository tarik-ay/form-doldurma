"""
STEP 1 — PDF parse + invoice page detection + Presidio PII masking
Usage:  python step1_mask.py invoice.pdf
Output: masked_output.json  (keep locally — contains PII mapping)
        claude_input.json   (safe to send to Claude — no PII)
"""

import json
import sys
import uuid
import pdfplumber
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# ── Invoice keyword list (extend as needed) ───────────────────────────────────
INVOICE_KEYWORDS = [
    "invoice", "inv", "commercial invoice", "proforma",
    "tax invoice", "fatura", "satis faturasi",
    "rechnung", "facture",
    "qinggodan", "fapiao",
    "faturah",
]

# ── PII entity types to mask ──────────────────────────────────────────────────
# The 11 target fields (HS code, quantity, weight, etc.) are NOT PII,
# so Presidio won't touch them.
MASK_ENTITIES = [
    "PERSON",
    "EMAIL_ADDRESS",
    "IBAN_CODE",
    "CREDIT_CARD",
    "LOCATION",
    "IP_ADDRESS",
    "US_SSN",
    "US_BANK_NUMBER",
    "URL",
]


def is_invoice_page(text: str) -> bool:
    """Return True if the page text contains an invoice keyword."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in INVOICE_KEYWORDS)


def extract_invoice_pages(pdf_path: str):
    """
    Read PDF page by page and identify invoice pages.
    Returns: (invoice_pages {page_no: text}, all_pages {page_no: metadata})
    """
    invoice_pages = {}
    all_pages = {}

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            is_inv = is_invoice_page(text)
            all_pages[i] = {"is_invoice": is_inv}

            if is_inv:
                invoice_pages[i] = text
                print(f"  [+] Page {i}: identified as INVOICE")
            else:
                print(f"  [-] Page {i}: not an invoice, skipped")

    return invoice_pages, all_pages


def mask_pii(text, analyzer, anonymizer):
    """
    Detect and replace PII with unique MASK_XXXXXXXX tokens.
    Same value always gets the same mask token.
    Returns: (masked_text, mapping dict)
    """
    mapping = {}
    reverse_mapping = {}

    results = analyzer.analyze(
        text=text,
        entities=MASK_ENTITIES,
        language="en",
    )

    if not results:
        return text, mapping

    operators = {}
    for result in results:
        original = text[result.start:result.end]

        if original in reverse_mapping:
            mask_key = reverse_mapping[original]
        else:
            mask_key = "MASK_" + uuid.uuid4().hex[:8].upper()
            mapping[mask_key] = original
            reverse_mapping[original] = mask_key

        operators[result.entity_type] = OperatorConfig(
            "replace", {"new_value": mask_key}
        )

    masked_result = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators=operators,
    )

    return masked_result.text, mapping


def run(pdf_path):
    print(f"\nFile: {pdf_path}")
    print("-" * 50)

    print("\n[1] Scanning pages...")
    invoice_pages, all_pages = extract_invoice_pages(pdf_path)

    if not invoice_pages:
        print("\nERROR: No invoice page found. Extend INVOICE_KEYWORDS list.")
        sys.exit(1)

    print(f"\n  Total pages  : {len(all_pages)}")
    print(f"  Invoice pages: {list(invoice_pages.keys())}")

    combined_text = "\n\n--- PAGE BREAK ---\n\n".join(
        f"[Page {p}]\n{t}" for p, t in invoice_pages.items()
    )

    print("\n[2] Masking PII locally (nothing sent to any API)...")
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()
    masked_text, mapping = mask_pii(combined_text, analyzer, anonymizer)

    print(f"  {len(mapping)} PII entities masked")
    for mask_key, original in mapping.items():
        print(f"    {mask_key}  =>  '{original}'")

    # Full output — keep LOCAL, contains PII mapping
    full_output = {
        "source_file": pdf_path,
        "invoice_pages": list(invoice_pages.keys()),
        "masked_text": masked_text,
        "pii_mapping": mapping,
    }
    with open("masked_output.json", "w", encoding="utf-8") as f:
        json.dump(full_output, f, ensure_ascii=False, indent=2)

    # Claude input — no PII mapping, safe to use with API
    claude_input = {
        "source_file": pdf_path,
        "invoice_pages": list(invoice_pages.keys()),
        "masked_text": masked_text,
    }
    with open("claude_input.json", "w", encoding="utf-8") as f:
        json.dump(claude_input, f, ensure_ascii=False, indent=2)

    print("\n[3] Files saved:")
    print("  masked_output.json  =>  contains PII mapping, keep LOCAL only")
    print("  claude_input.json   =>  safe to send to Claude API")
    print("\nDone.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python step1_mask.py invoice.pdf")
        sys.exit(1)
    run(sys.argv[1])
