# Evrim Customs AI — Demo Setup

## Installation

```bash
pip install pdfplumber presidio-analyzer presidio-anonymizer streamlit anthropic
pip install pytesseract pdf2image
python -m spacy download en_core_web_lg
brew install tesseract poppler   # macOS only
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
pdfplumber  -->  raw text extraction
    |
Text too short? --> pytesseract OCR (scanned PDFs)
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
| step1_mask.py | PDF parse + OCR + Presidio PII masking |
| step2_extract.py | Claude API field extraction |
| step3_app.py | Streamlit demo UI |
| requirements.txt | Streamlit Cloud dependencies |
| .gitignore | Keeps JSON files out of GitHub |
| masked_output.json | PII mapping — LOCAL only, never commit |
| claude_input.json | Claude-safe input (no PII) |
| extraction_result.json | Claude output |

## PDF Support

| PDF Type | Method |
|---|---|
| Digital (ERP/Word export) | pdfplumber — fast, accurate |
| Scanned (physical document) | pytesseract OCR — automatic fallback |

## Prompt Development Plan

```
Collect 20-25 invoices
    |
Train (15-18) --> prompt iteration
Test  (5-7)   --> blind evaluation
    |
LLM as Judge --> rubric scoring
    |
Production ready prompt
```

## Notes
- Extend INVOICE_KEYWORDS in step1_mask.py for new languages/formats
- Production: deploy as standalone Flask/FastAPI service or connect via py4j bridge
- Streamlit Cloud: add ANTHROPIC_API_KEY in Settings → Secrets
