"""
STEP 2 — Claude API extraction of 11 customs fields
Usage:  python step2_extract.py
Input:  claude_input.json   (output of step1_mask.py)
Output: extraction_result.json
"""

import json
import re
import anthropic

SYSTEM_PROMPT = """You are a customs declaration specialist.
The invoice text you receive has had sensitive personal data (company names, IBANs,
addresses, etc.) replaced with MASK_XXXXXXXX tokens. Keep these tokens as-is in
your output — do not remove or replace them.

Your task: extract exactly the following 11 fields from the invoice text.

FIELDS TO EXTRACT:
1.  product_code    — Item / line number (Item No, Pos., Nr., etc.)
2.  product_name    — Product description (Description, Bezeichnung, etc.)
3.  hs_code         — Customs tariff code (HS Code, GTiP, Tariff No, etc.)
4.  origin          — Country of origin, look specifically for "Country of Origin" label.
                      Return the value exactly as it appears, even if it is a MASK token.
5.  quantity        — Numeric quantity value
6.  unit            — Unit of measure (KG, PCS, MT, Units, etc.)
7.  net_weight      — Net weight in kg (Net Weight, Nettogewicht, etc.)
8.  gross_weight    — Gross weight in kg (Gross Weight, Bruttogewicht, etc.)
9.  invoice_no      — Invoice number, look specifically for "Invoice No:" label. 
                      Do NOT use routing numbers, bank codes, or reference numbers.
10. date            — Invoice date in DD.MM.YYYY format
11. amount          — Total invoice amount with currency

RULES:
- If a field cannot be found: return null — never guess or fabricate
- If multiple product lines exist: return one object per line item
- source_text: copy the exact original text snippet where you found the value
- confidence: float 0.0–1.0, how certain you are
- Works for any language (EN / TR / DE / ZH / AR / etc.)

OUTPUT FORMAT (return valid JSON only — no prose, no markdown fences):
{
  "items": [
    {
      "product_code":  {"value": "...", "source_text": "...", "confidence": 0.95},
      "product_name":  {"value": "...", "source_text": "...", "confidence": 0.95},
      "hs_code":       {"value": "...", "source_text": "...", "confidence": 0.95},
      "origin":        {"value": "...", "source_text": "...", "confidence": 0.95},
      "quantity":      {"value": "...", "source_text": "...", "confidence": 0.95},
      "unit":          {"value": "...", "source_text": "...", "confidence": 0.95},
      "net_weight":    {"value": "...", "source_text": "...", "confidence": 0.95},
      "gross_weight":  {"value": "...", "source_text": "...", "confidence": 0.95},
      "invoice_no":    {"value": "...", "source_text": "...", "confidence": 0.95},
      "date":          {"value": "...", "source_text": "...", "confidence": 0.95},
      "amount":        {"value": "...", "source_text": "...", "confidence": 0.95}
    }
  ]
}"""


def extract_fields(masked_text, source_file):
    client = anthropic.Anthropic()

    user_message = (
        f"Source file: {source_file}\n\n"
        f"INVOICE TEXT:\n{masked_text}"
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
        else:
            raise ValueError(f"Could not parse JSON from Claude response:\n{raw}")

    return result


def run():
    with open("claude_input.json", "r", encoding="utf-8") as f:
        claude_input = json.load(f)

    print(f"File: {claude_input['source_file']}")
    print(f"Invoice pages: {claude_input['invoice_pages']}")
    print("\nCalling Claude API...")

    result = extract_fields(
        masked_text=claude_input["masked_text"],
        source_file=claude_input["source_file"],
    )

    with open("extraction_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\nExtraction complete:")
    for i, item in enumerate(result.get("items", []), 1):
        print(f"\n  Item {i}:")
        for field, info in item.items():
            if info and info.get("value"):
                score = int(info.get("confidence", 0) * 100)
                print(f"    {field:15}  =>  {info['value']}  ({score}%)")
            else:
                print(f"    {field:15}  =>  not found")

    print("\nextraction_result.json saved.")


if __name__ == "__main__":
    run()
