# app.py
# Streamlit port of "StyleCode Data Lab v2.9" (index.html) - layout/flow preserved as much as possible.
# Notes:
# - Row-click behavior in HTML is approximated using radio/select widgets + table highlight.
# - DATA is the same simulated structure concept as the HTML script section.
# - KPI sales pulls from stylecode-api (HTML-wrapped JSON) with regex extraction like the original.

from __future__ import annotations

import json
import re
import math
import random
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List, Tuple, Any, Optional

import pandas as pd
import streamlit as st

try:
    import requests
except Exception:
    requests = None  # Streamlit Cloud may still have it; handle gracefully.


# -----------------------------
# Page / Theme
# -----------------------------
st.set_page_config(page_title="StyleCode Data Lab v2.9", layout="wide")

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;800&display=swap');
html, body, [class*="css"]  { font-family: 'Pretendard', sans-serif; }
.small-label { font-size: 10px; font-weight: 800; color: #94a3b8; letter-spacing: 0.12em; text-transform: uppercase; }
.kpi-card { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 18px 18px; }
.kpi-title { font-size: 11px; font-weight: 900; color: #94a3b8; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 6px; }
.kpi-value { font-size: 28px; font-weight: 900; color: #0f172a; }
.card { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 18px 18px; }
.card-strong { background: white; border: 2px solid #cbd5e1; border-radius: 16px; padding: 18px 18px; }
.section-header { border-bottom: 4px solid #0f172a; padding-bottom: 10px; margin: 28px 0 18px 0; }
.section-title { font-size: 22px; font-weight: 900; color: #0f172a; letter-spacing: -0.02em; }
.section-subtitle { font-size: 13px; font-weight: 800; color: #94a3b8; }
.block-title { font-size: 16px; font-weight: 900; color: #1f2937; letter-spacing: -0.01em; margin-bottom: 8px; }
.badge { display:inline-block; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 900; }
.badge-slate { background: #f1f5f9; color: #475569; }
.badge-blue { background: #dbeafe; color: #1d4ed8; }
.badge-red { background: #fee2e2; color: #b91c1c; }
.badge-purple { background: #ede9fe; color: #7c3aed; }
.hr-gap { height: 14px; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -----------------------------
# Simulated DATA (ported conceptually from index.html)
# -----------------------------
# Minimal faithful translation of the JS DATA structure.
DATA: Dict[str, Any] = {
    "total": {
        "전체": {
            "qty": 6300,
            "sales": 772_100_000,
            "colors": {"BLACK": 3300, "WHITE": 1400, "GREY": 600, "BEIGE": 600, "NAVY": 400},
            "sizes": {"230": 400, "240": 900, "250": 2000, "260": 2000, "270": 1000},
        },
        "온라인": {
            "qty": 3500,
            "sales": 452_100_000,
            "colors": {"BLACK": 1500, "WHITE": 1000, "GREY": 600, "NAVY": 400},
            "sizes": {"230": 400, "240": 900, "250": 1200, "260": 700, "270": 300},
        },
        "오프라인": {
            "qty": 2800,
            "sales": 320_000_000,
            "colors": {"BLACK": 1800, "BEIGE": 600, "WHITE": 400},
            "sizes": {"250": 800, "260": 1000, "270": 1000},
        },
    },
    "on": {
        "온라인 전체": {
            "qty": 3500,
            "colors": {"BLACK": 1500, "WHITE": 1000, "GREY": 600, "NAVY": 400},
            "sizes": {"230": 400, "240": 900, "250": 1200, "260": 700, "270": 300},
        },
        "자사몰": {"qty": 1050, "colors": {"BLACK": 450, "WHITE": 350, "GREY": 150, "NAVY": 100}, "sizes": {"230": 100, "240": 300, "250": 350, "260": 200, "270": 100}},
        "무신사": {"qty": 875, "colors": {"BLACK": 400, "WHITE": 200, "GREY": 175, "NAVY": 100}, "sizes": {"240": 275, "250": 300, "260": 200, "270": 100}},
        "네이버 스토어": {"qty": 700, "colors": {"BLACK": 300, "WHITE": 250, "GREY": 100, "NAVY": 50}, "sizes": {"230": 150, "240": 250, "250": 200, "260": 100}},
        "29CM": {"qty": 525, "colors": {"BLACK": 200, "WHITE": 150, "GREY": 100, "NAVY": 75}, "sizes": {"230": 100, "240": 200, "250": 150, "260": 75}},
        "W컨셉": {"qty": 350, "colors": {"BLACK": 150, "WHITE": 50, "GREY": 75, "NAVY": 75}, "sizes": {"230": 50, "240": 100, "250": 150, "260": 50}},
    },
    "off": {
        "오프라인 전체": {"qty": 2800, "colors": {"BLACK": 1800, "BEIGE": 600, "WHITE": 400}, "sizes": {"250": 800, "260": 1000, "270": 1000}, "geo": {"서울": 1200, "경기": 800, "부산": 300, "대구": 200, "광주": 100, "대전": 100, "제주": 100}},
        "백화점": {"qty": 1960, "colors": {"BLACK": 1300, "BEIGE": 400, "WHITE": 260}, "sizes": {"250": 500, "260": 700, "270": 760}, "geo": {"서울": 1000, "경기": 500, "부산": 200, "대구": 100, "기타": 160}},
        "대리점": {"qty": 560, "colors": {"BLACK": 300, "BEIGE": 160, "WHITE": 100}, "sizes": {"250": 200, "260": 200, "270": 160}, "geo": {"서울": 100, "경기": 200, "부산": 100, "대구": 100, "광주": 60}},
        "직영점": {"qty": 280, "colors": {"BLACK": 200, "BEIGE": 40, "WHITE": 40}, "sizes": {"250": 100, "260": 100, "270": 80}, "geo": {"서울": 100, "경기": 100, "부산": 80}},
    },
    "cust": {
        "회원 전체": {
            "qty": 6300,
            "sales": 772_100_000,
            "colors": {"BLACK": 3000, "WHITE": 2000, "GREY": 1300},
            "sizes": {"240": 1500, "250": 2500, "260": 2300},
            "members": {"기존회원": {"qty": 4410, "sales": 540_470_000}, "신규회원": {"qty": 1890, "sales": 231_630_000}},
            "ageGender": {
                "male": {
                    "15-19": {"qty": 180, "sales": 22_000_000}, "20-24": {"qty": 520, "sales": 64_000_000}, "25-29": {"qty": 850, "sales": 104_000_000},
                    "30-34": {"qty": 920, "sales": 112_000_000}, "35-39": {"qty": 680, "sales": 83_000_000}, "40-44": {"qty": 450, "sales": 55_000_000},
                    "45-49": {"qty": 320, "sales": 39_000_000}, "50-54": {"qty": 220, "sales": 27_000_000}, "55-59": {"qty": 150, "sales": 18_000_000}, "60~": {"qty": 120, "sales": 15_000_000},
                },
                "female": {
                    "15-19": {"qty": 200, "sales": 24_000_000}, "20-24": {"qty": 680, "sales": 83_000_000}, "25-29": {"qty": 950, "sales": 116_000_000},
                    "30-34": {"qty": 780, "sales": 95_000_000}, "35-39": {"qty": 520, "sales": 64_000_000}, "40-44": {"qty": 380, "sales": 46_000_000},
                    "45-49": {"qty": 280, "sales": 34_000_000}, "50-54": {"qty": 200, "sales": 24_000_000}, "55-59": {"qty": 130, "sales": 16_000_000}, "60~": {"qty": 100, "sales": 12_000_000},
                },
            },
        },
        # HTML은 온라인/자사몰을 동일 데이터로 두었으므로 그대로 유지
        "온라인": {
            "qty": 3500, "sales": 452_100_000,
            "colors": {"BLACK": 1500, "WHITE": 1200, "GREY": 800},
            "sizes": {"240": 1000, "250": 1500, "260": 1000},
            "members": {"기존회원": {"qty": 2450, "sales": 316_470_000}, "신규회원": {"qty": 1050, "sales": 135_630_000}},
            "ageGender": {
                "male": {"15-19": {"qty": 100, "sales": 12_000_000}, "20-24": {"qty": 290, "sales": 36_000_000}, "25-29": {"qty": 470, "sales": 58_000_000}, "30-34": {"qty": 510, "sales": 62_000_000},
                         "35-39": {"qty": 380, "sales": 46_000_000}, "40-44": {"qty": 250, "sales": 30_000_000}, "45-49": {"qty": 180, "sales": 22_000_000}, "50-54": {"qty": 120, "sales": 15_000_000},
                         "55-59": {"qty": 80, "sales": 10_000_000}, "60~": {"qty": 70, "sales": 8_000_000}},
                "female": {"15-19": {"qty": 110, "sales": 13_000_000}, "20-24": {"qty": 380, "sales": 46_000_000}, "25-29": {"qty": 530, "sales": 65_000_000}, "30-34": {"qty": 430, "sales": 52_000_000},
                           "35-39": {"qty": 290, "sales": 35_000_000}, "40-44": {"qty": 210, "sales": 25_000_000}, "45-49": {"qty": 150, "sales": 18_000_000}, "50-54": {"qty": 110, "sales": 13_000_000},
                           "55-59": {"qty": 70, "sales": 8_000_000}, "60~": {"qty": 60, "sales": 7_000_000}},
            },
        },
        "자사몰": None,  # will be set to 온라인 as alias
        "오프라인": {
            "qty": 2800, "sales": 320_000_000,
            "colors": {"BLACK": 1500, "BEIGE": 800, "WHITE": 500},
            "sizes": {"250": 1000, "260": 1300, "270": 500},
            "members": {"기존회원": {"qty": 1960, "sales": 224_000_000}, "신규회원": {"qty": 840, "sales": 96_000_000}},
            "ageGender": {
                "male": {"15-19": {"qty": 80, "sales": 10_000_000}, "20-24": {"qty": 230, "sales": 28_000_000}, "25-29": {"qty": 380, "sales": 46_000_000}, "30-34": {"qty": 410, "sales": 50_000_000},
                         "35-39": {"qty": 300, "sales": 37_000_000}, "40-44": {"qty": 200, "sales": 25_000_000}, "45-49": {"qty": 140, "sales": 17_000_000}, "50-54": {"qty": 100, "sales": 12_000_000},
                         "55-59": {"qty": 70, "sales": 8_000_000}, "60~": {"qty": 50, "sales": 6_000_000}},
                "female": {"15-19": {"qty": 90, "sales": 11_000_000}, "20-24": {"qty": 300, "sales": 37_000_000}, "25-29": {"qty": 420, "sales": 51_000_000}, "30-34": {"qty": 350, "sales": 43_000_000},
                           "35-39": {"qty": 230, "sales": 29_000_000}, "40-44": {"qty": 170, "sales": 21_000_000}, "45-49": {"qty": 130, "sales": 16_000_000}, "50-54": {"qty": 90, "sales": 11_000_000},
                           "55-59": {"qty": 60, "sales": 8_000_000}, "60~": {"qty": 40, "sales": 5_000_000}},
            },
        },
        "백화점": None,  # optional: you can expand similarly if needed
        "대리점": None,
        "직영점": None,
    },
}
DATA["cust"]["자사몰"] = DATA["cust"]["온라인"]


# -----------------------------
# Helpers
# -----------------------------
API_URL = "https://stylecode-api-dpqrqczbz89gpmn2hnxx34.streamlit.app/"

AGE_LABELS = ["15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60~"]


def _fmt_won(x: Optional[float]) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "-"
    try:
        return f"{int(round(x)):,}원"
    except Exception:
        return str(x)


def _ratio(v: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return (v / total) * 100.0


def _table_from_dict(obj: Dict[str, float], total: float, colname_key: str) -> pd.DataFrame:
    rows = []
    for k, v in obj.items():
        rows.append({colname_key: k, "판매수량": int(v), "비중(%)": round(_ratio(float(v), float(total)), 1)})
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by="판매수량", ascending=False).reset_index(drop=True)
    return df


def _highlight_selected(df: pd.DataFrame, key_col: str, selected_value: str) -> pd.io.formats.style.Styler:
    def _hl(row):
        if str(row[key_col]) == str(selected_value):
            return ["background-color: #f1f5f9; font-weight: 800"] * len(row)
        return [""] * len(row)

    return df.style.apply(_hl, axis=1)


def _month_yyyy_mm(d: date) -> str:
    return f"{d.year}-{d.month:02d}"


@st.cache_data(ttl=600)
def load_brands_local() -> List[str]:
    # HTML loads ./data/brands.json; try same path in Streamlit.
    # Fallback to common brand list if file not present.
    try:
        with open("data/brands.json", "r", encoding="utf-8") as f:
            j = json.load(f)
        brands = j.get("brands")
        if isinstance(brands, list) and brands:
            return [str(x) for x in brands]
    except Exception:
        pass
    return ["I", "M", "ST", "V", "X"]


@st.cache_data(ttl=300)
def fetch_sales_amt(brand: str, month: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Mimic the HTML behavior:
    - call API_URL?brand=...&month=...
    - response might be HTML; extract JSON by regex containing sales_amt
    - return (sales_amt, error_message)
    """
    if not brand:
        return None, "brand is empty"

    if requests is None:
        return None, "requests not available"

    try:
        url = f"{API_URL}?brand={brand}&month={month}"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}"

        text = r.text

        # Try multiple patterns like the HTML logic.
        patterns = [
            r'(\{[\s\S]*"sales_amt"[\s\S]*"generated_at"[\s\S]*?\})',
            r'(\{[\s\S]*"sales_amt"[\s\S]*?\})',
            r'(\{[\s\S]*?\})',
        ]
        data = None
        for p in patterns:
            m = re.search(p, text)
            if m:
                try:
                    data = json.loads(m.group(1))
                    break
                except Exception:
                    data = None

        if not isinstance(data, dict) or "sales_amt" not in data:
            return None, "JSON parse failed / sales_amt missing"

        sales_amt = data.get("sales_amt")
        if isinstance(sales_amt, (int, float)):
            return int(sales_amt), None
        return None, "sales_amt is not numeric"

    except Exception as e:
        return None, str(e)


def make_trend_series(seed_key: str, metric: str, view: str, mode: str, selected: str) -> pd.DataFrame:
    """
    Create trend lines similar to index.html renderSingleChart().
    - view: daily/weekly/monthly
    - metric: sales/qty
    - mode: main/on/off
    - selected: selectedChannel
    Returns long-form DF: [x, series, value]
    """
    rnd = random.Random(seed_key)

    if view == "daily":
        labels = ["01-12", "01-13", "01-14", "01-15", "01-16"]
        multiplier = 1.0
    elif view == "weekly":
        labels = ["Jan W1", "Jan W2", "Jan W3", "Jan W4"]
        multiplier = 5.5
    else:
        labels = ["Oct", "Nov", "Dec", "Jan"]
        multiplier = 22.0

    def _scale(v: float, base: float) -> float:
        if metric == "sales":
            return v * base * multiplier
        return v * multiplier

    rows = []

    if mode == "main":
        channel = selected or "전체"
        if channel == "전체":
            series_defs = [
                ("ONLINE TOTAL", [320, 450, 380, 520, 480], 60000),
                ("OFFLINE TOTAL", [280, 310, 290, 410, 390], 70000),
            ]
        elif channel == "온라인":
            series_defs = [("ONLINE TOTAL", [320, 450, 380, 520, 480], 60000)]
        else:
            series_defs = [("OFFLINE TOTAL", [280, 310, 290, 410, 390], 70000)]

        for name, vals, base in series_defs:
            for x, v in zip(labels, vals[: len(labels)]):
                rows.append({"x": x, "series": name, "value": _scale(float(v), float(base))})

    else:
        is_on = mode == "on"
        if "전체" in (selected or ""):
            targets = ["자사몰", "무신사", "네이버"] if is_on else ["백화점", "대리점", "직영점"]
        else:
            targets = [selected] if selected else (["온라인 전체"] if is_on else ["오프라인 전체"])

        base_vals = [100, 150, 130, 180, 160]
        base = 55000
        for name in targets:
            for x, v in zip(labels, base_vals[: len(labels)]):
                jitter = 0.8 + rnd.random() * 0.4
                rows.append({"x": x, "series": name, "value": _scale(float(v) * jitter, float(base))})

    df = pd.DataFrame(rows)
    return df


# -----------------------------
# Header
# -----------------------------
st.markdown(
    """
<div>
  <h1 style="font-size:40px; font-weight:900; color:#0f172a; letter-spacing:-0.03em; margin-bottom:4px;">
    StyleCode Data Lab <span style="font-size:18px; font-weight:900; color:#2563eb; background:#dbeafe; padding:4px 10px; border-radius:10px; margin-left:8px;">v2.9</span>
  </h1>
  <div style="font-size:18px; font-weight:700; color:#64748b;">스타일 판매 성과 분석 통합 대시보드</div>
</div>
""",
    unsafe_allow_html=True,
)

st.write("")

# -----------------------------
# Controls (Brand / Category / StyleCode / Period) + KPI
# -----------------------------
brands = load_brands_local()
default_brand = "X" if "X" in brands else brands[0]

if "brand" not in st.session_state:
    st.session_state.brand = default_brand

if "categories" not in st.session_state:
    st.session_state.categories = ["shoes"]

if "stylecodes" not in st.session_state:
    st.session_state.stylecodes = ["SC-001"]

today = date.today()
first_day = date(today.year, today.month, 1)
last_day = date(today.year, today.month, 28)
# safe last day of month:
try:
    import calendar
    last_day = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
except Exception:
    pass

if "period" not in st.session_state:
    st.session_state.period = (first_day, last_day)

# KPI row
kpi_col, _ = st.columns([1.3, 2.7])

with kpi_col:
    st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
    st.markdown('<div class="kpi-title">Total Sales Amount</div>', unsafe_allow_html=True)

    month = _month_yyyy_mm(st.session_state.period[0])
    sales_amt, sales_err = fetch_sales_amt(st.session_state.brand, month)
    st.markdown(f'<div class="kpi-value">{_fmt_won(sales_amt)}</div>', unsafe_allow_html=True)
    if sales_err:
        st.caption(f"데이터 로드 실패: {sales_err}")
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns([1.2, 1.8, 2.4, 1.8, 1.2])

    with c1:
        st.markdown('<div class="small-label">Brand Selection</div>', unsafe_allow_html=True)
        st.session_state.brand = st.selectbox("", brands, index=brands.index(st.session_state.brand) if st.session_state.brand in brands else 0, key="brand_select")

    with c2:
        st.markdown('<div class="small-label">Category</div>', unsafe_allow_html=True)
        st.session_state.categories = st.multiselect(
            "",
            options=["shoes", "top", "bottom", "acc"],
            default=st.session_state.categories,
            format_func=lambda x: {"shoes": "FOOTWEAR", "top": "TOPS", "bottom": "PANTS", "acc": "ACCESSORIES"}.get(x, x),
            key="cat_ms",
        )

    with c3:
        st.markdown('<div class="small-label">Style Code</div>', unsafe_allow_html=True)
        st.session_state.stylecodes = st.multiselect(
            "",
            options=["SC-001", "SC-002", "SC-003", "SC-004", "SC-005"],
            default=st.session_state.stylecodes,
            format_func=lambda x: {"SC-001": "SC-AIR-01", "SC-002": "SC-RUN-05", "SC-003": "SC-CT-09", "SC-004": "SC-LIFESTYLE-X", "SC-005": "SC-PRO-CHAMP"}.get(x, x),
            key="style_ms",
        )

    with c4:
        st.markdown('<div class="small-label">Analysis Period</div>', unsafe_allow_html=True)
        start, end = st.date_input("", value=st.session_state.period, key="period_input")
        if isinstance(start, date) and isinstance(end, date):
            st.session_state.period = (start, end)

    with c5:
        st.markdown('<div class="small-label">&nbsp;</div>', unsafe_allow_html=True)
        run = st.button("조회하기", type="primary", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# In this simulated version, "조회하기" mainly triggers rerun.
if run:
    st.cache_data.clear()
    st.rerun()


# -----------------------------
# GROUP 1: ON/OFF PERFORMANCE
# -----------------------------
st.markdown(
    """
<div class="section-header" style="display:flex; justify-content:space-between; align-items:flex-end;">
  <div class="section-title">1. ON/OFF PERFORMANCE</div>
  <div class="section-subtitle">CHANNEL &amp; PRODUCT ANALYSIS</div>
</div>
""",
    unsafe_allow_html=True,
)

# ---- TOTAL Performance Detailed
st.markdown('<div class="block-title">TOTAL Performance Detailed</div>', unsafe_allow_html=True)

# Left summary table (전체/온라인/오프라인)
total_summary = pd.DataFrame(
    [
        {"채널 구분": "전체", "매출액": DATA["total"]["전체"]["sales"], "수량": DATA["total"]["전체"]["qty"], "비중(%)": 100.0},
        {"채널 구분": "온라인", "매출액": DATA["total"]["온라인"]["sales"], "수량": DATA["total"]["온라인"]["qty"], "비중(%)": round(_ratio(DATA["total"]["온라인"]["sales"], DATA["total"]["전체"]["sales"]), 1)},
        {"채널 구분": "오프라인", "매출액": DATA["total"]["오프라인"]["sales"], "수량": DATA["total"]["오프라인"]["qty"], "비중(%)": round(_ratio(DATA["total"]["오프라인"]["sales"], DATA["total"]["전체"]["sales"]), 1)},
    ]
)

if "total_selected" not in st.session_state:
    st.session_state.total_selected = "전체"

tcol1, tcol2, tcol3 = st.columns([1.1, 1.1, 1.1], gap="large")

with tcol1:
    st.markdown('<div class="card-strong">', unsafe_allow_html=True)
    st.markdown('<div class="block-title">전체 실적</div>', unsafe_allow_html=True)
    st.session_state.total_selected = st.radio(
        "선택",
        options=["전체", "온라인", "오프라인"],
        index=["전체", "온라인", "오프라인"].index(st.session_state.total_selected),
        horizontal=True,
        label_visibility="collapsed",
        key="total_radio",
    )

    df_show = total_summary.copy()
    df_show["매출액"] = df_show["매출액"].map(lambda x: f"{x:,}")
    df_show["수량"] = df_show["수량"].map(lambda x: f"{x:,}")
    sty = _highlight_selected(df_show, "채널 구분", st.session_state.total_selected)
    st.dataframe(sty, use_container_width=True, height=330)
    st.markdown("</div>", unsafe_allow_html=True)

# Total color/size by selection
sel_total = st.session_state.total_selected
total_d = DATA["total"].get(sel_total, DATA["total"]["전체"])

with tcol2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="block-title">컬러별 판매 현황 <span class="badge badge-slate">{sel_total}</span></div>', unsafe_allow_html=True)
    df = _table_from_dict(total_d["colors"], total_d["qty"], "컬러")
    st.dataframe(df, use_container_width=True, height=330)
    st.markdown("</div>", unsafe_allow_html=True)

with tcol3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="block-title">사이즈별 판매 현황 <span class="badge badge-slate">{sel_total}</span></div>', unsafe_allow_html=True)
    df = _table_from_dict(total_d["sizes"], total_d["qty"], "사이즈")
    st.dataframe(df, use_container_width=True, height=330)
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# Total trend chart
if "main_metric" not in st.session_state:
    st.session_state.main_metric = "sales"
if "main_view" not in st.session_state:
    st.session_state.main_view = "daily"

st.markdown('<div class="card">', unsafe_allow_html=True)
cA, cB = st.columns([1.4, 2.6])
with cA:
    st.markdown(f'<div class="small-label">TOTAL TREND: {sel_total}</div>', unsafe_allow_html=True)
with cB:
    cc1, cc2 = st.columns([1, 1])
    with cc1:
        st.session_state.main_metric = st.radio(
            "metric",
            options=["sales", "qty"],
            horizontal=True,
            index=["sales", "qty"].index(st.session_state.main_metric),
            format_func=lambda x: "매출" if x == "sales" else "수량",
            label_visibility="collapsed",
            key="main_metric_radio",
        )
    with cc2:
        st.session_state.main_view = st.radio(
            "view",
            options=["daily", "weekly", "monthly"],
            horizontal=True,
            index=["daily", "weekly", "monthly"].index(st.session_state.main_view),
            format_func=lambda x: {"daily": "일", "weekly": "주", "monthly": "월"}[x],
            label_visibility="collapsed",
            key="main_view_radio",
        )

trend_df = make_trend_series(
    seed_key=f"main|{st.session_state.brand}|{sel_total}|{st.session_state.main_metric}|{st.session_state.main_view}",
    metric=st.session_state.main_metric,
    view=st.session_state.main_view,
    mode="main",
    selected=sel_total,
)

# Streamlit native line chart (quick + stable)
pivot = trend_df.pivot_table(index="x", columns="series", values="value", aggfunc="sum").reset_index()
pivot = pivot.set_index("x")
st.line_chart(pivot, height=280)

st.markdown("</div>", unsafe_allow_html=True)

st.write("")
st.markdown('<div class="hr-gap"></div>', unsafe_allow_html=True)

# ---- Online Performance Detailed
st.markdown('<div class="block-title">Online Performance Detailed</div>', unsafe_allow_html=True)

if "on_selected" not in st.session_state:
    st.session_state.on_selected = "온라인 전체"
if "on_metric" not in st.session_state:
    st.session_state.on_metric = "sales"
if "on_view" not in st.session_state:
    st.session_state.on_view = "daily"

on_targets = list(DATA["on"].keys())
ocol1, ocol2, ocol3 = st.columns([1.1, 1.1, 1.1], gap="large")

with ocol1:
    st.markdown('<div class="card-strong">', unsafe_allow_html=True)
    st.markdown('<div class="block-title">온라인 채널별 실적</div>', unsafe_allow_html=True)

    st.session_state.on_selected = st.radio(
        "온라인 선택",
        options=on_targets,
        index=on_targets.index(st.session_state.on_selected) if st.session_state.on_selected in on_targets else 0,
        label_visibility="collapsed",
        key="on_radio",
    )

    # Build summary table like HTML list (with fake sales ratios for sub-channels)
    # The HTML's online list includes sales numbers. Here we approximate by allocating from total online sales.
    online_total_sales = DATA["total"]["온라인"]["sales"]
    alloc = {
        "온라인 전체": online_total_sales,
        "자사몰": int(online_total_sales * 0.30),
        "무신사": int(online_total_sales * 0.25),
        "네이버 스토어": int(online_total_sales * 0.20),
        "29CM": int(online_total_sales * 0.15),
        "W컨셉": int(online_total_sales * 0.10),
    }
    rows = []
    for k in on_targets:
        qty = DATA["on"][k]["qty"]
        sales = alloc.get(k, int(online_total_sales * 0.05))
        ratio = round(_ratio(sales, online_total_sales), 1) if k != "온라인 전체" else 100.0
        rows.append({"채널명": k, "매출액": f"{sales:,}", "수량": f"{qty:,}", "비중(%)": ratio})
    df_on_sum = pd.DataFrame(rows)
    st.dataframe(_highlight_selected(df_on_sum, "채널명", st.session_state.on_selected), use_container_width=True, height=330)
    st.markdown("</div>", unsafe_allow_html=True)

on_d = DATA["on"].get(st.session_state.on_selected, DATA["on"]["온라인 전체"])

with ocol2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="block-title">컬러별 판매 현황 <span class="badge badge-blue">{st.session_state.on_selected}</span></div>', unsafe_allow_html=True)
    df = _table_from_dict(on_d["colors"], on_d["qty"], "컬러")
    st.dataframe(df, use_container_width=True, height=330)
    st.markdown("</div>", unsafe_allow_html=True)

with ocol3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="block-title">사이즈별 판매 현황 <span class="badge badge-blue">{st.session_state.on_selected}</span></div>', unsafe_allow_html=True)
    df = _table_from_dict(on_d["sizes"], on_d["qty"], "사이즈")
    st.dataframe(df, use_container_width=True, height=330)
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")

st.markdown('<div class="card">', unsafe_allow_html=True)
cA, cB = st.columns([1.4, 2.6])
with cA:
    st.markdown(f'<div class="small-label">ONLINE TREND: {st.session_state.on_selected}</div>', unsafe_allow_html=True)
with cB:
    cc1, cc2 = st.columns([1, 1])
    with cc1:
        st.session_state.on_metric = st.radio(
            "on_metric",
            options=["sales", "qty"],
            horizontal=True,
            index=["sales", "qty"].index(st.session_state.on_metric),
            format_func=lambda x: "매출" if x == "sales" else "수량",
            label_visibility="collapsed",
            key="on_metric_radio",
        )
    with cc2:
        st.session_state.on_view = st.radio(
            "on_view",
            options=["daily", "weekly", "monthly"],
            horizontal=True,
            index=["daily", "weekly", "monthly"].index(st.session_state.on_view),
            format_func=lambda x: {"daily": "일", "weekly": "주", "monthly": "월"}[x],
            label_visibility="collapsed",
            key="on_view_radio",
        )

trend_df = make_trend_series(
    seed_key=f"on|{st.session_state.brand}|{st.session_state.on_selected}|{st.session_state.on_metric}|{st.session_state.on_view}",
    metric=st.session_state.on_metric,
    view=st.session_state.on_view,
    mode="on",
    selected=st.session_state.on_selected,
)
pivot = trend_df.pivot_table(index="x", columns="series", values="value", aggfunc="sum").reset_index().set_index("x")
st.line_chart(pivot, height=280)
st.markdown("</div>", unsafe_allow_html=True)

st.write("")
st.markdown('<div class="hr-gap"></div>', unsafe_allow_html=True)

# ---- Offline Performance Detailed
st.markdown('<div class="block-title">Offline Performance Detailed</div>', unsafe_allow_html=True)

if "off_selected" not in st.session_state:
    st.session_state.off_selected = "오프라인 전체"
if "off_metric" not in st.session_state:
    st.session_state.off_metric = "sales"
if "off_view" not in st.session_state:
    st.session_state.off_view = "daily"

off_targets = list(DATA["off"].keys())
fcol1, fcol2, fcol3 = st.columns([1.1, 1.1, 1.1], gap="large")

with fcol1:
    st.markdown('<div class="card-strong">', unsafe_allow_html=True)
    st.markdown('<div class="block-title">오프라인 채널별 실적</div>', unsafe_allow_html=True)

    st.session_state.off_selected = st.radio(
        "오프라인 선택",
        options=off_targets,
        index=off_targets.index(st.session_state.off_selected) if st.session_state.off_selected in off_targets else 0,
        label_visibility="collapsed",
        key="off_radio",
    )

    offline_total_sales = DATA["total"]["오프라인"]["sales"]
    alloc = {
        "오프라인 전체": offline_total_sales,
        "백화점": int(offline_total_sales * 0.70),
        "대리점": int(offline_total_sales * 0.20),
        "직영점": int(offline_total_sales * 0.10),
    }
    rows = []
    for k in off_targets:
        qty = DATA["off"][k]["qty"]
        sales = alloc.get(k, int(offline_total_sales * 0.05))
        ratio = round(_ratio(sales, offline_total_sales), 1) if k != "오프라인 전체" else 100.0
        rows.append({"채널명": k, "매출액": f"{sales:,}", "수량": f"{qty:,}", "비중(%)": ratio})
    df_off_sum = pd.DataFrame(rows)
    st.dataframe(_highlight_selected(df_off_sum, "채널명", st.session_state.off_selected), use_container_width=True, height=330)
    st.markdown("</div>", unsafe_allow_html=True)

off_d = DATA["off"].get(st.session_state.off_selected, DATA["off"]["오프라인 전체"])

with fcol2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="block-title">컬러별 판매 현황 <span class="badge badge-red">{st.session_state.off_selected}</span></div>', unsafe_allow_html=True)
    df = _table_from_dict(off_d["colors"], off_d["qty"], "컬러")
    st.dataframe(df, use_container_width=True, height=330)
    st.markdown("</div>", unsafe_allow_html=True)

with fcol3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="block-title">사이즈별 판매 현황 <span class="badge badge-red">{st.session_state.off_selected}</span></div>', unsafe_allow_html=True)
    df = _table_from_dict(off_d["sizes"], off_d["qty"], "사이즈")
    st.dataframe(df, use_container_width=True, height=330)
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")

st.markdown('<div class="card">', unsafe_allow_html=True)
cA, cB = st.columns([1.4, 2.6])
with cA:
    st.markdown(f'<div class="small-label">OFFLINE TREND: {st.session_state.off_selected}</div>', unsafe_allow_html=True)
with cB:
    cc1, cc2 = st.columns([1, 1])
    with cc1:
        st.session_state.off_metric = st.radio(
            "off_metric",
            options=["sales", "qty"],
            horizontal=True,
            index=["sales", "qty"].index(st.session_state.off_metric),
            format_func=lambda x: "매출" if x == "sales" else "수량",
            label_visibility="collapsed",
            key="off_metric_radio",
        )
    with cc2:
        st.session_state.off_view = st.radio(
            "off_view",
            options=["daily", "weekly", "monthly"],
            horizontal=True,
            index=["daily", "weekly", "monthly"].index(st.session_state.off_view),
            format_func=lambda x: {"daily": "일", "weekly": "주", "monthly": "월"}[x],
            label_visibility="collapsed",
            key="off_view_radio",
        )

trend_df = make_trend_series(
    seed_key=f"off|{st.session_state.brand}|{st.session_state.off_selected}|{st.session_state.off_metric}|{st.session_state.off_view}",
    metric=st.session_state.off_metric,
    view=st.session_state.off_view,
    mode="off",
    selected=st.session_state.off_selected,
)
pivot = trend_df.pivot_table(index="x", columns="series", values="value", aggfunc="sum").reset_index().set_index("x")
st.line_chart(pivot, height=280)
st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# Offline: Shop TOP 15 + Region table (HTML uses random; we keep deterministic random)
shop_col, region_col = st.columns([1, 1], gap="large")

def make_shop_rank(seed_key: str, label_prefix: str) -> pd.DataFrame:
    rnd = random.Random(seed_key)
    rows = []
    for i in range(1, 16):
        sales = rnd.randint(2_000_000, 7_000_000)
        rows.append({"순위": i, "매장명": f"{label_prefix} 매장 {i}호점", "매출액": f"{sales:,}원", "수량": int(sales / 80_000)})
    return pd.DataFrame(rows)

with shop_col:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="block-title">오프라인 매장 실적 TOP 15 <span class="badge badge-slate">{st.session_state.off_selected}</span></div>', unsafe_allow_html=True)
    df = make_shop_rank(f"shop|{st.session_state.off_selected}|{st.session_state.brand}", st.session_state.off_selected.replace(" 전체", ""))
    st.dataframe(df, use_container_width=True, height=360)
    st.markdown("</div>", unsafe_allow_html=True)

with region_col:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="block-title">전국 지역별 매출 분포 <span class="badge badge-slate">{st.session_state.off_selected}</span></div>', unsafe_allow_html=True)
    geo = off_d.get("geo", {})
    rows = []
    for region, qty in geo.items():
        sales = int(qty) * 75_000
        rows.append({"Region": region, "매출액": f"{sales:,}원", "수량": f"{int(qty):,}", "비중(%)": round(_ratio(float(qty), float(off_d["qty"])), 1)})
    df = pd.DataFrame(rows).sort_values("비중(%)", ascending=False).reset_index(drop=True)
    st.dataframe(df, use_container_width=True, height=360)
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# GROUP 2: CUSTOMER ANALYSIS
# -----------------------------
st.markdown(
    """
<div class="section-header">
  <div class="section-title">2. CUSTOMER ANALYSIS</div>
</div>
""",
    unsafe_allow_html=True,
)

cust_targets = ["회원 전체", "온라인", "자사몰", "오프라인"]  # HTML 리스트 핵심 선택지
if "cust_selected" not in st.session_state:
    st.session_state.cust_selected = "회원 전체"
if "age_metric" not in st.session_state:
    st.session_state.age_metric = "sales"

ccol1, ccol2, ccol3 = st.columns([1.1, 1.1, 1.1], gap="large")

with ccol1:
    st.markdown('<div class="card-strong">', unsafe_allow_html=True)
    st.markdown('<div class="block-title">회원 채널별 실적</div>', unsafe_allow_html=True)

    st.session_state.cust_selected = st.radio(
        "회원 선택",
        options=cust_targets,
        index=cust_targets.index(st.session_state.cust_selected) if st.session_state.cust_selected in cust_targets else 0,
        label_visibility="collapsed",
        key="cust_radio",
    )

    # Build a simple summary table similar to HTML 3-depth feel
    # (회원 전체 -> 온라인 -> 자사몰, 회원 전체 -> 오프라인)
    d_all = DATA["cust"]["회원 전체"]
    d_on = DATA["cust"]["온라인"]
    d_off = DATA["cust"]["오프라인"]
    df = pd.DataFrame(
        [
            {"채널 구분": "회원 전체", "매출액": f'{d_all["sales"]:,}', "수량": f'{d_all["qty"]:,}', "비중(%)": 100.0},
            {"채널 구분": "└ 온라인", "매출액": f'{d_on["sales"]:,}', "수량": f'{d_on["qty"]:,}', "비중(%)": round(_ratio(d_on["sales"], d_all["sales"]), 1)},
            {"채널 구분": "   └ 자사몰", "매출액": f'{d_on["sales"]:,}', "수량": f'{d_on["qty"]:,}', "비중(%)": 100.0},
            {"채널 구분": "└ 오프라인", "매출액": f'{d_off["sales"]:,}', "수량": f'{d_off["qty"]:,}', "비중(%)": round(_ratio(d_off["sales"], d_all["sales"]), 1)},
        ]
    )
    # Highlight approximate: match selected to rows
    key_map = {
        "회원 전체": "회원 전체",
        "온라인": "└ 온라인",
        "자사몰": "   └ 자사몰",
        "오프라인": "└ 오프라인",
    }
    st.dataframe(_highlight_selected(df, "채널 구분", key_map.get(st.session_state.cust_selected, "회원 전체")), use_container_width=True, height=330)
    st.markdown("</div>", unsafe_allow_html=True)

cust_d = DATA["cust"].get(st.session_state.cust_selected, DATA["cust"]["회원 전체"])

with ccol2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="block-title">컬러별 판매 현황 <span class="badge badge-purple">{st.session_state.cust_selected}</span></div>', unsafe_allow_html=True)
    df = _table_from_dict(cust_d["colors"], cust_d["qty"], "컬러")
    st.dataframe(df, use_container_width=True, height=330)
    st.markdown("</div>", unsafe_allow_html=True)

with ccol3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="block-title">사이즈별 판매 현황 <span class="badge badge-purple">{st.session_state.cust_selected}</span></div>', unsafe_allow_html=True)
    df = _table_from_dict(cust_d["sizes"], cust_d["qty"], "사이즈")
    st.dataframe(df, use_container_width=True, height=330)
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")

mcol1, mcol2 = st.columns([1.05, 1.95], gap="large")

with mcol1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    # HTML: title "기존/신규 회원" + badge
    badge_name = st.session_state.cust_selected if ("전체" in st.session_state.cust_selected or st.session_state.cust_selected == "자사몰") else f"{st.session_state.cust_selected} 전체"
    st.markdown(f'<div class="block-title">기존/신규 회원 <span class="badge badge-purple">{badge_name}</span></div>', unsafe_allow_html=True)

    members = cust_d["members"]
    total_sales = cust_d["sales"]
    total_qty = cust_d["qty"]
    rows = [{"회원 구분": st.session_state.cust_selected, "매출액": f"{total_sales:,}", "수량": f"{total_qty:,}", "비중(%)": 100.0}]
    for k, v in members.items():
        rows.append({"회원 구분": k, "매출액": f'{v["sales"]:,}', "수량": f'{v["qty"]:,}', "비중(%)": round(_ratio(v["qty"], total_qty), 1)})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, height=360)
    st.markdown("</div>", unsafe_allow_html=True)

with mcol2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="block-title">성별/연령대 분석</div>', unsafe_allow_html=True)
    st.session_state.age_metric = st.radio(
        "age_metric",
        options=["sales", "qty"],
        horizontal=True,
        index=["sales", "qty"].index(st.session_state.age_metric),
        format_func=lambda x: "매출액" if x == "sales" else "판매량",
        label_visibility="collapsed",
        key="age_metric_radio",
    )

    age_gender = cust_d.get("ageGender", {})
    male = age_gender.get("male", {})
    female = age_gender.get("female", {})

    x = AGE_LABELS
    male_vals = [(male.get(a, {"qty": 0, "sales": 0})["sales" if st.session_state.age_metric == "sales" else "qty"]) for a in x]
    female_vals = [(female.get(a, {"qty": 0, "sales": 0})["sales" if st.session_state.age_metric == "sales" else "qty"]) for a in x]

    df_age = pd.DataFrame({"연령대": x, "남성": male_vals, "여성": female_vals}).set_index("연령대")
    st.bar_chart(df_age, height=360)
    st.markdown("</div>", unsafe_allow_html=True)

# Footer spacing
st.write("")
st.caption("Ported layout from index.html (StyleCode Data Lab v2.9).")


