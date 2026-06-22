import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import matplotlib.font_manager as fm
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import scipy.stats as stats
import os

st.set_page_config(page_title="서울시 치안 데이터 대시보드", layout="wide")



# --- 한글 폰트 설정 (Streamlit Cloud 대응) ---
@st.cache_resource
def set_korean_font():
    # 1. 서버 환경(Linux)인 경우 나눔 폰트 설치
    if os.name != 'nt':  # Windows가 아니면 (즉, 리눅스 서버이면)
        os.system('apt-get update -qq')
        os.system('apt-get install -y fonts-nanum -qq')
        font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
        if os.path.exists(font_path):
            font_prop = fm.FontProperties(fname=font_path)
            plt.rc('font', family=font_prop.get_name())
    # 2. 로컬 환경(Windows)인 경우
    else:
        plt.rc('font', family='Malgun Gothic')
    
    plt.rcParams['axes.unicode_minus'] = False # 마이너스 기호 깨짐 방지

set_korean_font()

# 현재 페이지 상태 초기화 (기본값: Home)
if 'page' not in st.session_state:
    st.session_state.page = 'Home'

# 페이지 변경 함수
def set_page(page_name):
    st.session_state.page = page_name

st.markdown("""
<style>
[data-testid="stSidebar"] {
    min-width: 200px !important;
    max-width: 200px !important;
    background-color: #f5f5f5 !important;
    border-right: 2px solid #f5f5f5 !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 0.8rem; }
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,[data-testid="stSidebar"] span { color: #000000 !important; }

[data-testid="stSidebar"] div.stButton > button {
    width: 100% !important; 
    background: transparent !important; 
    border: none !important;
    border-radius: 20px !important; 
    display: flex !important;
    justify-content: flex-start !important; 
    text-align: left !important; 
    padding: 2px 12px !important;
    color: #a8b8d0 !important;
    transition: all 0.15s ease !important; 
    margin-bottom: 0px !important;
}

[data-testid="stSidebar"] div.stButton > button p {
    font-size: 0.78rem !important;
    font-weight: 550 !important;
    text-align: left !important; 
    letter-spacing: -0.02em !important;
}

[data-testid="stSidebar"] div.stButton > button:hover {
    background: rgba(255,255,255,0.08) !important; color: #ffffff !important;
}

[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
    background: #dcdcdc !important; 
    border-left: 3px solid #d3d3d3 !important; 
    padding-left: 15px !important;
}

[data-testid="stSidebar"] div.stButton > button[kind="primary"] p {
    font-weight: 750 !important;
}

[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.1) !important; margin: 0.6rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# # ── 파일 경로 ─────────────────────────────────────────────────────────────────
# CCTV_FILE      = r"C:\Users\KDT29\Desktop\cctv\DATA\서울시 자치구 CCTV 설치현황.xlsx"
# POP_FILE       = r"C:\Users\KDT29\Desktop\cctv\DATA\등록인구_20260512150716.xlsx"
# CRIME_CSV      = r"C:\Users\KDT29\Desktop\cctv\DATA\5대+범죄+발생현황_20260512140024.csv"
# LOC_FILE       = r"C:\Users\KDT29\Desktop\cctv\DATA\5대+범죄+발생장소별+현황.xlsx"
# CRIME_NEW_FILE = r"C:\Users\KDT29\Desktop\cctv\DATA\crime(2015-2024).xlsx"
# UTIL_FILE      = r"C:\Users\KDT29\Desktop\cctv\DATA\util_clean.xlsx"
# ADULT_FILE     = r"C:\Users\KDT29\Desktop\cctv\DATA\서울시 유흥주점영업 인허가 정보.xlsx"
CCTV_FILE    = "./DATA/서울시 자치구 CCTV 설치현황.xlsx"
CRIME_TYPES   = ["살인", "강도", "강간·강제추행", "절도", "폭력"]
CRIME_OFFSETS = [2, 4, 6, 8, 10]
POP_FILE   = "./DATA/등록인구_20260512150716.xlsx"
CRIME_CSV  = "./DATA/5대+범죄+발생현황_20260512140024.csv"
LOC_FILE   = "./DATA/5대+범죄+발생장소별+현황.xlsx"
UTIL_FILE  = "./DATA/util_clean.xlsx"
ADULT_FILE = "./DATA/서울시 유흥주점영업 인허가 정보.xlsx"
# ════════════════════════════════════════════════════════════════════════════════
# 데이터 로딩
# ════════════════════════════════════════════════════════════════════════════════
@st.cache_data
def load_cctv():
    raw = pd.read_excel(CCTV_FILE, header=2)
    raw = raw.drop(columns=["Unnamed: 0"], errors="ignore")
    raw = raw.iloc[:-2]
    raw = raw[raw["구분"] != "계"].copy()
    year_cols = [c for c in raw.columns if str(c).endswith("년")]
    raw[year_cols] = raw[year_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
    return raw.set_index("순번")

@st.cache_data
def load_crime_csv():
    return pd.read_csv(CRIME_CSV, encoding="utf-8")

@st.cache_data
def load_population():
    return pd.read_excel(POP_FILE)

# @st.cache_data
# def load_population_trend():
#     return pd.read_excel(POP_TREND_FILE)

@st.cache_data
def load_crime_loc():
    return pd.read_excel(LOC_FILE)

@st.cache_data
def load_cctv_new():
    cctv  = load_cctv()
    years = [f"{y}년" for y in range(2015, 2025)]
    vals  = cctv[years].sum().values
    return pd.DataFrame({"연도": [str(y) for y in range(2015, 2025)],
                         "CCTV누적": vals.astype(float)})

@st.cache_data
def load_util():
    return pd.read_excel(UTIL_FILE)

@st.cache_data
def load_adult():
    raw   = pd.read_excel(ADULT_FILE)
    adult = raw[raw['영업상태명'] == '영업/정상'].copy()
    def extract_gu(row):
        addr = row['도로명주소'] if pd.notna(row['도로명주소']) else row['지번주소']
        if pd.isna(addr):
            return None
        parts = str(addr).split()
        return parts[1] if len(parts) >= 2 else None
    adult['지역구'] = adult.apply(extract_gu, axis=1)
    gu_counts = adult['지역구'].value_counts().reset_index()
    gu_counts.columns = ['자치구', '유흥업소수']
    return gu_counts

def _get_total_row(crime_raw):
    row = crime_raw[(crime_raw["자치구별(1)"] == "합계") & (crime_raw["자치구별(2)"] == "소계")]
    if row.empty:
        row = crime_raw[crime_raw["자치구별(1)"] == "합계"].iloc[[0]]
    return row

@st.cache_data
def build_crime_yearly():
    crime_raw = load_crime_csv()
    row_sum   = _get_total_row(crime_raw)
    rows = []
    for yr in range(2015, 2025):
        year_str = str(yr)
        for crime, offset in zip(CRIME_TYPES, CRIME_OFFSETS):
            col = f"{year_str}.{offset}"
            if col in crime_raw.columns:
                val = pd.to_numeric(str(row_sum[col].values[0]).replace(",", ""), errors="coerce")
                rows.append({"연도": year_str, "유형": crime, "건수": int(val) if pd.notna(val) else 0})
    return pd.DataFrame(rows)

@st.cache_data
def build_df_final():
    cctv      = load_cctv()
    crime_raw = load_crime_csv()
    pop_raw   = load_population()

    pop_24 = pop_raw[pop_raw["동별(1)"].isna() & pop_raw["동별(2)"].notna()][
        ["동별(2)", "2024.1"]].copy()
        # ["동별(2)", "2024 4/4.1"]].copy()
    pop_24.columns = ["자치구", "인구수"]
    pop_24["자치구"] = pop_24["자치구"].astype(str).str.strip()
    pop_24["인구수"] = pd.to_numeric(pop_24["인구수"].astype(str).str.replace(",", ""), errors="coerce")
    pop_24 = pop_24.dropna(subset=["인구수"])
    pop_24["인구수"] = pop_24["인구수"].astype(int)

    cctv_24 = cctv[["구분", "2024년"]].rename(columns={"구분": "자치구", "2024년": "CCTV수"}).copy()
    cctv_24["CCTV수"] = pd.to_numeric(cctv_24["CCTV수"], errors="coerce")

    crime_filt = crime_raw[[c for c in crime_raw.columns if "." not in str(c)]].copy()
    crime_filt = crime_filt.drop(0).rename(columns={"자치구별(2)": "자치구"})
    if "자치구별(1)" in crime_filt.columns:
        crime_filt = crime_filt.drop(columns=["자치구별(1)"])
    crime_24 = crime_filt[["자치구", "2024"]].rename(columns={"2024": "발생건수"}).copy()
    crime_24["발생건수"] = pd.to_numeric(crime_24["발생건수"], errors="coerce")

    df = pd.merge(pop_24, cctv_24, on="자치구")
    df = pd.merge(df, crime_24, on="자치구")
    df = df.dropna()
    df["범죄율"]        = (df["발생건수"] / df["인구수"]) * 100_000
    df["CCTV_밀도"]     = (df["CCTV수"]   / df["인구수"]) * 10_000
    df["CCTV당_범죄수"] = df["발생건수"]  / df["CCTV수"]
    df.index = range(1, len(df) + 1)
    return df

@st.cache_data
def build_crime_trend():
    cctv      = load_cctv()
    crime_raw = load_crime_csv()
    pop_raw   = load_population()
    row_sum   = _get_total_row(crime_raw)
    rows = []
    for year in range(2015, 2025):
        yr = str(year)
        try:
            pop_total = pd.to_numeric(
                str(pop_raw.loc[pop_raw["동별(2)"] == "소계", f"{yr}.1"].values[0]).replace(",", ""),
                errors="coerce")
        except Exception:
            continue
        cctv_col         = f"{yr}년"
        cctv_sum         = cctv[cctv_col].sum() if cctv_col in cctv.columns else np.nan
        total_crime      = pd.to_numeric(str(row_sum[yr].values[0]).replace(",", ""), errors="coerce")
        crime_rate_total = (total_crime / pop_total) * 100_000
        type_rates = []
        for offset in CRIME_OFFSETS:
            col = f"{yr}.{offset}"
            val = pd.to_numeric(str(row_sum[col].values[0]).replace(",", ""), errors="coerce")
            type_rates.append((val / pop_total) * 100_000)
        rows.append([yr, cctv_sum, pop_total, total_crime, crime_rate_total] + type_rates)
    df = pd.DataFrame(rows, columns=["연도","CCTV수량","인구수","총범죄수","총범죄율"] + CRIME_TYPES)
    df["연도"] = df["연도"].astype(str)
    return df

# ── 데이터 로드 ───────────────────────────────────────────────────────────────
df_final     = build_df_final()
df_trend     = build_crime_trend()
cctv_raw     = load_cctv()
df_all_crime = build_crime_yearly()
df_10yr_base = load_cctv_new()
df_util      = load_util()
df_adult     = load_adult()

df_final = df_final.merge(df_adult, on='자치구', how='left')
df_final['유흥업소수'] = df_final['유흥업소수'].fillna(0).astype(int)

# --- 사이드바 (홈으로 돌아가기 기능 추가) ---
if st.session_state.page != 'Home':
    if st.sidebar.button("🏠 홈 화면으로 이동"):
        set_page('Home')

# ════════════════════════════════════════════════════════════════════════════════
# 사이드바
# ════════════════════════════════════════════════════════════════════════════════
CHAPTERS = {
    "ch1": "CH1.  지역구별 분석",
    "ch2": "CH2.  범죄 유형별 분석",
    "ch3": "CH3.  연도별 추세 분석",
    "ch4": "CH4.  CCTV 투자 우선순위",
}
if "page" not in st.session_state:
    st.session_state.page = "ch1"

with st.sidebar:
    st.markdown(
        '<p style="font-size:0.8rem;font-weight:700;letter-spacing:0.12em;'
        'text-transform:uppercase;color:#6b7fa3;margin-bottom:6px;">분석 목차</p>',
        unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    for key, label in CHAPTERS.items():
        btn_type = "primary" if st.session_state.page == key else "secondary"
        if st.button(label, key=f"nav_{key}", type=btn_type, use_container_width=True):
            st.session_state.page = key
            st.rerun()
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size:0.65rem;color:#4a5a72;line-height:1.6;margin-top:4px;">'
        '서울시 25개 자치구<br>데이터 기준: 2015~2024</p>',
        unsafe_allow_html=True)

page = st.session_state.page


# ════════════════════════════════════════════════════════════════════════════════
# 홈 화면
# ════════════════════════════════════════════════════════════════════════════════

if st.session_state.page == 'Home':

    # ── 홈 전용 CSS ──────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    /* 흰 배경 */
    section[data-testid="stMain"] > div:first-child {
        background: #ffffff !important;
        min-height: 100vh;
        padding: 0 !important;
    }

    /* 전체 텍스트 기본 다크 */
    section[data-testid="stMain"] p,
    section[data-testid="stMain"] span,
    section[data-testid="stMain"] label {
        color: #1a1a2e !important;
    }

    /* ── 메인 wrapper : 사이드바(200px) + 추가 여백 ── */
    .home-wrap {
        max-width: 1060px;
        margin: 0 auto 0 60px;
        padding: 52px 40px 80px 0;
    }

    /* ── 히어로 ── */
    .hero-badge {
        display: inline-block;
        background: #eef4ff;
        border: 1px solid #b6ccf7;
        border-radius: 50px;
        padding: 5px 16px;
        font-size: 0.71rem;
        letter-spacing: 0.11em;
        text-transform: uppercase;
        color: #2563eb !important;
        margin-bottom: 20px;
        font-weight: 600;
    }
    .hero-title {
        font-size: 2.7rem;
        font-weight: 800;
        line-height: 1.18;
        color: #111827 !important;
        margin: 0 0 10px;
        letter-spacing: -0.03em;
    }
    .hero-title span {
        color: #2563eb !important;
    }
    .hero-sub {
        font-size: 1.0rem;
        color: #4b5563 !important;
        margin: 0 0 44px;
        line-height: 1.75;
        max-width: 600px;
    }

    /* ── 구분선 ── */
    .home-divider {
        border: none;
        border-top: 1px solid #e5e7eb;
        margin: 0 0 38px;
    }

    /* ── KPI 카드 ── */
    .kpi-row {
        display: flex;
        gap: 14px;
        margin-bottom: 48px;
        flex-wrap: wrap;
    }
    .kpi-card {
        flex: 1;
        min-width: 160px;
        background: #f8faff;
        border: 1px solid #dde6f8;
        border-radius: 14px;
        padding: 18px 20px 16px;
    }
    .kpi-label {
        font-size: 0.69rem;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        color: #6b7280 !important;
        margin-bottom: 6px;
        font-weight: 600;
    }
    .kpi-value {
        font-size: 1.75rem;
        font-weight: 800;
        color: #111827 !important;
        letter-spacing: -0.04em;
        line-height: 1;
    }
    .kpi-value span {
        font-size: 0.82rem;
        font-weight: 500;
        color: #2563eb !important;
        margin-left: 5px;
        letter-spacing: 0;
    }

    /* ── 챕터 섹션 타이틀 ── */
    .chapter-section-title {
        font-size: 0.69rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #9ca3af !important;
        margin-bottom: 16px;
        font-weight: 700;
    }

    /* ── 챕터 카드 ── */
    .ch-card {
        background: #ffffff;
        border: 1.5px solid #e5e7eb;
        border-radius: 16px;
        padding: 24px 24px 18px;
        position: relative;
        overflow: hidden;
        transition: border-color 0.18s, box-shadow 0.18s;
        box-sizing: border-box;
    }
    .ch-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 4px;
    }
    .ch-card.c1::before { background: #2563eb; }
    .ch-card.c2::before { background: #dc2626; }
    .ch-card.c3::before { background: #16a34a; }
    .ch-card.c4::before { background: #d97706; }

    .ch-card:hover {
        border-color: #c7d6f7;
        box-shadow: 0 4px 18px rgba(37,99,235,0.08);
    }

    .ch-num {
        font-size: 0.67rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        font-weight: 700;
        margin-bottom: 7px;
    }
    .ch-card.c1 .ch-num { color: #2563eb; }
    .ch-card.c2 .ch-num { color: #dc2626; }
    .ch-card.c3 .ch-num { color: #16a34a; }
    .ch-card.c4 .ch-num { color: #d97706; }

    .ch-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #111827 !important;
        margin-bottom: 9px;
        letter-spacing: -0.02em;
    }
    .ch-desc {
        font-size: 0.81rem;
        color: #6b7280 !important;
        line-height: 1.65;
        margin-bottom: 14px;
    }
    .ch-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
        margin-bottom: 4px;
    }
    .ch-tag {
        border-radius: 50px;
        padding: 3px 10px;
        font-size: 0.67rem;
        font-weight: 600;
    }
    .ch-card.c1 .ch-tag { background:#eef4ff; color:#2563eb !important; }
    .ch-card.c2 .ch-tag { background:#fef2f2; color:#dc2626 !important; }
    .ch-card.c3 .ch-tag { background:#f0fdf4; color:#16a34a !important; }
    .ch-card.c4 .ch-tag { background:#fffbeb; color:#d97706 !important; }

    /* ── 이동 버튼 공통 ── */
    div[data-testid="stColumns"] div.stButton > button {
        border-radius: 8px !important;
        font-size: 0.83rem !important;
        font-weight: 700 !important;
        padding: 9px 18px !important;
        margin-top: 10px !important;
        width: 100% !important;
        border: none !important;
        color: #ffffff !important;
        transition: filter 0.15s, transform 0.1s !important;
        letter-spacing: 0.01em !important;
    }
    div[data-testid="stColumns"] div.stButton > button:hover {
        filter: brightness(1.12) !important;
        transform: translateY(-1px) !important;
    }
    div[data-testid="stColumns"] div.stButton > button:active {
        transform: scale(0.97) !important;
    }
    /* 챕터별 버튼 배경색 */
    div[data-testid="stButton-home_btn_ch1"] > button { background: #2563eb !important; }
    div[data-testid="stButton-home_btn_ch2"] > button { background: #dc2626 !important; }
    div[data-testid="stButton-home_btn_ch3"] > button { background: #16a34a !important; }
    div[data-testid="stButton-home_btn_ch4"] > button { background: #d97706 !important; }

    /* ── 정보 띠 ── */
    .info-bar {
        display: flex;
        gap: 0;
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        overflow: hidden;
        margin-bottom: 48px;
    }
    .info-item {
        flex: 1;
        padding: 16px 20px;
        border-right: 1px solid #e5e7eb;
    }
    .info-item:last-child { border-right: none; }
    .info-item-label {
        font-size: 0.67rem;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        color: #9ca3af !important;
        margin-bottom: 4px;
        font-weight: 600;
    }
    .info-item-val {
        font-size: 0.86rem;
        font-weight: 700;
        color: #111827 !important;
    }

    /* ── 푸터 ── */
    .home-footer {
        text-align: center;
        font-size: 0.71rem;
        color: #9ca3af !important;
        padding-top: 20px;
        border-top: 1px solid #e5e7eb;
        margin-top: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── 홈 레이아웃 ──────────────────────────────────────────────────────────
    st.markdown('<div class="home-wrap">', unsafe_allow_html=True)

    # 히어로
    st.markdown("""
    <div class="hero-badge">📡 데이터 기반 치안 분석 프로젝트</div>
    <h1 class="hero-title">서울시 치안 데이터<br><span>CCTV 상관관계 분석</span></h1>
    <p class="hero-sub">
        서울시 25개 자치구의 범죄 발생 이력, CCTV 설치 현황, 인구 통계를 통합 분석해<br>
        치안 인프라의 효율성과 CCTV 투자 우선순위를 도출합니다.
    </p>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="home-divider">', unsafe_allow_html=True)

    # KPI 카드 (실제 데이터)
    total_cctv     = int(df_final["CCTV수"].sum())
    total_crime    = int(df_final["발생건수"].sum())
    avg_crime_rate = df_final["범죄율"].mean()
    top_gu         = df_final.loc[df_final["발생건수"].idxmax(), "자치구"]

    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-label">분석 대상</div>
            <div class="kpi-value">25<span>개 자치구</span></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">CCTV 총 설치 대수 (2024)</div>
            <div class="kpi-value">{total_cctv:,}<span>대</span></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">5대 범죄 발생 (2024)</div>
            <div class="kpi-value">{total_crime:,}<span>건</span></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">평균 범죄율 (10만당)</div>
            <div class="kpi-value">{avg_crime_rate:.0f}<span>건</span></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">범죄 최다 자치구</div>
            <div class="kpi-value" style="font-size:1.35rem;">{top_gu}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 분석 정보 띠
    st.markdown("""
    <div class="info-bar">
        <div class="info-item">
            <div class="info-item-label">📅 분석 기간</div>
            <div class="info-item-val">2015 ~ 2024년</div>
        </div>
        <div class="info-item">
            <div class="info-item-label">📂 활용 데이터</div>
            <div class="info-item-val">CCTV · 범죄 · 인구 · 유흥업소</div>
        </div>
        <div class="info-item">
            <div class="info-item-label">🔬 분석 방법</div>
            <div class="info-item-val">피어슨 상관계수 · 순위 종합 분석</div>
        </div>
        <div class="info-item">
            <div class="info-item-label">🎯 목적</div>
            <div class="info-item-val">CCTV 추가 설치 우선순위 도출</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 챕터 카드
    st.markdown('<div class="chapter-section-title">분석 챕터 바로가기</div>',
                unsafe_allow_html=True)

    CHAPTERS_META = [
        {
            "key": "ch1", "cls": "c1",
            "num": "Chapter 01",
            "title": "지역구별 분석",
            "desc": "CCTV 수·인구·유흥업소와 범죄 발생 건수의 자치구별 상관관계를 시각화합니다.",
            "tags": ["CCTV & 범죄", "유흥업소 & 범죄", "인구 & 범죄"],
        },
        {
            "key": "ch2", "cls": "c2",
            "num": "Chapter 02",
            "title": "범죄 유형별 분석",
            "desc": "살인·강도·절도·폭력 등 5대 범죄 유형의 10년 추이와 발생 장소 분포를 분석합니다.",
            "tags": ["5대 범죄 추이", "CCTV 상관성", "발생 장소 히트맵"],
        },
        {
            "key": "ch3", "cls": "c3",
            "num": "Chapter 03",
            "title": "연도별 추세 분석",
            "desc": "2015~2024년 CCTV 누적 증가와 범죄율 변화 추이를 연도별로 비교합니다.",
            "tags": ["CCTV 누적 현황", "범죄율 추세", "실시간 탐지 실적"],
        },
        {
            "key": "ch4", "cls": "c4",
            "num": "Chapter 04",
            "title": "CCTV 투자 우선순위",
            "desc": "범죄율·CCTV 밀도·효율성을 종합해 CCTV 추가 설치가 시급한 자치구를 도출합니다.",
            "tags": ["종합 우선순위", "CCTV 부담 지표", "추가 설치 전략"],
        },
    ]

    # 2×2 그리드
    row1_l, row1_r = st.columns(2, gap="medium")
    row2_l, row2_r = st.columns(2, gap="medium")
    col_map = [row1_l, row1_r, row2_l, row2_r]

    for meta, col in zip(CHAPTERS_META, col_map):
        with col:
            tags_html = "".join(
                f'<span class="ch-tag">{t}</span>' for t in meta["tags"]
            )
            st.markdown(f"""
            <div class="ch-card {meta['cls']}">
                <div class="ch-num">{meta['num']}</div>
                <div class="ch-title">{meta['title']}</div>
                <div class="ch-desc">{meta['desc']}</div>
                <div class="ch-tags">{tags_html}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(
                f"→ {meta['title']} 바로가기",
                key=f"home_btn_{meta['key']}",
                use_container_width=True
            ):
                st.session_state.page = meta["key"]
                st.rerun()

    # 푸터
    st.markdown("""
    <div class="home-footer">
        서울 열린데이터광장 · 경찰청 범죄통계 · 공공데이터포털 기반 분석
        &nbsp;|&nbsp; 2015–2024 &nbsp;|&nbsp; 서울시 25개 자치구
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # home-wrap 닫기

# ════════════════════════════════════════════════════════════════════════════════
# CH1. 지역구별 분석
# ════════════════════════════════════════════════════════════════════════════════
if page == "ch1":
    st.header("CH1. 지역구별 분석 (2024년 기준)")
    st.markdown("---")

    # ── 1️⃣ CCTV 수 & 범죄 수 ────────────────────────────────────────────────
    corr_abs = df_final["CCTV수"].corr(df_final["발생건수"])
    st.subheader("1️⃣ CCTV 수 & 범죄 발생 건수 (상관관계 이상)")

    view1 = st.segmented_control("그래프 형태 선택",
                                 options=["📊 추이 분석", "📈 상관관계"],
                                 default="📊 추이 분석", key="view_1")
    if view1 == "📊 추이 분석":
        df_s = df_final.sort_values("CCTV수")
        fig, ax1 = plt.subplots(figsize=(13, 5))
        ax1.bar(df_s["자치구"], df_s["CCTV수"], color="#87CEEB", alpha=0.6, label="CCTV 수")
        ax1.set_ylabel("CCTV 설치 수 (대)", color="#008B8B")
        ax1.tick_params(axis="x", rotation=45); ax1.tick_params(axis="y", labelcolor="#008B8B")
        ax2 = ax1.twinx()
        ax2.plot(df_s["자치구"], df_s["발생건수"], color= "#FF4500", marker="s", linewidth=2, label="범죄 발생 건수")
        ax2.set_ylabel("범죄 발생 건수 (건)", color="#FF4500"); ax2.tick_params(axis="y", labelcolor="#FF4500")
        ax1.set_title(f"CCTV 설치 수 오름차순 · 범죄 발생 건수  (r = {corr_abs:.4f})", fontsize=13, fontweight="bold")
        lines1, lbl1 = ax1.get_legend_handles_labels(); lines2, lbl2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1+lines2, lbl1+lbl2, loc="upper left", fontsize=10)
        plt.tight_layout(); st.pyplot(fig)
    else:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.regplot(data=df_final, x="CCTV수", y="발생건수",
                    scatter_kws={"s": 60, 'color': "#87CEEB", "edgecolors": "#008B8B"}, line_kws={"color": "#FF4500"}, ax=ax)
        for _, row in df_final.iterrows():
            ax.text(row["CCTV수"]+60, row["발생건수"]+30, row["자치구"], fontsize=8)
        ax.set_title(f"CCTV 수 vs 범죄 발생 건수  (상관계수: {corr_abs:.4f})", fontsize=13, fontweight="bold")
        ax.set_xlabel("CCTV 설치 수 (대)"); ax.set_ylabel("범죄 발생 건수 (건)")
        plt.tight_layout(); st.pyplot(fig)
    st.markdown(f"CCTV수 ↔ 범죄발생건수 상관계수: **{corr_abs:.4f}**")

    st.divider()

    # ── 2️⃣ 유흥업소 수 & 범죄 수 ────────────────────────────────────────────
    corr_adult = df_final["유흥업소수"].corr(df_final["발생건수"])
    st.subheader("2️⃣ 유흥업소 수 & 범죄 발생 건수")

    view_adult = st.segmented_control("그래프 형태 선택",
                                      options=["📊 추이 분석", "📈 상관관계"],
                                      default="📊 추이 분석", key="view_adult")
    if view_adult == "📊 추이 분석":
        df_a = df_final.sort_values("유흥업소수")
        fig_a, ax_a1 = plt.subplots(figsize=(13, 5))
        ax_a1.bar(df_a["자치구"], df_a["유흥업소수"], color="#87CEEB", alpha=0.7, label="유흥업소 수")
        ax_a1.set_ylabel("유흥업소 수 (개)", color="#008B8B")
        ax_a1.tick_params(axis="x", rotation=45); ax_a1.tick_params(axis="y", labelcolor="#008B8B")
        ax_a1.grid(True, axis="y", linestyle="--", alpha=0.3)
        ax_a2 = ax_a1.twinx()
        ax_a2.plot(df_a["자치구"], df_a["발생건수"], color="#FF4500", marker="o",
                   markersize=7, linewidth=2.5, label="범죄 발생 건수")
        ax_a2.set_ylabel("범죄 발생 건수 (건)", color="#FF4500"); ax_a2.tick_params(axis="y", labelcolor="#FF4500")
        ax_a1.set_title(f"자치구별 유흥업소 수 & 범죄 발생 건수  (r = {corr_adult:.4f})", fontsize=13, fontweight="bold")
        lines1, lbl1 = ax_a1.get_legend_handles_labels(); lines2, lbl2 = ax_a2.get_legend_handles_labels()
        ax_a1.legend(lines1+lines2, lbl1+lbl2, loc="upper left", fontsize=10)
        plt.tight_layout(); st.pyplot(fig_a)
    else:
        fig_a, ax_a = plt.subplots(figsize=(10, 6))
        sns.regplot(data=df_final, x="유흥업소수", y="발생건수",
                    scatter_kws={"s": 65, "color": "#87CEEB", "edgecolors": "#008B8B", "linewidths": 0.8},
                    line_kws={"color": "#FF4500", "linewidth": 2}, ax=ax_a)
        for _, row in df_final.iterrows():
            ax_a.text(row["유흥업소수"]+0.5, row["발생건수"]+30, row["자치구"], fontsize=8)
        ax_a.set_title(f"유흥업소 수 vs 범죄 발생 건수  (상관계수: {corr_adult:.4f})", fontsize=13, fontweight="bold")
        ax_a.set_xlabel("유흥업소 수 (개)"); ax_a.set_ylabel("범죄 발생 건수 (건)")
        ax_a.grid(True, linestyle="--", alpha=0.3)
        plt.tight_layout(); st.pyplot(fig_a)
    st.markdown(f"유흥업소수 ↔ 범죄발생건수 상관계수: **{corr_adult:.4f}**")
    st.divider()

    # ── 3️⃣ 인구 수 & 범죄 수 ────────────────────────────────────────────────
    corr_pop = df_final["인구수"].corr(df_final["발생건수"])
    st.subheader("3️⃣ 인구 수 & 범죄 발생 건수")

    view_pop = st.segmented_control("그래프 형태 선택",
                                    options=["📊 추이 분석", "📈 상관관계"],
                                    default="📊 추이 분석", key="view_pop")
    if view_pop == "📊 추이 분석":
        df_p = df_final.sort_values("인구수")
        fig_p, ax_p1 = plt.subplots(figsize=(13, 5))
        ax_p1.bar(df_p["자치구"], df_p["인구수"] / 10_000,
                  color="#87CEEB", alpha=0.75, label="인구수")
        ax_p1.set_ylabel("인구수 (만 명)", color="#008B8B")
        ax_p1.tick_params(axis="x", rotation=45); ax_p1.tick_params(axis="y", labelcolor="#008B8B")
        ax_p1.grid(True, axis="y", linestyle="--", alpha=0.3)
        ax_p2 = ax_p1.twinx()
        ax_p2.plot(df_p["자치구"], df_p["발생건수"], color="#FF4500", marker="D",
                   markersize=7, linewidth=2.5, label="범죄 발생 건수")
        ax_p2.set_ylabel("범죄 발생 건수 (건)", color="#FF4500"); ax_p2.tick_params(axis="y", labelcolor="#FF4500")
        ax_p1.set_title(f"인구수 오름차순 · 범죄 발생 건수  (r = {corr_pop:.4f})", fontsize=13, fontweight="bold")
        lines1, lbl1 = ax_p1.get_legend_handles_labels(); lines2, lbl2 = ax_p2.get_legend_handles_labels()
        ax_p1.legend(lines1+lines2, lbl1+lbl2, loc="upper left", fontsize=10)
        plt.tight_layout(); st.pyplot(fig_p)
    else:
        fig_p, ax_p = plt.subplots(figsize=(10, 6))
        sns.regplot(data=df_final, x="인구수", y="발생건수",
                    scatter_kws={"s": 65, "color": "#87CEEB", "edgecolors": "#008B8B", "linewidths": 0.8},
                    line_kws={"color": "#FF4500", "linewidth": 2}, ax=ax_p)
        for _, row in df_final.iterrows():
            ax_p.text(row["인구수"]+2_000, row["발생건수"]+30, row["자치구"], fontsize=8)
        ax_p.set_title(f"인구수 vs 범죄 발생 건수  (상관계수: {corr_pop:.4f})", fontsize=13, fontweight="bold")
        ax_p.set_xlabel("인구수 (명)"); ax_p.set_ylabel("범죄 발생 건수 (건)")
        ax_p.grid(True, linestyle="--", alpha=0.3)
        ax_p.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x/10000)}만"))
        plt.tight_layout(); st.pyplot(fig_p)
        
    st.markdown(f"인구수 ↔ 범죄발생건수 상관계수: **{corr_pop:.4f}**")
    st.divider()

    # ── 인구 현황 바 차트 ─────────────────────────────────────────────────────
    st.subheader("👥 서울시 자치구별 등록인구 현황 (2024년)")
    pop_s = df_final.sort_values("인구수", ascending=False)
    fig_pop, ax_pop = plt.subplots(figsize=(14, 5))
    sns.barplot(x="자치구", y="인구수", data=pop_s, color="#87CEEB", ax=ax_pop)
    ax_pop.set_title("2024년 서울시 자치구별 등록인구 (내림차순)", fontsize=14, fontweight="bold")
    ax_pop.set_ylabel("인구수 (명)"); ax_pop.tick_params(axis="x", rotation=45)
    for i, val in enumerate(pop_s["인구수"]):
        ax_pop.text(i, val+3_000, f"{val/10000:.1f}만", ha="center", fontsize=8, fontweight="bold")
    plt.tight_layout(); st.pyplot(fig_pop)
    st.divider()

    # ── 4️⃣ CCTV 수 & 범죄율 ─────────────────────────────────────────────────
    corr_rate = df_final["CCTV수"].corr(df_final["범죄율"])
    st.subheader("4️⃣ CCTV 수 & 인구 대비 범죄율 (상관관계 미약)")
    st.caption(f"CCTV수 ↔ 범죄율(10만당) 상관계수: **{corr_rate:.4f}**")

    view2 = st.segmented_control("그래프 형태 선택",
                                 options=["📊 추이 분석", "📈 상관관계"],
                                 default="📊 추이 분석", key="view_2")
    if view2 == "📊 추이 분석":
        df_s = df_final.sort_values("CCTV수")
        fig2, ax3 = plt.subplots(figsize=(13, 5))
        ax3.bar(df_s["자치구"], df_s["CCTV수"], color="#87CEEB", alpha=0.7, label="CCTV 수")
        ax3.set_ylabel("CCTV 설치 수 (대)", color="#008B8B")
        ax3.tick_params(axis="x", rotation=45); ax3.tick_params(axis="y", labelcolor="#008B8B")
        ax4 = ax3.twinx()
        ax4.plot(df_s["자치구"], df_s["범죄율"], color="#FF4500", marker="o", linewidth=2.5, label="범죄율")
        ax4.set_ylabel("인구 10만명당 범죄율 (건)", color="#FF4500"); ax4.tick_params(axis="y", labelcolor="#FF4500")
        ax3.set_title(f"CCTV 설치 수 오름차순 · 인구 대비 범죄율  (r = {corr_rate:.4f})", fontsize=13, fontweight="bold")
        lines1, lbl1 = ax3.get_legend_handles_labels(); lines2, lbl2 = ax4.get_legend_handles_labels()
        ax3.legend(lines1+lines2, lbl1+lbl2, loc="upper left", fontsize=10)
        plt.tight_layout(); st.pyplot(fig2)
    else:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.regplot(data=df_final, x="CCTV수", y="범죄율",
                    scatter_kws={"s": 60, "alpha": 0.8, "color": "#87CEEB", "edgecolors": "#008B8B"}, line_kws={"color": "#FF4500"}, ax=ax)
        for _, row in df_final.iterrows():
            ax.text(row["CCTV수"]+60, row["범죄율"]+0.5, row["자치구"], fontsize=8)
        ax.set_title(f"CCTV 수 vs 인구 10만명당 범죄율  (상관계수: {corr_rate:.4f})", fontsize=13, fontweight="bold")
        ax.set_xlabel("CCTV 설치 수 (대)"); ax.set_ylabel("범죄율 (인구 10만명당)")
        plt.tight_layout(); st.pyplot(fig)

    st.divider()

    # ── 데이터 요약표 ─────────────────────────────────────────────────────────
    with st.expander("🔍 2024년 자치구별 종합 데이터 요약 보기", expanded=False):
        disp = df_final[["자치구","인구수","CCTV수","발생건수","범죄율","CCTV_밀도","CCTV당_범죄수"]].rename(columns={
            "CCTV수":"CCTV수(대)","발생건수":"범죄발생건수","범죄율":"범죄율(10만당)",
            "CCTV_밀도":"CCTV밀도(1만당)","CCTV당_범죄수":"CCTV당범죄건수"})
        disp.index = disp.index + 1
        st.dataframe(disp.style.format({
            "인구수":"{:,.0f}","CCTV수(대)":"{:,.0f}","범죄발생건수":"{:,.0f}",
            "범죄율(10만당)":"{:.1f}","CCTV밀도(1만당)":"{:.1f}","CCTV당범죄건수":"{:.2f}"}),
            use_container_width=True)
    st.divider()

    # # ── 5️⃣ CCTV 밀도 & 범죄율 (상관관계 강함) ───────────────────────────────
    # corr_dens = df_final["CCTV_밀도"].corr(df_final["범죄율"])
    # st.header("5️⃣ CCTV 밀도 & 범죄율 (상관관계 강함)")
    # st.markdown("단순 설치 대수가 아닌 **인구 대비 CCTV 밀도**로 비교하면 뚜렷한 음의 상관이 나타납니다.")

    # col1, col2 = st.columns(2)
    # with col1:
    #     st.subheader("인구 1만명당 CCTV 수 순위")
    #     df_dens  = df_final.sort_values("CCTV_밀도", ascending=True)
    #     mean_d   = df_final["CCTV_밀도"].mean()
    #     colors_d = ["#d73027" if v > mean_d else "#4575b4" for v in df_dens["CCTV_밀도"]]
    #     fig4, ax4 = plt.subplots(figsize=(8, 9))
    #     b4 = ax4.barh(df_dens["자치구"], df_dens["CCTV_밀도"], color=colors_d)
    #     ax4.axvline(mean_d, color="orange", linestyle="--", linewidth=2, label=f"평균 {mean_d:.1f}대/만명")
    #     ax4.set_title("인구 1만명당 CCTV 밀도", fontsize=12, fontweight="bold")
    #     ax4.set_xlabel("대 / 인구 1만명"); ax4.legend()
    #     for bar, val in zip(b4, df_dens["CCTV_밀도"]):
    #         ax4.text(val+0.1, bar.get_y()+bar.get_height()/2, f"{val:.1f}", va="center", fontsize=8)
    #     plt.tight_layout(); st.pyplot(fig4)
    #     st.caption("🔴 평균 초과 / 🔵 평균 이하")
    # with col2:
    #     st.subheader("CCTV 밀도 vs 범죄율 산점도")
    #     fig5, ax5 = plt.subplots(figsize=(8, 7))
    #     sns.regplot(data=df_final, x="CCTV_밀도", y="범죄율",
    #                 scatter_kws={"s": 70, "alpha": 0.8}, line_kws={"color": "red"}, ax=ax5)
    #     for _, row in df_final.iterrows():
    #         ax5.text(row["CCTV_밀도"]+0.15, row["범죄율"]+0.5, row["자치구"], fontsize=8)
    #     ax5.set_title(f"CCTV 밀도 vs 범죄율  (상관계수: {corr_dens:.4f})", fontsize=12, fontweight="bold")
    #     ax5.set_xlabel("인구 1만명당 CCTV 수 (대)"); ax5.set_ylabel("인구 10만명당 범죄율 (건)")
    #     plt.tight_layout(); st.pyplot(fig5)
    #     if corr_dens < 0:
    #         st.success(f"✅ CCTV 밀도 ↑ → 범죄율 ↓ 경향 확인 (상관계수: {corr_dens:.4f})")
    #     else:
    #         st.info(f"ℹ️ 상관계수: {corr_dens:.4f}")

# ════════════════════════════════════════════════════════════════════════════════
# CH2. 범죄 유형별 분석
# ════════════════════════════════════════════════════════════════════════════════
elif page == "ch2":
    st.title("CH2. 범죄 유형별 분석")
    st.markdown("---")

    st.subheader("1️⃣ 범죄 유형별 발생 추이 및 CCTV 상관성 분석 (2015–2024)")
    st.markdown("2015 ~ 2024년 서울시 **5대 범죄 유형별 발생 건수**와 CCTV 누적 설치량의 관계를 분석합니다.")
    st.write("아래 버튼을 눌러 분석할 범죄 유형을 선택하세요. **(중복 선택 가능)**")

    CRIME_TYPES_BTN = ["절도","폭력","살인","강도","강간·강제추행"]
    CRIME_COLORS    = {"절도":"#e74c3c","폭력":"#3498db","살인":"#2ecc71","강도":"#f39c12","강간·강제추행":"#9b59b6"}
    if "active_crimes" not in st.session_state:
        st.session_state.active_crimes = set()

    # ── 활성 버튼 테두리 CSS (범죄별 고유 색상) ──────────────────────────────
    # 정확히 5열 + 버튼 포함 조건으로 범죄 버튼 행만 타겟
    btn_css = ""
    for i, crime in enumerate(CRIME_TYPES_BTN):
        if crime in st.session_state.active_crimes:
            c = CRIME_COLORS[crime]
            btn_css += (
                f"[data-testid='stHorizontalBlock']:has(>div:nth-child(5)):not(:has(>div:nth-child(6)))"
                f">div:nth-child({i+1}) button{{"
                f"border:2px solid {c}!important;"
                f"color:{c}!important;"
                f"background:transparent!important;"
                f"font-weight:700!important;}}"
            )
    st.markdown(f"<style>{btn_css}</style>", unsafe_allow_html=True)
 
    btn_cols = st.columns(len(CRIME_TYPES_BTN))
    for i, crime in enumerate(CRIME_TYPES_BTN):
        if btn_cols[i].button(crime, key=f"btn_{crime}", use_container_width=True):
            if crime in st.session_state.active_crimes: st.session_state.active_crimes.remove(crime)
            else:                                       st.session_state.active_crimes.add(crime)
            st.rerun()
 
    if not st.session_state.active_crimes:
        st.info("범죄 유형 버튼을 클릭하면 분석 차트가 활성화됩니다.")
    else:
        selected = sorted(st.session_state.active_crimes, key=lambda x: CRIME_TYPES_BTN.index(x))
        df_sub   = df_all_crime[df_all_crime["유형"].isin(selected)]
        col_chart, col_table = st.columns([3, 2])
        COLORS    = ["#e74c3c","#3498db","#2ecc71","#f39c12","#9b59b6"]
        color_map = dict(zip(CRIME_TYPES_BTN, COLORS))
 
        with col_chart:
            fig_s3 = make_subplots(specs=[[{"secondary_y": True}]])
            fig_s3.add_trace(
                go.Bar(x=df_10yr_base["연도"], y=df_10yr_base["CCTV누적"],
                       name="CCTV 누적 (배경)", marker_color="rgba(149,165,166,0.4)"),
                secondary_y=False)
            for crime in selected:
                crime_df = df_sub[df_sub["유형"] == crime].sort_values("연도")
                fig_s3.add_trace(
                    go.Scatter(x=crime_df["연도"], y=crime_df["건수"], name=crime,
                               mode="lines+markers",
                               line=dict(width=3, color=color_map[crime]), marker=dict(size=8)),
                    secondary_y=True)
            fig_s3.update_layout(
                template="plotly_white", hovermode="x unified", height=420, margin=dict(b=0),
                yaxis_title="CCTV 누적 설치 수 (대)", yaxis2_title="범죄 발생 건수 (건)")
            st.plotly_chart(fig_s3, use_container_width=True)
 
            df_sub_agg  = df_sub.groupby("연도")["건수"].sum().reset_index().sort_values("연도")
            merged_corr = df_10yr_base.merge(df_sub_agg, on="연도")
            r_val, _    = stats.pearsonr(merged_corr["CCTV누적"], merged_corr["건수"])
            label_str   = " + ".join(selected)
            c_card  = "#e7f5ff" if r_val < 0 else "#fff5f5"
            b_color = "#a5d8ff" if r_val < 0 else "#ffa8a8"
            t_color = "#1864ab" if r_val < 0 else "#c92a2a"
            st.markdown(
                f'<div style="padding:12px 20px;border-radius:0 0 12px 12px;background:{c_card};'
                f'color:{t_color};border-top:2px solid {b_color};text-align:center;'
                f'margin-top:-14px;font-size:1.05em;">'
                f'<b>{label_str}</b> 합계 ↔ CCTV 상관계수(r): <b>{r_val:.4f}</b></div>',
                unsafe_allow_html=True)
 
        with col_table:
            st.subheader("연도별 증감 수치")
 
            # ── 증감 데이터 계산 ──────────────────────────────────────────────
            tbl = df_10yr_base[["연도"]].copy()
            for crime in selected:
                cy = df_sub[df_sub["유형"] == crime].sort_values("연도").set_index("연도")["건수"]
                tbl[f"{crime}_증감"] = tbl["연도"].map(cy).diff().fillna(0).astype(int)
 
            # ── HTML 테이블 생성 ──────────────────────────────────────────────
            th_style  = "padding:8px 14px;text-align:center;border-bottom:2px solid #e0e0e0;font-weight:600;"
            td_yr     = "padding:7px 14px;text-align:center;color:#555;border-bottom:1px solid #f0f0f0;"
            td_val    = "padding:7px 14px;text-align:center;border-bottom:1px solid #f0f0f0;"
 
            # 헤더
            head = f'<th style="{th_style}color:#555;">연도</th>'
            for crime in selected:
                c = color_map[crime]
                head += f'<th style="{th_style}color:{c};">{crime} 증감</th>'
 
            # 행
            body = ""
            for _, row in tbl.iterrows():
                cells = f'<td style="{td_yr}">{row["연도"]}</td>'
                for crime in selected:
                    val = int(row[f"{crime}_증감"])
                    c   = color_map[crime]
                    if val > 0:
                        tri = f'<span style="color:#e74c3c;">▲</span>'
                    elif val < 0:
                        tri = f'<span style="color:#3498db;">▼</span>'
                    else:
                        tri = '<span style="color:#bbb;">─</span>'
                    num = f'<span style="color:{c};font-weight:600;">{val:+,}</span>'
                    cells += f'<td style="{td_val}">{tri}&nbsp;{num}</td>'
                body += f"<tr>{cells}</tr>"
 
            st.markdown(
                f'<div style="overflow-y:auto;max-height:390px;border:1px solid #e8e8e8;'
                f'border-radius:8px;font-size:0.83rem;">'
                f'<table style="width:100%;border-collapse:collapse;">'
                f'<thead style="position:sticky;top:0;background:#fafafa;"><tr>{head}</tr></thead>'
                f'<tbody>{body}</tbody></table></div>',
                unsafe_allow_html=True)
 
        st.markdown("##### 2015 → 2024 변화율 요약")
        cctv_chg    = (df_10yr_base["CCTV누적"].iloc[-1] - df_10yr_base["CCTV누적"].iloc[0]) \
                      / df_10yr_base["CCTV누적"].iloc[0] * 100
        metric_cols = st.columns(len(selected) + 1)
        metric_cols[0].metric("CCTV 증가율", f"+{cctv_chg:.1f}%")
        for j, crime in enumerate(selected):
            cdf     = df_sub[df_sub["유형"] == crime].sort_values("연도")
            v_first = cdf["건수"].iloc[0]
            v_last  = cdf["건수"].iloc[-1]
            chg     = (v_last - v_first) / v_first * 100 if v_first != 0 else 0
            metric_cols[j+1].metric(
                f"{crime} 발생 변화", f"{v_last:,.0f}건",
                delta=f"{'▼' if chg < 0 else '▲'} {abs(chg):.1f}%", delta_color="inverse")
    st.divider()
 
    st.header("2️⃣ 5대 범죄 발생 장소 분포 (2024년)")
    st.markdown("**어디서 범죄가 주로 발생하는지** 파악해 CCTV 설치 전략에 활용합니다.")
 
    try:
        crime_loc_raw = load_crime_loc()
        loc_cols   = [f"2024.{i}" for i in range(1, 13)]
        loc_labels = ["아파트/연립다세대","단독주택","기타거주시설","도로/골목길","상점/창고",
                      "공중위생업소","음식점/유흥업소","역/대합실","교통수단","문화/체육시설","학교/도서관","기타"]
        crime_loc_filter = ["살인","강도","강간강제추행","절도","폭력"]
        crime_loc_kor    = ["살인","강도","강간·강제추행","절도","폭력"]
        rows_loc = []
        for c_type, c_kor in zip(crime_loc_filter, crime_loc_kor):
            row = crime_loc_raw[crime_loc_raw["범죄별(2)"] == c_type]
            if not row.empty:
                vals = []
                for col in loc_cols:
                    v = pd.to_numeric(str(row[col].values[0]).replace(",","").replace("-","0"), errors="coerce")
                    vals.append(float(v) if pd.notna(v) else 0.0)
                rows_loc.append([c_kor] + vals)
        df_loc     = pd.DataFrame(rows_loc, columns=["범죄유형"] + loc_labels).set_index("범죄유형")
        df_loc_pct = df_loc.div(df_loc.sum(axis=1), axis=0) * 100
 
        st.subheader("범죄 유형 × 발생 장소 비율 히트맵")
        fig8, ax8 = plt.subplots(figsize=(14, 4))
        sns.heatmap(df_loc_pct, annot=True, fmt=".1f", cmap="YlOrRd",
                    linewidths=0.5, ax=ax8, cbar_kws={"label": "비율 (%)"})
        ax8.set_title("2024년 범죄 유형별 발생 장소 비율 히트맵 (%)", fontsize=13, fontweight="bold")
        ax8.set_xticklabels(ax8.get_xticklabels(), rotation=30, ha="right")
        plt.tight_layout(); st.pyplot(fig8)
 
        st.subheader("범죄 유형별 발생 장소 상세")
        tabs_loc = st.tabs([f"{c}" for c in crime_loc_kor])
        for ti, crime in enumerate(crime_loc_kor):
            with tabs_loc[ti]:
                row_data = df_loc_pct.loc[crime].sort_values(ascending=False)
                row_data = row_data[row_data > 0]
                fig9, ax9 = plt.subplots(figsize=(9, 4))
                b9 = ax9.barh(row_data.index[::-1], row_data.values[::-1],
                              color=sns.color_palette("RdYlBu_r", len(row_data))[::-1])
                ax9.set_title(f"{crime} 발생 장소 비율 (2024년)", fontsize=12, fontweight="bold")
                ax9.set_xlabel("비율 (%)")
                for bar, val in zip(b9, row_data.values[::-1]):
                    ax9.text(val+0.3, bar.get_y()+bar.get_height()/2,
                             f"{val:.1f}%", va="center", fontsize=9, fontweight="bold")
                plt.tight_layout(); st.pyplot(fig9)
    except Exception as e:
        st.warning(f"범죄 발생 장소 데이터를 불러오는 중 오류: {e}")
# ════════════════════════════════════════════════════════════════════════════════
# CH3. 연도별 추세 분석
# ════════════════════════════════════════════════════════════════════════════════
elif page == "ch3":
    st.header("CH3. 연도별 추세 분석 (2015–2024)")
    st.markdown("---")

    st.subheader("1️⃣ 서울시 CCTV 연도별 설치 현황 (2015–2025)")
    year_cols  = [c for c in cctv_raw.columns if str(c).endswith("년")]
    cctv_years = cctv_raw[year_cols].apply(pd.to_numeric, errors="coerce").fillna(0)

    tab_a1, tab_a2, tab_a3 = st.tabs(
        ["📊 연도별 누적 설치 총량", "📈 연도별 신규 설치 추이", "🗂️ 자치구별 2024년 CCTV"])

    with tab_a1:
        total_cum = cctv_years.sum()
        fig, ax = plt.subplots(figsize=(12, 5))
        bars = ax.bar(total_cum.index, total_cum.values, color='#87CEEB')
        ax.set_title("서울시 연도별 CCTV 누적 설치 대수 (전체 합산)", fontsize=14, fontweight="bold")
        ax.set_ylabel("누적 설치 대수 (대)"); ax.tick_params(axis="x", rotation=30)
        for bar, val in zip(bars, total_cum.values):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+500,
                    f"{int(val):,}", ha="center", fontsize=8, fontweight="bold")
        plt.tight_layout(); st.pyplot(fig)

    with tab_a2:
        cctv_diff = cctv_years.diff(axis=1).iloc[:, 1:]
        total_inc = cctv_diff.sum()
        fig2, ax2 = plt.subplots(figsize=(12, 5))
        ax2.fill_between(range(len(total_inc)), total_inc.values, alpha=0.2, color="#FF4500")
        ax2.plot(total_inc.index, total_inc.values, marker="o", linewidth=3, color="#FF4500", markersize=8)
        ax2.set_title("서울시 연도별 신규 CCTV 설치 추이", fontsize=14, fontweight="bold")
        ax2.set_ylabel("신규 설치 대수 (대)")
        ax2.grid(True, linestyle="--", alpha=0.4); ax2.tick_params(axis="x", rotation=30)
        for i, val in enumerate(total_inc.values):
            ax2.text(i, val+max(total_inc)*0.03, f"{int(val):,}", ha="center",
                     fontsize=8, fontweight="bold", color="#FF4500")
        plt.tight_layout(); st.pyplot(fig2)

    with tab_a3:
        df_cctv_s = df_final.sort_values("CCTV수", ascending=True)
        mean_cctv = df_final["CCTV수"].mean()
        colors_c  = ["#d73027" if v > mean_cctv else "#4575b4" for v in df_cctv_s["CCTV수"]]
        fig3, ax3 = plt.subplots(figsize=(9, 9))
        b3 = ax3.barh(df_cctv_s["자치구"], df_cctv_s["CCTV수"], color=colors_c)
        ax3.axvline(mean_cctv, color="orange", linestyle="--", linewidth=2, label=f"평균 {mean_cctv:.0f}대")
        ax3.set_title("자치구별 CCTV 누적 설치 대수 (2024년)", fontsize=13, fontweight="bold")
        ax3.set_xlabel("CCTV 설치 대수 (대)"); ax3.legend()
        for bar, val in zip(b3, df_cctv_s["CCTV수"]):
            ax3.text(val+50, bar.get_y()+bar.get_height()/2, f"{int(val):,}", va="center", fontsize=8)
        plt.tight_layout(); st.pyplot(fig3)
        st.caption("🔴 평균 초과 / 🔵 평균 이하")

    st.divider()

    st.subheader("2️⃣ CCTV 증가량 & 범죄율 감소 상관관계")

    fig7, ax7a = plt.subplots(figsize=(13, 5))
    ax7a.fill_between(df_trend["연도"], df_trend["CCTV수량"], alpha=0.25, color="#87CEEB")
    ax7a.plot(df_trend["연도"], df_trend["CCTV수량"], color="#87CEEB", linewidth=2,
              marker="o", label="CCTV 설치 수량")
    ax7a.set_ylabel("CCTV 누적 설치 수량 (대)", color="#008B8B")
    ax7a.tick_params(axis="y", labelcolor="#008B8B"); ax7a.tick_params(axis="x", rotation=30)
    ax7b = ax7a.twinx()
    ax7b.plot(df_trend["연도"], df_trend["총범죄율"], color="#FF4500", linewidth=2.5,
              marker="^", linestyle="--", label="5대 범죄율 (10만당)")
    ax7b.set_ylabel("인구 10만명당 범죄율 (건)", color="#FF4500"); ax7b.tick_params(axis="y", labelcolor="#FF4500")
    ax7a.set_title("서울시 전체 CCTV 누적 수량 vs 5대 범죄율 추이 (2015–2024)", fontsize=14, fontweight="bold")
    lines_a, lbl_a = ax7a.get_legend_handles_labels()
    lines_b, lbl_b = ax7b.get_legend_handles_labels()
    ax7a.legend(lines_a+lines_b, lbl_a+lbl_b, loc="upper right")
    plt.tight_layout(); st.pyplot(fig7)

    chg_cctv  = (df_trend["CCTV수량"].iloc[-1]-df_trend["CCTV수량"].iloc[0])/df_trend["CCTV수량"].iloc[0]*100
    chg_crime = (df_trend["총범죄율"].iloc[-1]-df_trend["총범죄율"].iloc[0])/df_trend["총범죄율"].iloc[0]*100
    corr_t    = df_trend["CCTV수량"].corr(df_trend["총범죄율"])
    c1, c2, c3 = st.columns(3)
    c1.metric("CCTV 증가율 (2015→2024)", f"+{chg_cctv:.1f}%")
    c2.metric("5대 범죄율 변화 (2015→2024)", f"{chg_crime:.1f}%",
              delta="감소" if chg_crime < 0 else "증가", delta_color="inverse")
    c3.metric("연도별 CCTV–범죄율 상관계수", f"{corr_t:.4f}",
              help="음수: CCTV 증가 시 범죄율 감소 경향")
    st.divider()

    st.subheader("3️⃣ CCTV 인프라 & 실시간 탐지 신고 건수 상관관계")

    short_years  = ["2021","2022","2023","2024"]
    detect_vals  = [df_util[df_util["연도"].astype(str).str.contains(yr)]["합계"].sum()
                    for yr in short_years]
    df_util_base = df_10yr_base[df_10yr_base["연도"].isin(short_years)].copy()
    df_util_base["탐지실적"] = detect_vals

    fig_util = make_subplots(specs=[[{"secondary_y": True}]])
    fig_util.add_trace(
        go.Bar(x=df_util_base["연도"], y=df_util_base["CCTV누적"],
               name="CCTV 설치 누적", marker_color="#87CEEB"), secondary_y=False)
    fig_util.add_trace(
        go.Scatter(x=df_util_base["연도"], y=df_util_base["탐지실적"],
                   name="실시간 탐지 실적", mode="lines+markers",
                   line=dict(color="#FF4500", width=4, dash="dot"), marker=dict(size=12)),
        secondary_y=True)
    fig_util.update_layout(
        template="plotly_white", height=420, margin=dict(b=0), hovermode="x unified",
        yaxis_title="CCTV 누적 설치 수 (대)", yaxis2_title="탐지 실적 (건)")
    st.plotly_chart(fig_util, use_container_width=True)

    r_util, _ = stats.pearsonr(df_util_base["CCTV누적"], df_util_base["탐지실적"])
    st.markdown(
        f'<div style="padding:12px 20px;border-radius:0 0 12px 12px;background:#fff5f5;'
        f'color:#c92a2a;border-top:2px solid #ffa8a8;text-align:center;margin-top:-14px;font-size:1.05em;">'
        f'인프라 확충 대비 실시간 탐지 효율 상관계수(r): <b>{r_util:.4f}</b></div>',
        unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# CH4. CCTV 투자 우선순위
# ════════════════════════════════════════════════════════════════════════════════
elif page == "ch4":
    st.header("CH4. 자치구별 CCTV 투자 우선순위 분석")
    st.markdown("---")

    st.subheader("자치구별 CCTV 1대당 범죄 건수 (부담 지표)")
    df_eff   = df_final.sort_values("CCTV당_범죄수", ascending=False)
    mean_eff = df_final["CCTV당_범죄수"].mean()
    colors_e = ["#d73027" if v > mean_eff else "#4575b4" for v in df_eff["CCTV당_범죄수"]]
    fig6, ax6 = plt.subplots(figsize=(14, 4))
    ax6.bar(df_eff["자치구"], df_eff["CCTV당_범죄수"], color=colors_e)
    ax6.axhline(mean_eff, color="black", linestyle="--", linewidth=1.5, label=f"평균 {mean_eff:.2f}건/대")
    ax6.set_title("자치구별 CCTV 1대당 범죄 발생 건수 (2024년)", fontsize=13, fontweight="bold")
    ax6.set_ylabel("범죄 건수 / CCTV 1대")
    ax6.tick_params(axis="x", rotation=45); ax6.legend()
    plt.tight_layout(); st.pyplot(fig6)
    st.info("수치가 높을수록 CCTV가 상대적으로 부족함을 의미합니다.")
    st.divider()

    st.subheader("자치구별 CCTV 투자 우선순위 종합 분석")
    st.markdown(
        "**범죄율 순위** + **CCTV 밀도 역순위** + **CCTV 1대당 범죄수 순위**를 합산해 "
        "추가 설치가 가장 시급한 자치구를 도출합니다.")

    df_pri = df_final[["자치구","범죄율","CCTV_밀도","CCTV당_범죄수"]].copy()
    df_pri["범죄율_순위"]     = df_pri["범죄율"].rank(ascending=False)
    df_pri["CCTV밀도_역순위"] = df_pri["CCTV_밀도"].rank(ascending=True)
    df_pri["효율성_순위"]     = df_pri["CCTV당_범죄수"].rank(ascending=False)
    df_pri["종합점수"]        = (df_pri[["범죄율_순위","CCTV밀도_역순위","효율성_순위"]].sum(axis=1))/75*100
    df_pri = df_pri.sort_values("종합점수", ascending=True).reset_index(drop=True)
    df_pri.index += 1

    cp1, cp2 = st.columns([1, 2])

    st.dataframe(
        df_pri[["자치구","범죄율","CCTV_밀도","CCTV당_범죄수","종합점수"]]
        .rename(columns={"범죄율":"범죄율\n(10만당)","CCTV_밀도":"CCTV밀도\n(1만당)",
                          "CCTV당_범죄수":"CCTV당\n범죄건수","종합점수":"종합점수"})
        .style.format({"범죄율\n(10만당)":"{:.1f}","CCTV밀도\n(1만당)":"{:.1f}",
                       "CCTV당\n범죄건수":"{:.2f}","종합점수":"{:.0f}"})
        .background_gradient(subset=["종합점수"], cmap="RdBu"),
        use_container_width=True, height=500)
    
    top10 = df_pri.head(10)
    fig10, ax10 = plt.subplots(figsize=(9, 3))
    b10 = ax10.barh(top10["자치구"].iloc[::-1], top10["종합점수"].iloc[::-1],
                    color=sns.color_palette("RdBu", 10)[::-1])
    ax10.set_title("CCTV 추가 설치 우선순위 TOP 10 자치구", fontsize=13, fontweight="bold")
    ax10.set_xlabel("종합 우선순위 점수 (낮을수록 시급)")
    for bar, val in zip(b10, top10["종합점수"].iloc[::-1]):
        ax10.text(val+0.3, bar.get_y()+bar.get_height()/2,
                  f"{val:.0f}점", va="center", fontsize=10, fontweight="bold")
    plt.tight_layout(); st.pyplot(fig10)

    st.success(
        "✅ CCTV 설치가 가장 필요한 자치구는 송파구입니다." )
