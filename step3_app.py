"""
STEP 3 — Streamlit Demo App
Full 54-field T.C. Customs Declaration form
Usage: streamlit run step3_app.py
"""

import json
import os
import subprocess
import sys
import tempfile
import streamlit as st

st.set_page_config(
    page_title="Evrim — Customs Declaration AI",
    page_icon="🛃",
    layout="wide",
)

st.markdown("""
<style>
.main-title { font-size: 28px; font-weight: 700; margin-bottom: 4px; }
.sub-title { font-size: 14px; color: #888; margin-bottom: 32px; }
.form-section { font-size: 10px; font-weight: 600; color: #888; text-transform: uppercase;
    letter-spacing: 0.06em; margin: 20px 0 8px; border-bottom: 1px solid #eee; padding-bottom: 4px; }
.field-wrap { border: 1px solid #e8e8e8; border-radius: 8px; padding: 8px 12px;
    margin-bottom: 6px; background: #fafafa; min-height: 52px; }
.field-wrap.ai-high { background: #EAF3DE; border-color: #3B6D11; }
.field-wrap.ai-mid  { background: #FAEEDA; border-color: #854F0B; }
.field-wrap.ai-low  { background: #FCEBEB; border-color: #A32D2D; }
.field-num  { font-size: 9px; color: #aaa; }
.field-lbl  { font-size: 10px; color: #666; margin-bottom: 2px; }
.field-val  { font-size: 13px; font-weight: 600; min-height: 18px; }
.field-val.high { color: #1a4a0a; }
.field-val.mid  { color: #5a3000; }
.field-val.low  { color: #6a0000; }
.field-empty { font-size: 13px; color: #ccc; }
.field-src  { font-size: 9px; color: #999; margin-top: 2px; font-style: italic; }
.score { display:inline-block; font-size:9px; font-weight:700; padding:1px 6px;
    border-radius:8px; margin-left:5px; vertical-align:middle; }
.s-hi { background:#C0DD97; color:#1a4a0a; }
.s-mid{ background:#FAC775; color:#5a3000; }
.s-lo { background:#F09595; color:#6a0000; }
.stat-box { background:#f5f5f5; border-radius:8px; padding:14px; text-align:center; }
.stat-n { font-size:24px; font-weight:700; }
.stat-l { font-size:11px; color:#888; }
.upload-area { border: 2px dashed #ccc; border-radius: 12px; padding: 40px;
    text-align: center; background: #fafafa; margin-bottom: 24px; }
.legend-row { display:flex; gap:16px; font-size:11px; color:#666;
    align-items:center; margin-bottom:16px; flex-wrap:wrap; }
.ld { width:12px; height:12px; border-radius:3px; display:inline-block; margin-right:4px; vertical-align:middle; }
</style>
""", unsafe_allow_html=True)


def confidence_class(score):
    if score is None: return "", "empty", ""
    if score >= 0.90: return "ai-high", "high", "s-hi"
    if score >= 0.70: return "ai-mid",  "mid",  "s-mid"
    return "ai-low", "low", "s-lo"


def replace_masks(text, mapping):
    if not text or not mapping: return text or ""
    for k, v in mapping.items():
        text = str(text).replace(k, v)
    return text


def render_field(box_no, label, data, mapping):
    val = None
    src = None
    score = None
    if data:
        val = replace_masks(data.get("value"), mapping)
        src = replace_masks(data.get("source_text"), mapping)
        score = data.get("confidence")

    box_cls, val_cls, badge_cls = confidence_class(score)
    score_html = f'<span class="score {badge_cls}">{int(score*100)}%</span>' if score else ""

    if val:
        src_html = f'<div class="field-src">Source: {src}</div>' if src else ""
        st.markdown(f"""
        <div class="field-wrap {box_cls}">
            <div class="field-lbl"><b>{box_no}</b> — {label}{score_html}</div>
            <div class="field-val {val_cls}">{val}</div>
            {src_html}
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="field-wrap">
            <div class="field-lbl"><b>{box_no}</b> — {label}</div>
            <div class="field-empty">—</div>
        </div>""", unsafe_allow_html=True)


