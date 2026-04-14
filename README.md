# Evrim Customs AI — Demo Setup

## Installation

```bash
pip install pdfplumber presidio-analyzer presidio-anonymizer streamlit anthropic
python -m spacy download en_core_web_lg
```

## Run Order

### Step 1 — PDF parse + PII masking
```bash
python step1_mask.py invoice.pdf
```
Outputs:
- `masked_output.json`  — includes PII mapping, keep LOCAL only
- `claude_input.json`   — safe to send to Claude (no PII)

### Step 2 — Claude field extraction
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python step2_extract.py
```
Output:
- `extraction_result.json`

### Step 3 — Streamlit demo
```bash
streamlit run step3_app.py
```
Open `http://localhost:8501`

## Pipeline

```
PDF upload
    |
pdfplumber  -->  raw text  (digital PDF)
    |
Presidio    -->  mask PII, save mapping  (runs LOCAL)
    |
Claude API  -->  masked text  -->  11 fields JSON
    |
Python      -->  replace masks with originals
    |
Streamlit   -->  colour-coded form + source tooltips
```

## Files

| File | Description |
|---|---|
| step1_mask.py | PDF parse + Presidio PII masking |
| step2_extract.py | Claude API field extraction |
| step3_app.py | Streamlit demo UI |
| masked_output.json | PII mapping — LOCAL only |
| claude_input.json | Claude-safe input (no PII) |
| extraction_result.json | Claude output |

## Notes
- Scanned PDFs: add OCR layer (pytesseract or Azure Document Intelligence)
- Production: deploy as standalone Flask/FastAPI service or connect via py4j bridge
- Multi-language: extend INVOICE_KEYWORDS list in step1_mask.py