def run_pipeline(pdf_path):
    """Run step1 and step2 on the uploaded PDF."""
    result = subprocess.run(
        [sys.executable, "step1_mask.py", pdf_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return False, result.stderr

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    env = os.environ.copy()
    env["ANTHROPIC_API_KEY"] = api_key

    result2 = subprocess.run(
        [sys.executable, "step2_extract.py"],
        capture_output=True, text=True, env=env
    )
    if result2.returncode != 0:
        return False, result2.stderr

    return True, "OK"


def load_results():
    try:
        with open("masked_output.json", "r", encoding="utf-8") as f:
            masked = json.load(f)
        with open("extraction_result.json", "r", encoding="utf-8") as f:
            extraction = json.load(f)
        return masked.get("pii_mapping", {}), extraction.get("items", [])
    except FileNotFoundError:
        return {}, []


def render_form(mapping, items):
    # Flatten first item for field lookup
    fields = items[0] if items else {}

    # Stats
    filled = sum(1 for v in fields.values() if v and v.get("value"))
    high   = sum(1 for v in fields.values() if v and v.get("confidence", 0) >= 0.90)
    mid    = sum(1 for v in fields.values() if v and 0.70 <= v.get("confidence", 0) < 0.90)
    scores = [v.get("confidence", 0) for v in fields.values() if v and v.get("confidence")]
    avg    = int(sum(scores) / len(scores) * 100) if scores else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="stat-box"><div class="stat-n">{filled}</div><div class="stat-l">Fields filled</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat-box"><div class="stat-n" style="color:#27500A">{high}</div><div class="stat-l">High confidence</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="stat-box"><div class="stat-n" style="color:#633806">{mid}</div><div class="stat-l">Medium confidence</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="stat-box"><div class="stat-n">{avg}%</div><div class="stat-l">Avg confidence</div></div>', unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)
    st.markdown("""<div class="legend-row">
        <span><span class="ld" style="background:#EAF3DE;border:1px solid #3B6D11"></span>High confidence &gt;90%</span>
        <span><span class="ld" style="background:#FAEEDA;border:1px solid #854F0B"></span>Medium confidence 70–90%</span>
        <span><span class="ld" style="background:#FCEBEB;border:1px solid #A32D2D"></span>Low confidence &lt;70%</span>
        <span><span class="ld" style="background:#f0f0f0;border:1px solid #ccc"></span>Not found / manual entry</span>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── SECTION 1: General ────────────────────────────────────────────────────
    st.markdown('<div class="form-section">General Information</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2,1,1])
    with c1: render_field("A", "Arrival customs office", None, mapping)
    with c2: render_field("1", "Declaration type", None, mapping)
    with c3: render_field("6", "Box no", None, mapping)

    c1, c2 = st.columns([3,1])
    with c1: render_field("2", "Sender / Exporter", None, mapping)
    with c2: render_field("No", "Exporter No", None, mapping)

    c1, c2, c3 = st.columns(3)
    with c1: render_field("3", "Forms", None, mapping)
    with c2: render_field("4", "Loading lists", None, mapping)
    with c3: render_field("5", "Item count", None, mapping)

    c1, c2, c3 = st.columns(3)
    with c1: render_field("6", "Package count", None, mapping)
    with c2: render_field("7", "Reference No (Invoice No)", fields.get("invoice_no"), mapping)
    with c3: render_field("—", "Invoice date", fields.get("date"), mapping)

    c1, c2 = st.columns([3,1])
    with c1: render_field("8", "Buyer / Consignee", None, mapping)
    with c2: render_field("No", "Buyer No", None, mapping)

    c1, c2 = st.columns(2)
    with c1: render_field("9", "Financial representative", None, mapping)
    with c2: render_field("No", "Representative No", None, mapping)

    # ── SECTION 2: Trade info ─────────────────────────────────────────────────
    st.markdown('<div class="form-section">Trade & Transport Information</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1: render_field("10", "Last dispatch country", None, mapping)
    with c2: render_field("11", "Trade/Production country", None, mapping)
    with c3: render_field("12", "Value information", None, mapping)
    with c4: render_field("13", "V.P.", None, mapping)

    c1, c2 = st.columns(2)
    with c1: render_field("14", "Declarant / Representative", None, mapping)
    with c2: render_field("15", "Dispatch / Export country", None, mapping)

    c1, c2 = st.columns(2)
    with c1: render_field("16", "Country of origin", fields.get("origin"), mapping)
    with c2: render_field("17", "Destination country", None, mapping)

    c1, c2, c3 = st.columns([3,1,2])
    with c1: render_field("18", "Transport vehicle at arrival", None, mapping)
    with c2: render_field("19", "Ctr.", None, mapping)
    with c3: render_field("20", "Delivery terms", None, mapping)

    c1, c2, c3, c4 = st.columns(4)
    with c1: render_field("21", "Border transport vehicle", None, mapping)
    with c2: render_field("22", "Currency & invoice total", fields.get("amount"), mapping)
    with c3: render_field("23", "Exchange rate", None, mapping)
    with c4: render_field("24", "Transaction nature", None, mapping)

    c1, c2, c3, c4 = st.columns(4)
    with c1: render_field("25", "Border transport mode", None, mapping)
    with c2: render_field("26", "Inland transport mode", None, mapping)
    with c3: render_field("27", "Unloading place", None, mapping)
    with c4: render_field("28", "Financial & banking data", None, mapping)

    c1, c2 = st.columns(2)
    with c1: render_field("29", "Entry customs office", None, mapping)
    with c2: render_field("30", "Location of goods", None, mapping)

    # ── SECTION 3: Item details ───────────────────────────────────────────────
    st.markdown('<div class="form-section">Item Details</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([3,1,1])
    with c1: render_field("31", "Packages & description of goods (Product name)", fields.get("product_name"), mapping)
    with c2: render_field("32", "Item No (Product code)", fields.get("product_code"), mapping)
    with c3: render_field("33", "HS Code (GTiP)", fields.get("hs_code"), mapping)

    c1, c2, c3, c4 = st.columns(4)
    with c1: render_field("34", "Country of origin code", fields.get("origin"), mapping)
    with c2: render_field("35", "Gross weight (kg)", fields.get("gross_weight"), mapping)
    with c3: render_field("36", "Preference", None, mapping)
    with c4: render_field("37", "Regime", None, mapping)

    c1, c2, c3, c4 = st.columns(4)
    with c1: render_field("38", "Net weight (kg)", fields.get("net_weight"), mapping)
    with c2: render_field("39", "Quota", None, mapping)
    with c3: render_field("40", "Summary declaration", None, mapping)
    with c4: render_field("41", "Quantity", fields.get("quantity"), mapping)

    c1, c2, c3 = st.columns(3)
    with c1: render_field("41b", "Unit of measure", fields.get("unit"), mapping)
    with c2: render_field("42", "Item price", None, mapping)
    with c3: render_field("43", "V.M. code", None, mapping)

    c1, c2 = st.columns(2)
    with c1: render_field("44", "Additional info / documents / certificates", None, mapping)
    with c2: render_field("E.B.", "E.B. Code / 45 Adjustment / 46 Statistical value", None, mapping)

    # ── SECTION 4: Tax ────────────────────────────────────────────────────────
    st.markdown('<div class="form-section">Tax Calculation & Other</div>', unsafe_allow_html=True)

    render_field("47", "Tax calculation (Type / Tax base / Rate / Amount)", None, mapping)

    c1, c2 = st.columns(2)
    with c1: render_field("48", "Deferred payment", None, mapping)
    with c2: render_field("49", "Warehouse identification", None, mapping)

    c1, c2 = st.columns(2)
    with c1: render_field("50", "Principal / No", None, mapping)
    with c2: render_field("C", "Movement office", None, mapping)

    render_field("51", "Anticipated transit offices (and country)", None, mapping)

    c1, c2 = st.columns(2)
    with c1: render_field("52", "Guarantee not valid", None, mapping)
    with c2: render_field("53", "Destination office (and country)", None, mapping)

    render_field("54", "Place, date & declarant signature", None, mapping)
    render_field("J", "Arrival customs office control", None, mapping)


# ── MAIN APP ──────────────────────────────────────────────────────────────────

st.markdown('<div class="main-title">🛃 T.C. Gümrük Beyannamesi — AI Asistanı</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Fatura → Beyanname otomatik alan doldurma · Evrim Gümrük Yazılımı</div>', unsafe_allow_html=True)

mapping, items = load_results()
has_results = bool(items)

if not has_results:
    # Landing state — empty form + upload CTA
    st.markdown("""
    <div class="upload-area">
        <div style="font-size:40px;margin-bottom:12px">📄</div>
        <div style="font-size:18px;font-weight:600;margin-bottom:8px">Fatura Yükle</div>
        <div style="font-size:13px;color:#999;margin-bottom:20px">
            PDF veya Excel fatura yükleyin — AI 11 alanı otomatik doldurur
        </div>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Dosya Yükle (PDF veya Excel)",
        type=["pdf", "xlsx", "xls"],
        label_visibility="collapsed",
    )

    if uploaded:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", dir=".") as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name

        with st.spinner("Fatura işleniyor..."):
            ok, msg = run_pipeline(tmp_path)

        os.unlink(tmp_path)

        if ok:
            st.success("Tamamlandı! Alanlar dolduruldu.")
            st.rerun()
        else:
            st.error(f"Hata: {msg}")

    st.markdown("---")
    st.markdown('<div style="opacity:0.4">', unsafe_allow_html=True)
    render_form({}, [])
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # Results state — filled form
    col1, col2 = st.columns([6,1])
    with col2:
        if st.button("🔄 Yeni Fatura"):
            os.remove("masked_output.json")
            os.remove("extraction_result.json")
            st.rerun()

    render_form(mapping, items)