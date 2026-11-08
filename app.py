# ============================================================
# SMART TRAFFIC ANALYTICS — app.py
# NYC Yellow Taxi demand analytics (Hadoop MapReduce -> CSV -> Streamlit)
# Historical analytics only. Fully filter-aware, single file.
# ============================================================

from datetime import datetime
from pathlib import Path
import html

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# 1. PAGE CONFIGURATION AND CONSTANTS
# ============================================================

st.set_page_config(
    page_title="Smart Traffic Analytics",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

FILES = {
    # all-time files (cannot be filtered by month)
    "monthly": "monthly_trips.csv",
    "hourly": "hourly_trips.csv",
    "weekday": "weekday_trips.csv",
    "pickup": "pickup_zones.csv",
    "dropoff": "dropoff_zones.csv",
    "payment": "payment_types.csv",
    "passengers": "passenger_counts.csv",
    "summary": "summary.csv",
    # month-level files (enable full filtering)
    "ms": "monthly_summary.csv",
    "mwh": "month_weekday_hour.csv",
    "mpick": "month_pickup.csv",
    "mdrop": "month_dropoff.csv",
    "mpay": "month_payment.csv",
    "mpax": "month_passengers.csv",
}
LOOKUP_NAME = "taxi_zone_lookup.csv"

TEAL = "#20E3CF"
ORANGE = "#FF9F43"
GREEN = "#38D996"
RED = "#FF647C"
MUTED = "#94A3B8"
COLORS = [TEAL, ORANGE, "#7C83FD", "#F472B6", "#38D996", "#FACC15", "#60A5FA", "#C084FC"]

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
PAY_LABELS = {"1": "Credit card", "2": "Cash", "3": "No charge", "4": "Dispute", "5": "Unknown", "6": "Voided"}
AIRPORTS = {1: "Newark Airport", 132: "JFK Airport", 138: "LaGuardia Airport"}  # official TLC zone IDs
ALLTIME = "All-time data (add month-level file to enable filtering)"


# ============================================================
# 2. CUSTOM STYLING (same look as before + chips, badges, deltas)
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp {
    background:
        radial-gradient(ellipse at 15% 0%, #102C35 0%, transparent 35%),
        radial-gradient(ellipse at 90% 10%, #241B35 0%, transparent 30%),
        #080E19;
    color: #E5EDF6;
}
[data-testid="stSidebar"] { background: #0C1524; border-right: 1px solid #233247; }
[data-testid="stSidebar"] * { color: #DCE7F3; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1500px; }
.hero {
    padding: 35px 38px; border: 1px solid #254253; border-radius: 22px;
    background: linear-gradient(115deg, #102A35, #151C30 60%, #242039);
    margin-bottom: 20px; box-shadow: 0 15px 45px rgba(0,0,0,0.25);
}
.hero h1 {
    font-size: clamp(28px, 4vw, 43px); font-weight: 800; letter-spacing: -1.5px; margin: 0;
    background: linear-gradient(90deg, #FFFFFF, #20E3CF, #FFAD68);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero p { color: #A8BACB; margin-top: 12px; font-size: 15px; }
.eyebrow { color: #20E3CF; font-size: 11px; font-weight: 800; letter-spacing: 2px; margin-bottom: 10px; }
.kpi-card {
    background: linear-gradient(145deg, rgba(25,43,60,0.92), rgba(13,24,39,0.96));
    border: 1px solid #294052; border-radius: 17px; padding: 20px; min-height: 125px;
    transition: all 0.25s ease; box-shadow: 0 8px 25px rgba(0,0,0,0.18);
}
.kpi-card:hover { border-color: #20E3CF; transform: translateY(-4px); box-shadow: 0 12px 30px rgba(32,227,207,0.12); }
.kpi-label { color: #9DB0C2; font-size: 12px; font-weight: 600; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
.kpi-value { color: #F4F8FC; font-size: 26px; font-weight: 800; letter-spacing: -0.8px; }
.kpi-caption { color: #20E3CF; font-size: 11px; margin-top: 8px; }
.delta-up { color: #38D996; font-size: 11px; margin-top: 6px; font-weight: 600; }
.delta-down { color: #FF647C; font-size: 11px; margin-top: 6px; font-weight: 600; }
.delta-flat { color: #94A3B8; font-size: 11px; margin-top: 6px; font-weight: 600; }
.section-title { color: #F1F6FC; font-size: 20px; font-weight: 750; margin-top: 22px; margin-bottom: 12px; }
.insight-card {
    background: #111F30; border-left: 3px solid #20E3CF; border-radius: 10px;
    padding: 14px 17px; margin-bottom: 11px; color: #DCE7F3; font-size: 13px;
}
.story-card {
    background: linear-gradient(145deg, #12263A, #101A2B); border: 1px solid #2B5260;
    border-radius: 14px; padding: 18px 22px; color: #DCE7F3; font-size: 14px; line-height: 1.7;
}
.warning-card {
    background: #302719; border: 1px solid #71502A; border-radius: 10px;
    padding: 12px 15px; color: #FFD49B; font-size: 12px;
}
.badge {
    display: inline-block; background: #302719; border: 1px solid #71502A; color: #FFD49B;
    border-radius: 999px; padding: 3px 11px; font-size: 11px; margin: 0 6px 8px 0;
}
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 18px 0; }
.chip {
    background: #0F2A33; border: 1px solid #20AFA4; color: #BFFBF4;
    border-radius: 999px; padding: 5px 13px; font-size: 12px;
}
.chip b { color: #20E3CF; font-size: 10px; letter-spacing: 1px; margin-right: 6px; }
.pipeline-step {
    background: linear-gradient(145deg, #172B3B, #101A2B); border: 1px solid #2B5260;
    border-radius: 13px; padding: 17px 8px; text-align: center; min-height: 100px;
}
.pipeline-step strong { color: #20E3CF; font-size: 14px; }
.pipeline-step small { color: #A8BACB; font-size: 11px; }
.footer {
    text-align: center; color: #8293A7; border-top: 1px solid #263548;
    padding: 22px 5px; margin-top: 45px; font-size: 11px;
}
.stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 1px solid #26384B; }
.stTabs [data-baseweb="tab"] { background: #111C2D; border-radius: 9px 9px 0 0; color: #AFC0D1; padding: 12px 17px; }
.stTabs [aria-selected="true"] { color: #20E3CF !important; border-bottom: 2px solid #20E3CF; }
div[data-testid="stExpander"] { border: 1px solid #294052; border-radius: 12px; background: #101B2B; }
.stButton button, .stDownloadButton button {
    border-radius: 9px; border: 1px solid #20AFA4; background: #12343B; color: #DFFFFB;
}
[data-testid="stMetricValue"] { color: #20E3CF; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# 3. SMALL HELPERS (formatting, HTML components, shared Plotly helper)
# ============================================================

def number(value, decimals=0):
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:,.{decimals}f}"


def safe_divide(a, b):
    return a / b if b else 0


def pct_change(new, old):
    if old is None or pd.isna(old) or old == 0 or new is None or pd.isna(new):
        return None
    return (new - old) / old * 100


def hour_label(h):
    h = int(h)
    return f"{(h % 12) or 12} {'AM' if h < 12 else 'PM'}"


def esc(text):
    """HTML-escape and neutralise '$' so Streamlit does not treat it as LaTeX."""
    return html.escape(str(text)).replace("$", "&#36;")


def cap(text):
    st.caption(str(text).replace("$", r"\$"))


def section_title(title, subtitle=None):
    st.markdown(f'<div class="section-title">{esc(title)}</div>', unsafe_allow_html=True)
    if subtitle:
        cap(subtitle)


def badge(text):
    st.markdown(f'<span class="badge">{esc(text)}</span>', unsafe_allow_html=True)


def insight(text):
    st.markdown(f'<div class="insight-card">✦ {esc(text)}</div>', unsafe_allow_html=True)


def sparkline(values, color=TEAL, w=120, h=30):
    vals = [float(v) for v in values if pd.notna(v)]
    if len(vals) < 2:
        return ""
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1
    pts = " ".join(
        f"{i * (w - 4) / (len(vals) - 1) + 2:.1f},{h - 3 - (v - lo) / rng * (h - 6):.1f}"
        for i, v in enumerate(vals)
    )
    return (
        f'<svg width="100%" viewBox="0 0 {w} {h}" preserveAspectRatio="none" '
        f'style="margin-top:8px;height:30px"><polyline fill="none" stroke="{color}" '
        f'stroke-width="2" points="{pts}"/></svg>'
    )


def kpi(label, value, caption="", delta=None, delta_label="", unit="%", spark=None):
    d = ""
    if delta is not None and pd.notna(delta):
        if abs(delta) < 0.05:
            cls, arrow = "delta-flat", "▬"
        elif delta > 0:
            cls, arrow = "delta-up", "▲"
        else:
            cls, arrow = "delta-down", "▼"
        d = f'<div class="{cls}">{arrow} {abs(delta):.1f}{unit} {esc(delta_label)}</div>'
    sp = sparkline(spark) if spark is not None else ""
    st.markdown(
        f'<div class="kpi-card"><div class="kpi-label">{esc(label)}</div>'
        f'<div class="kpi-value">{esc(value)}</div>'
        f'<div class="kpi-caption">{esc(caption)}</div>{d}{sp}</div>',
        unsafe_allow_html=True,
    )


def chart_style(fig, height=380):
    fig.update_layout(
        template="plotly_dark", height=height,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#DCE7F3", size=11),
        title_font=dict(size=16, color="#F1F6FC"),
        margin=dict(l=15, r=15, t=55, b=15), colorway=COLORS,
        hoverlabel=dict(bgcolor="#17283A", bordercolor=TEAL, font=dict(color="white", family="Inter")),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#C6D2DF")),
    )
    fig.update_xaxes(showgrid=False, linecolor="#29394D", tickfont=dict(color="#A9B9CA"))
    fig.update_yaxes(gridcolor="rgba(130,155,180,0.12)", zeroline=False, tickfont=dict(color="#A9B9CA"))
    return fig


def show_chart(fig, data=None, name="chart", height=380, hover="closest"):
    """ONE shared helper: consistent style, hover tooltips, CSV download of the plotted data."""
    fig = chart_style(fig, height)
    fig.update_layout(hovermode=hover)
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False}, key=f"chart_{name}")
    if data is not None and len(data):
        st.download_button(
            "↓ CSV", data.to_csv(index=False).encode("utf-8"),
            file_name=f"{name}.csv", mime="text/csv", key=f"dl_{name}",
        )


def empty_msg():
    st.info("No data matches the current filters. Try selecting more months, a wider hour range, "
            "or at least one weekday — or press **Reset filters** in the sidebar.")


def footer():
    st.markdown("""
<div class="footer">
<strong style="color:#20E3CF">Smart Traffic Analytics</strong> | Built with Python, Hadoop, Pandas, Plotly and Streamlit
</div>
""", unsafe_allow_html=True)


# ============================================================
# 4. DATA LOADING AND NORMALISATION (cached, never crashes)
# ============================================================

def lookup_path():
    for p in (DATA_DIR / LOOKUP_NAME, ROOT / "DATASET" / LOOKUP_NAME):
        if p.exists():
            return p
    return None


@st.cache_data(show_spinner=False)
def read_csv_cached(path_str, mtime):
    """mtime is part of the cache key, so edited CSVs are reloaded automatically."""
    try:
        df = pd.read_csv(path_str)
    except Exception:
        return None
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def raw(key):
    p = DATA_DIR / FILES[key]
    return read_csv_cached(str(p), p.stat().st_mtime) if p.exists() else None


def to_num(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def prep(df, required, numeric=(), month=False):
    """Validate columns, coerce numbers, parse month -> 'period' (month start). Returns None if unusable."""
    if df is None:
        return None
    df = df.copy()
    if "locationid" in df.columns and "location_id" not in df.columns:
        df = df.rename(columns={"locationid": "location_id"})
    if any(c not in df.columns for c in required):
        return None
    df = to_num(df, numeric)
    if month:
        df["period"] = pd.to_datetime(df["month"].astype(str), errors="coerce").dt.to_period("M").dt.to_timestamp()
        df = df.dropna(subset=["period"])
    df = df.dropna(subset=[c for c in required if c in numeric])
    return df if len(df) else None


def norm_weekday(series):
    s = series.astype(str).str.strip()
    nums = pd.to_numeric(s, errors="coerce")
    if len(nums) and nums.notna().all():
        base = 0 if nums.min() == 0 else 1
        return nums.sub(base).astype(int).mod(7).map(lambda i: WEEKDAYS[i])
    short = {d[:3].lower(): d for d in WEEKDAYS}
    return s.map(lambda v: short.get(v[:3].lower(), v))


def norm_payment(series):
    n = pd.to_numeric(series, errors="coerce")
    return pd.Series(
        [str(int(x)) if pd.notna(x) else str(o) for x, o in zip(n, series)], index=series.index
    )


@st.cache_data(show_spinner=False)
def load_tables(signature):
    T = {}

    T["monthly"] = prep(raw("monthly"), ["month", "trips"], ["trips"], month=True)

    s = raw("summary")
    T["summary"] = None
    if s is not None and len(s):
        row = to_num(s.copy(), ["average_fare", "average_distance", "average_total_amount"]).iloc[0]
        T["summary"] = {
            k: (float(row.get(k, 0)) if pd.notna(row.get(k, 0)) else 0.0)
            for k in ["average_fare", "average_distance", "average_total_amount"]
        }

    ms_cols = ["trips", "sum_fare", "sum_distance", "sum_total_amount"]
    T["ms"] = prep(raw("ms"), ["month"] + ms_cols, ms_cols, month=True)

    h = prep(raw("hourly"), ["hour", "trips"], ["hour", "trips"])
    if h is not None:
        h["hour"] = h["hour"].astype(int)
        h = h.groupby("hour", as_index=False)["trips"].sum()
    T["hourly"] = h

    w = prep(raw("weekday"), ["weekday", "trips"], ["trips"])
    if w is not None:
        w["weekday"] = norm_weekday(w["weekday"])
        w = w.groupby("weekday", as_index=False)["trips"].sum()
    T["weekday"] = w

    mwh = prep(raw("mwh"), ["month", "weekday", "hour", "trips"], ["hour", "trips"], month=True)
    if mwh is not None:
        mwh["hour"] = mwh["hour"].astype(int)
        mwh["weekday"] = norm_weekday(mwh["weekday"])
    T["mwh"] = mwh

    for key, mkey in (("pickup", "mpick"), ("dropoff", "mdrop")):
        a = prep(raw(key), ["location_id", "trips"], ["location_id", "trips"])
        if a is not None:
            a["location_id"] = a["location_id"].astype(int)
        T[key] = a
        m = prep(raw(mkey), ["month", "location_id", "trips"], ["location_id", "trips"], month=True)
        if m is not None:
            m["location_id"] = m["location_id"].astype(int)
        T[mkey] = m

    p = prep(raw("payment"), ["payment_type", "trips"], ["trips"])
    if p is not None:
        p["payment_type"] = norm_payment(p["payment_type"])
    T["payment"] = p
    mp = prep(raw("mpay"), ["month", "payment_type", "trips"], ["trips"], month=True)
    if mp is not None:
        mp["payment_type"] = norm_payment(mp["payment_type"])
    T["mpay"] = mp

    T["passengers"] = prep(raw("passengers"), ["passenger_count", "trips"], ["passenger_count", "trips"])
    T["mpax"] = prep(raw("mpax"), ["month", "passenger_count", "trips"], ["passenger_count", "trips"], month=True)

    lk = None
    lp = lookup_path()
    if lp is not None:
        lk = read_csv_cached(str(lp), lp.stat().st_mtime)
        if lk is not None:
            lk = lk.rename(columns={"locationid": "location_id"})
            if "location_id" in lk.columns and "zone" in lk.columns:
                lk["location_id"] = pd.to_numeric(lk["location_id"], errors="coerce")
                lk = lk.dropna(subset=["location_id"])
                lk["location_id"] = lk["location_id"].astype(int)
            else:
                lk = None
    T["lookup"] = lk
    return T


def files_signature():
    sig = []
    for name in list(FILES.values()) + [LOOKUP_NAME]:
        p = DATA_DIR / name
        sig.append(p.stat().st_mtime if p.exists() else 0)
    lp = lookup_path()
    sig.append(lp.stat().st_mtime if lp else 0)
    return tuple(sig)


T = load_tables(files_signature())
HW_OK = T["mwh"] is not None  # hour/weekday filters can be honoured


def enrich_zones(df):
    """Add Zone name + Borough from lookup if available."""
    df = df.copy()
    lk = T["lookup"]
    if lk is not None:
        cols = [c for c in ["location_id", "borough", "zone", "service_zone"] if c in lk.columns]
        df = df.merge(lk[cols].drop_duplicates("location_id"), on="location_id", how="left")
    zone = df["zone"] if "zone" in df.columns else pd.Series(np.nan, index=df.index, dtype=object)
    bor = df["borough"] if "borough" in df.columns else pd.Series(np.nan, index=df.index, dtype=object)
    df["Zone"] = zone.fillna("Zone " + df["location_id"].astype(int).astype(str))
    df["Borough"] = bor.fillna("Unknown")
    return df


# Monthly summary: real file if present, otherwise built from monthly_trips + all-time averages
ms_is_fallback = False
if T["ms"] is not None:
    ms_all = T["ms"].groupby("period", as_index=False)[["trips", "sum_fare", "sum_distance", "sum_total_amount"]].sum()
elif T["monthly"] is not None:
    ms_all = T["monthly"].groupby("period", as_index=False)["trips"].sum()
    sm = T["summary"] or {"average_fare": 0, "average_distance": 0, "average_total_amount": 0}
    ms_all["sum_fare"] = ms_all["trips"] * sm["average_fare"]
    ms_all["sum_distance"] = ms_all["trips"] * sm["average_distance"]
    ms_all["sum_total_amount"] = ms_all["trips"] * sm["average_total_amount"]
    ms_is_fallback = True
else:
    ms_all = None

if ms_all is None:
    st.markdown("""
<div class="hero"><div class="eyebrow">DATA INTELLIGENCE • NYC TAXI</div>
<h1>Smart Traffic Analytics</h1>
<p>No monthly data found. Place <b>monthly_summary.csv</b> (or <b>monthly_trips.csv</b>) inside the <b>data/</b> folder next to app.py.</p></div>
""", unsafe_allow_html=True)
    footer()
    st.stop()

ms_all = ms_all.sort_values("period").reset_index(drop=True)
all_periods = ms_all["period"].tolist()


# ============================================================
# 5. SIDEBAR FILTERS (year, months, hours, weekdays, reset)
# ============================================================

years = sorted(ms_all["period"].dt.year.unique().astype(int).tolist())
YEAR_OPTIONS = ["All"] + years

DEFAULTS = {
    "f_year": "All",
    "f_months": list(range(1, 13)),
    "f_hours": (0, 23),
    "f_weekdays": list(WEEKDAYS),
}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, list(v) if isinstance(v, list) else v)
if st.session_state["f_year"] not in YEAR_OPTIONS:
    st.session_state["f_year"] = "All"


def reset_filters():
    for k, v in DEFAULTS.items():
        st.session_state[k] = list(v) if isinstance(v, list) else v


st.sidebar.markdown("## 🚕 SMART TRAFFIC")
st.sidebar.caption("NYC TAXI DEMAND INTELLIGENCE")
st.sidebar.divider()
st.sidebar.markdown("### Dashboard Filters")
st.sidebar.selectbox("Year", YEAR_OPTIONS, key="f_year")
st.sidebar.multiselect(
    "Months", list(range(1, 13)), key="f_months",
    format_func=lambda x: datetime(2000, x, 1).strftime("%B"),
)
st.sidebar.slider("Hour range", 0, 23, key="f_hours")
st.sidebar.multiselect("Weekdays", WEEKDAYS, key="f_weekdays")
st.sidebar.button("↺ Reset filters", on_click=reset_filters, use_container_width=True)

F = {
    "year": st.session_state["f_year"],
    "months": sorted(st.session_state["f_months"]),
    "hours": tuple(st.session_state["f_hours"]),
    "weekdays": [d for d in WEEKDAYS if d in st.session_state["f_weekdays"]],
}
hw_active = F["hours"] != (0, 23) or len(F["weekdays"]) < 7


def month_mask(df, use_year=True):
    m = df["period"].dt.month.isin(F["months"])
    if use_year and F["year"] != "All":
        m &= df["period"].dt.year.eq(F["year"])
    return m


def sel(df, use_year=True):
    return None if df is None else df[month_mask(df, use_year)]


ms_sel = sel(ms_all)
sel_periods = ms_sel["period"].tolist()
no_data = ms_sel.empty or not F["weekdays"]


# ============================================================
# 6. CORE COMPUTATIONS (everything recomputed from the filters)
# ============================================================

def filter_notes(month_level, hour_applies, weekday_applies):
    """Never silently ignore a filter: show a badge for what a chart cannot honour."""
    if not month_level:
        badge(ALLTIME)
    ignored = []
    if F["hours"] != (0, 23) and not hour_applies:
        ignored.append("hour range")
    if len(F["weekdays"]) < 7 and not weekday_applies:
        ignored.append("weekday")
    if ignored:
        badge("Not applied to this chart: " + " & ".join(ignored) + " filter")


def kpi_calc(df):
    """WEIGHTED averages: sum / trips (never an average of averages)."""
    if df is None or df.empty:
        return {"trips": 0.0, "fare": 0.0, "dist": 0.0, "total": 0.0, "fpm": 0.0, "months": 0}
    t = float(df["trips"].sum())
    sf = float(df["sum_fare"].sum())
    sd = float(df["sum_distance"].sum())
    sa = float(df["sum_total_amount"].sum())
    return {"trips": t, "fare": safe_divide(sf, t), "dist": safe_divide(sd, t),
            "total": safe_divide(sa, t), "fpm": safe_divide(sf, sd), "months": len(df)}


def trips_by_month(periods, apply_hw=True):
    if HW_OK and apply_hw and hw_active:
        d = T["mwh"]
        d = d[d["period"].isin(periods) & d["weekday"].isin(F["weekdays"]) & d["hour"].between(*F["hours"])]
        return d.groupby("period", as_index=False)["trips"].sum().sort_values("period")
    return ms_all[ms_all["period"].isin(periods)][["period", "trips"]].sort_values("period")


def hourly_df(periods, apply_hw=True):
    lo, hi = F["hours"] if apply_hw else (0, 23)
    wd = F["weekdays"] if apply_hw else WEEKDAYS
    if HW_OK:
        d = T["mwh"]
        d = d[d["period"].isin(periods) & d["weekday"].isin(wd) & d["hour"].between(lo, hi)]
        return d.groupby("hour", as_index=False)["trips"].sum().sort_values("hour")
    h = T["hourly"]
    if h is None:
        return pd.DataFrame(columns=["hour", "trips"])
    return h[h["hour"].between(lo, hi)].sort_values("hour").copy()


def weekday_df(periods, apply_hw=True):
    lo, hi = F["hours"] if apply_hw else (0, 23)
    wd = F["weekdays"] if apply_hw else WEEKDAYS
    if HW_OK:
        d = T["mwh"]
        d = d[d["period"].isin(periods) & d["weekday"].isin(wd) & d["hour"].between(lo, hi)]
        out = d.groupby("weekday", as_index=False)["trips"].sum()
    else:
        w = T["weekday"]
        if w is None:
            return pd.DataFrame(columns=["weekday", "trips"])
        out = w[w["weekday"].isin(wd)].copy()
    out["weekday"] = pd.Categorical(out["weekday"], categories=WEEKDAYS, ordered=True)
    out = out.sort_values("weekday")
    out["weekday"] = out["weekday"].astype(str)
    return out


def extremes(df, col):
    if df is None or df.empty or df["trips"].sum() <= 0:
        return None
    tot = df["trips"].sum()
    hi = df.loc[df["trips"].idxmax()]
    lo = df.loc[df["trips"].idxmin()]
    return {"peak": hi[col], "peak_share": hi["trips"] / tot * 100, "quiet": lo[col]}


def zone_table(kind, periods):
    mkey, akey = ("mpick", "pickup") if kind == "pickup" else ("mdrop", "dropoff")
    if T[mkey] is not None:
        d = T[mkey][T[mkey]["period"].isin(periods)]
        d = d.groupby("location_id", as_index=False)["trips"].sum()
        return enrich_zones(d), True
    if T[akey] is not None:
        return enrich_zones(T[akey].groupby("location_id", as_index=False)["trips"].sum()), False
    return None, False


def scope_text():
    yr = f"{years[0]}–{years[-1]}" if F["year"] == "All" else str(F["year"])
    ms = F["months"]
    if len(ms) == 12:
        m = "all months"
    elif len(ms) <= 4:
        m = ", ".join(datetime(2000, x, 1).strftime("%b") for x in ms)
    else:
        m = f"{len(ms)} selected months"
    return f"{yr} ({m})"


K = kpi_calc(ms_sel)
tm_sel = trips_by_month(sel_periods)
total_trips = float(tm_sel["trips"].sum()) if not tm_sel.empty else 0.0

hourly_sel = hourly_df(sel_periods)
weekday_sel = weekday_df(sel_periods)
H = extremes(hourly_sel, "hour")
H0 = extremes(hourly_df(all_periods, apply_hw=False), "hour")
D = extremes(weekday_sel, "weekday")
D0 = extremes(weekday_df(all_periods, apply_hw=False), "weekday")

peak_hour_text = hour_label(H["peak"]) if H else "N/A"
busy_day = D["peak"] if D else "N/A"

weekend_share = None
if not weekday_sel.empty and weekday_sel["trips"].sum() > 0:
    weekend_share = weekday_sel[weekday_sel["weekday"].isin(["Saturday", "Sunday"])]["trips"].sum() / weekday_sel["trips"].sum() * 100

best_month = None
if not tm_sel.empty:
    best_row = tm_sel.loc[tm_sel["trips"].idxmax()]
    best_month = best_row["period"].strftime("%B %Y")

pk_sel, pk_month_level = zone_table("pickup", sel_periods)
top_zone = None
if pk_sel is not None and not pk_sel.empty:
    top_zone = pk_sel.groupby("Zone")["trips"].sum().idxmax()

# Baseline for KPI deltas: same months of previous year if possible, else all-data average
def get_baseline():
    if F["year"] != "All":
        prev = ms_all[(ms_all["period"].dt.year == F["year"] - 1) & ms_all["period"].dt.month.isin(F["months"])]
        if not prev.empty:
            return kpi_calc(prev), f"vs same months {F['year'] - 1}", "total"
    return kpi_calc(ms_all), "vs all-data average", "per_month"


BASE, BASE_LABEL, BASE_MODE = get_baseline()
if BASE_MODE == "total":
    trips_delta = pct_change(K["trips"], BASE["trips"])
else:
    trips_delta = pct_change(safe_divide(K["trips"], K["months"]), safe_divide(BASE["trips"], BASE["months"]))


# ============================================================
# 7. ACTIVE FILTER CHIPS + SIDEBAR SUMMARY DOWNLOAD
# ============================================================

def chip(label, value):
    return f'<span class="chip"><b>{esc(label.upper())}</b>{esc(value)}</span>'


mon_txt = "All" if len(F["months"]) == 12 else (", ".join(datetime(2000, m, 1).strftime("%b") for m in F["months"]) or "None")
wd_txt = "All" if len(F["weekdays"]) == 7 else (", ".join(d[:3] for d in F["weekdays"]) or "None")
chips_html = '<div class="chips">' + "".join([
    chip("Year", F["year"]),
    chip("Months", mon_txt),
    chip("Hours", f"{F['hours'][0]:02d}:00–{F['hours'][1]:02d}:59"),
    chip("Weekdays", wd_txt),
]) + "</div>"


def build_summary_text():
    lines = [
        "SMART TRAFFIC ANALYTICS — CURRENT VIEW SUMMARY",
        "Historical NYC Yellow Taxi analytics (not live traffic)",
        "=" * 52,
        f"Filters: year={F['year']}, months={mon_txt}, hours={F['hours'][0]:02d}:00-{F['hours'][1]:02d}:59, weekdays={wd_txt}",
        "",
    ]
    if no_data:
        lines.append("No data matches the current filters.")
        return "\n".join(lines)
    lines += [
        f"Total trips: {total_trips:,.0f}",
        f"Average fare (weighted): ${K['fare']:.2f}",
        f"Average distance (weighted): {K['dist']:.2f} mi",
        f"Average total amount (weighted): ${K['total']:.2f}",
        f"Fare per mile: ${K['fpm']:.2f}",
        f"Peak hour: {peak_hour_text}",
        f"Busiest weekday: {busy_day}",
        f"Highest-demand month: {best_month or 'N/A'}",
        f"Leading pickup zone: {top_zone or 'N/A'}",
        f"Estimated revenue (trips x average total, estimate based on averages): ${total_trips * K['total']:,.0f}",
    ]
    if ms_is_fallback:
        lines.append("Note: averages are all-time (monthly_summary.csv not found).")
    return "\n".join(lines)


st.sidebar.divider()
st.sidebar.download_button(
    "↓ Summary of current view (.txt)", build_summary_text().encode("utf-8"),
    file_name="traffic_view_summary.txt", mime="text/plain", use_container_width=True,
)
st.sidebar.divider()
st.sidebar.markdown("### Data Source")
st.sidebar.info(
    f"NYC Yellow Taxi Trip Records\n\n{years[0]} – {years[-1]} · {len(all_periods)} months\n\nHistorical demand analytics"
)


# ============================================================
# 8. HEADER
# ============================================================

st.markdown("""
<div class="hero">
<div class="eyebrow">DATA INTELLIGENCE • NYC • HISTORICAL TAXI DEMAND</div>
<h1>Smart Traffic Analytics</h1>
<p>NYC Taxi Demand Intelligence | Hadoop MapReduce Analytics Platform</p>
</div>
""", unsafe_allow_html=True)
st.markdown(chips_html, unsafe_allow_html=True)


# ============================================================
# 9. TAB FUNCTIONS
# ============================================================

# ---------- TAB 1: OVERVIEW ----------
def tab_overview():
    section_title("Executive Overview", "Every figure is recomputed from the sidebar filters.")
    if ms_is_fallback:
        badge("Averages are all-time (add monthly_summary.csv to enable filtering)")
    if hw_active and not HW_OK:
        badge("Hour/weekday filters need month_weekday_hour.csv to change these KPIs")
    elif hw_active:
        cap("Hour/weekday filters change trip counts; fare and distance averages are computed per month.")

    ms_sorted = ms_sel.sort_values("period")
    spark_trips = tm_sel["trips"].tolist()
    if ms_is_fallback:
        spark_fare = spark_dist = spark_total = None
    else:
        spark_fare = (ms_sorted["sum_fare"] / ms_sorted["trips"]).tolist()
        spark_dist = (ms_sorted["sum_distance"] / ms_sorted["trips"]).tolist()
        spark_total = (ms_sorted["sum_total_amount"] / ms_sorted["trips"]).tolist()

    cols = st.columns(6)
    with cols[0]:
        kpi("Total trips", number(total_trips), f"{K['months']} month(s) selected", trips_delta, BASE_LABEL, spark=spark_trips)
    with cols[1]:
        kpi("Average fare", f"${number(K['fare'], 2)}", "Weighted per trip",
            pct_change(K["fare"], BASE["fare"]), BASE_LABEL, spark=spark_fare)
    with cols[2]:
        kpi("Avg distance", f"{number(K['dist'], 2)} mi", "Weighted per trip",
            pct_change(K["dist"], BASE["dist"]), BASE_LABEL, spark=spark_dist)
    with cols[3]:
        kpi("Avg total", f"${number(K['total'], 2)}", "Including additional charges",
            pct_change(K["total"], BASE["total"]), BASE_LABEL, spark=spark_total)
    with cols[4]:
        pp = (H["peak_share"] - H0["peak_share"]) if H and H0 else None
        kpi("Peak hour", peak_hour_text, f"{H['peak_share']:.1f}% of trips" if H else "",
            pp, "pts vs all-data", unit="", spark=hourly_sel["trips"].tolist() if H else None)
    with cols[5]:
        pp = (D["peak_share"] - D0["peak_share"]) if D and D0 else None
        kpi("Busiest day", busy_day, f"{D['peak_share']:.1f}% of trips" if D else "",
            pp, "pts vs all-data", unit="", spark=weekday_sel["trips"].tolist() if D else None)

    st.divider()

    # Story mode
    section_title("Story Mode", "A plain-language reading of the current view.")
    s1 = (f"For {scope_text()}, the data records {number(total_trips)} yellow-taxi trips, "
          f"with an average fare of ${K['fare']:.2f} over {K['dist']:.2f} miles per trip.")
    s2 = (f"Demand is highest around {peak_hour_text} and {busy_day} is the busiest day, "
          f"while weekends carry {weekend_share:.0f}% of trips." if weekend_share is not None and H
          else "Hourly and weekday patterns are not available for this selection.")
    s3 = (f"{best_month} is the strongest month in this view"
          + (f", and {top_zone} is the leading pickup zone." if top_zone else ".")) if best_month else ""
    st.markdown(f'<div class="story-card">{esc(" ".join([s1, s2, s3]))}</div>', unsafe_allow_html=True)

    st.divider()
    col1, col2 = st.columns([1.7, 1])

    with col1:
        section_title("Monthly Demand Trend")
        filter_notes(True, HW_OK, HW_OK)
        d = tm_sel.sort_values("period")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=d["period"], y=d["trips"], mode="lines+markers", name="Trips",
            line=dict(color=TEAL, width=3),
            hovertemplate="%{x|%b %Y}<br>Trips: %{y:,.0f}<extra></extra>",
        ))
        pk = d.loc[d["trips"].idxmax()]
        fig.add_trace(go.Scatter(
            x=[pk["period"]], y=[pk["trips"]], mode="markers+text", name="Peak month",
            text=["Peak"], textposition="top center", marker=dict(color=ORANGE, size=14),
            hovertemplate="Peak: %{x|%b %Y}<br>Trips: %{y:,.0f}<extra></extra>",
        ))
        fig.update_layout(title="Monthly Taxi Trips")
        show_chart(fig, d.rename(columns={"period": "month"}), "monthly_trend", 390)

    with col2:
        section_title("Year-over-Year Growth")
        tm_all = trips_by_month(all_periods)
        tm_all = tm_all[tm_all["period"].dt.month.isin(F["months"])].copy()
        tm_all["year"] = tm_all["period"].dt.year
        tm_all["m"] = tm_all["period"].dt.month
        ys = sorted(tm_all["year"].unique())
        if len(ys) >= 2:
            y0, y1 = ys[0], ys[-1]
            common = set(tm_all[tm_all["year"] == y0]["m"]) & set(tm_all[tm_all["year"] == y1]["m"])
            like = tm_all[tm_all["m"].isin(common)]
            annual = like.groupby("year", as_index=False)["trips"].sum()
            annual["year"] = annual["year"].astype(str)
            if not annual.empty:
                fig = px.bar(annual, x="year", y="trips", color="year", text_auto=".3s",
                             title=f"Trips by Year ({len(common)} comparable months)",
                             labels={"year": "Year", "trips": "Trips"})
                show_chart(fig, annual, "yearly_trips", 330)
                a = annual.loc[annual["year"] == str(y0), "trips"].sum()
                b = annual.loc[annual["year"] == str(y1), "trips"].sum()
                g = pct_change(b, a)
                if g is not None:
                    st.metric(f"{y1} vs {y0} growth", f"{g:+.2f}%")
                cap("Like-for-like: only months present in both years (respecting the month filter); the year filter is not applied here.")
            else:
                st.info("No months are present in both years for this selection.")
        else:
            st.info("Year comparison needs at least two years of data.")

    section_title("Key Findings", "Recalculated on every filter change.")
    findings = []
    if H:
        findings.append(f"Peak demand occurs at {peak_hour_text}; the quietest hour is {int(H['quiet']):02d}:00.")
    if D:
        findings.append(f"{busy_day} is the busiest weekday in this selection.")
    if best_month:
        findings.append(f"The highest-demand month in this selection is {best_month}.")
    if K["fpm"]:
        findings.append(f"Fare per mile (sum of fares ÷ sum of distance) is ${K['fpm']:.2f}.")
    if top_zone:
        findings.append(f"The leading pickup zone is {top_zone}.")
    for item in findings[:5]:
        insight(item)
    if not findings:
        st.info("Not enough data to generate findings.")

    if st.button("Refresh dashboard data"):
        st.cache_data.clear()
        st.rerun()


# ---------- TAB 2: DEMAND ----------
def tab_demand():
    section_title("Demand Patterns", "When is taxi demand highest?")

    chart_type = st.radio("Hourly chart type", ["Bar", "Line"], horizontal=True, key="hour_chart_type")
    filter_notes(HW_OK, True, HW_OK)
    if hourly_sel.empty:
        st.info("Hourly data is not available for this selection.")
    else:
        h = hourly_sel.copy()
        h["hour_label"] = h["hour"].apply(hour_label)
        pk = h["trips"].max()
        h["color"] = h["trips"].apply(lambda x: ORANGE if x == pk else TEAL)
        if chart_type == "Bar":
            fig = px.bar(h, x="hour_label", y="trips", color="color", color_discrete_map="identity",
                         title="Hourly Taxi Demand", labels={"hour_label": "Hour", "trips": "Trips"},
                         hover_data={"color": False, "hour": True})
        else:
            fig = px.line(h, x="hour_label", y="trips", markers=True, title="Hourly Taxi Demand",
                          labels={"hour_label": "Hour", "trips": "Trips"})
            fig.update_traces(line=dict(color=TEAL, width=3))
        show_chart(fig, h[["hour", "trips"]], "hourly_demand")
        cap(f"Peak hour: {peak_hour_text} | Quietest hour: {int(H['quiet']):02d}:00" if H else "")

    col1, col2 = st.columns(2)
    with col1:
        section_title("Weekday Demand")
        filter_notes(HW_OK, HW_OK, True)
        if weekday_sel.empty:
            st.info("Weekday data is not available for this selection.")
        else:
            fig = px.bar(weekday_sel, x="weekday", y="trips", color="trips", title="Trips by Day of Week",
                         color_continuous_scale=["#145B61", TEAL], labels={"weekday": "Day", "trips": "Trips"})
            show_chart(fig, weekday_sel, "weekday_demand")
            hi = weekday_sel.loc[weekday_sel["trips"].idxmax()]
            lo = weekday_sel.loc[weekday_sel["trips"].idxmin()]
            insight(f"Busiest day: {hi['weekday']}. Quietest day: {lo['weekday']}.")

    with col2:
        section_title("Weekday vs Weekend")
        filter_notes(HW_OK, HW_OK, True)
        if weekday_sel.empty:
            st.info("Weekday data is not available for this selection.")
        else:
            wk = weekday_sel[~weekday_sel["weekday"].isin(["Saturday", "Sunday"])]["trips"].sum()
            we = weekday_sel[weekday_sel["weekday"].isin(["Saturday", "Sunday"])]["trips"].sum()
            split = pd.DataFrame({"type": ["Weekdays", "Weekends"], "trips": [wk, we]})
            fig = px.pie(split, names="type", values="trips", hole=0.65, title="Demand Distribution",
                         color_discrete_sequence=[TEAL, ORANGE])
            show_chart(fig, split, "weekday_vs_weekend")

    section_title("Month-over-Month Change")
    filter_notes(True, HW_OK, HW_OK)
    tm_all = trips_by_month(all_periods).sort_values("period").copy()
    tm_all["change"] = tm_all["trips"].diff()
    tm_all["change_pct"] = tm_all["trips"].pct_change() * 100
    mom = tm_all[tm_all["period"].isin(sel_periods)].dropna(subset=["change"]).copy()
    if mom.empty:
        st.info("No month-over-month change available (needs a month with a previous month in the data).")
    else:
        mom["direction"] = mom["change"].apply(lambda x: "Increase" if x >= 0 else "Decrease")
        fig = px.bar(mom, x="period", y="change", color="direction",
                     color_discrete_map={"Increase": GREEN, "Decrease": RED},
                     title="Monthly Change in Trip Volume (vs previous calendar month)",
                     hover_data={"change_pct": ":.2f"}, labels={"period": "Month", "change": "Change in trips"})
        show_chart(fig, mom.rename(columns={"period": "month"}), "mom_change")

    section_title("Year Comparison by Month")
    filter_notes(True, HW_OK, HW_OK)
    cmp_df = tm_all[tm_all["period"].dt.month.isin(F["months"])].copy()
    cmp_df["Year"] = cmp_df["period"].dt.year.astype(str)
    cmp_df["Month"] = cmp_df["period"].dt.strftime("%b")
    if cmp_df.empty:
        st.info("No data for the selected months.")
    else:
        fig = px.bar(cmp_df, x="Month", y="trips", color="Year", barmode="group",
                     category_orders={"Month": MONTH_ORDER}, title="Monthly Demand by Year",
                     labels={"trips": "Trips"})
        show_chart(fig, cmp_df[["period", "trips"]].rename(columns={"period": "month"}), "year_comparison")
        cap("The year filter is not applied here so both years stay comparable; months and hour/weekday filters are.")

    section_title("Weekday × Hour Heatmap")
    if not HW_OK:
        st.info("Add **month_weekday_hour.csv** to data/ to enable the weekday × hour heatmap.")
    else:
        d = T["mwh"]
        d = d[d["period"].isin(sel_periods) & d["weekday"].isin(F["weekdays"]) & d["hour"].between(*F["hours"])]
        if d.empty:
            st.info("No data for the heatmap with these filters.")
        else:
            pv = d.pivot_table(index="weekday", columns="hour", values="trips", aggfunc="sum").reindex(
                [w for w in WEEKDAYS if w in F["weekdays"]])
            fig = px.imshow(pv, aspect="auto", color_continuous_scale=["#0B1A2A", "#145B61", TEAL, ORANGE],
                            labels=dict(x="Hour", y="Day", color="Trips"), title="Trips by Weekday and Hour")
            show_chart(fig, pv.reset_index(), "weekday_hour_heatmap", 420)


# ---------- TAB 3: ZONES ----------
def tab_zones():
    section_title("Geographical Demand Intelligence", "Busiest taxi pickup and drop-off zones for the selected months.")
    top_n = st.slider("Number of zones to display", 5, 20, 10, key="top_n")
    has_lookup = T["lookup"] is not None
    if not has_lookup:
        cap("Add taxi_zone_lookup.csv to data/ (or DATASET/) to show zone names and boroughs.")

    dr_sel, dr_month_level = zone_table("dropoff", sel_periods)

    col1, col2 = st.columns(2)
    for col, (title, tbl, ml, name) in zip(
        (col1, col2),
        (("Pickup", pk_sel, pk_month_level, "pickup"), ("Drop-off", dr_sel, dr_month_level, "dropoff")),
    ):
        with col:
            section_title(f"Top {top_n} {title} Zones")
            if tbl is None or tbl.empty:
                st.info(f"No {name} zone data for this selection (needs {'month_' + name[:4] if False else ''}"
                        f"{'month_pickup.csv' if name == 'pickup' else 'month_dropoff.csv'} or the all-time file).")
                continue
            filter_notes(ml, False, False)
            top = tbl.nlargest(top_n, "trips").sort_values("trips")
            fig = px.bar(top, x="trips", y="Zone", color="Borough" if has_lookup else None, orientation="h",
                         title=f"{title} Demand", hover_data={"location_id": True, "Borough": True, "trips": ":,"},
                         labels={"trips": "Trips", "Zone": "Taxi Zone"})
            show_chart(fig, top[["location_id", "Zone", "Borough", "trips"]], f"top_{name}_zones", 470)

    col1, col2 = st.columns(2)
    for col, (title, tbl, name) in zip((col1, col2), (("Pickup", pk_sel, "pickup"), ("Drop-off", dr_sel, "dropoff"))):
        with col:
            section_title(f"{title} Share by Borough")
            if not has_lookup:
                st.info("Borough share needs taxi_zone_lookup.csv.")
            elif tbl is None or tbl.empty:
                st.info("No data for this selection.")
            else:
                b = tbl.groupby("Borough", as_index=False)["trips"].sum()
                fig = px.pie(b, names="Borough", values="trips", hole=0.62,
                             title=f"{title} Borough Distribution", color_discrete_sequence=COLORS)
                show_chart(fig, b, f"{name}_borough_share")

    section_title("Search a Taxi Zone")
    if pk_sel is None or pk_sel.empty:
        st.info("Zone search needs pickup data.")
    else:
        by_zone = pk_sel.groupby("Zone")["trips"].sum().sort_values(ascending=False)
        selected_zone = st.selectbox("Choose a pickup zone", by_zone.index.tolist(), key="zone_search")
        zone_trips = by_zone[selected_zone]
        rank = int(by_zone.rank(method="min", ascending=False)[selected_zone])
        share = safe_divide(zone_trips, by_zone.sum()) * 100
        c1, c2, c3 = st.columns(3)
        with c1:
            kpi("Zone trips", number(zone_trips), selected_zone)
        with c2:
            kpi("Zone rank", f"#{rank}", f"of {len(by_zone)} pickup zones")
        with c3:
            kpi("Trip share", f"{share:.2f}%", "Of all pickup trips in selection")
        if T["mpick"] is not None:
            ids = pk_sel[pk_sel["Zone"] == selected_zone]["location_id"].tolist()
            tr = T["mpick"][T["mpick"]["location_id"].isin(ids) & T["mpick"]["period"].isin(sel_periods)]
            tr = tr.groupby("period", as_index=False)["trips"].sum()
            if len(tr) > 1:
                fig = px.line(tr, x="period", y="trips", markers=True, title=f"{selected_zone}: pickups by month",
                              labels={"period": "Month", "trips": "Trips"})
                show_chart(fig, tr.rename(columns={"period": "month"}), "zone_search_trend", 300)

    section_title("Airport Pickup Share Over Months")
    if T["mpick"] is None:
        st.info("Airport share over time needs **month_pickup.csv**.")
    else:
        d = T["mpick"][T["mpick"]["period"].isin(sel_periods)]
        if d.empty:
            st.info("No data for this selection.")
        else:
            tot = d.groupby("period")["trips"].sum()
            a = d[d["location_id"].isin(AIRPORTS)].copy()
            a["Airport"] = a["location_id"].map(AIRPORTS)
            a = a.groupby(["period", "Airport"], as_index=False)["trips"].sum()
            a["share_pct"] = a["trips"] / a["period"].map(tot) * 100
            if a.empty:
                st.info("No airport pickups found in this selection.")
            else:
                fig = px.line(a, x="period", y="share_pct", color="Airport", markers=True,
                              title="Airport share of all pickups (JFK, LaGuardia, Newark)",
                              labels={"period": "Month", "share_pct": "Share of pickups (%)"},
                              hover_data={"trips": ":,"})
                show_chart(fig, a.rename(columns={"period": "month"}), "airport_share", 360, "x unified")
                total_air = a["trips"].sum() / d["trips"].sum() * 100
                insight(f"Airports account for {total_air:.2f}% of pickups in this selection.")

    section_title("Top Growing Pickup Zones")
    if T["mpick"] is None:
        st.info("Zone growth needs **month_pickup.csv**.")
    else:
        d = T["mpick"][T["mpick"]["period"].dt.month.isin(F["months"])].copy()
        d["year"] = d["period"].dt.year
        d["m"] = d["period"].dt.month
        ys = sorted(d["year"].unique())
        if len(ys) < 2:
            st.info("Growth needs at least two years of data.")
        else:
            y0, y1 = int(ys[0]), int(ys[-1])
            common = set(d[d["year"] == y0]["m"]) & set(d[d["year"] == y1]["m"])
            d = d[d["m"].isin(common)]
            g = d.pivot_table(index="location_id", columns="year", values="trips", aggfunc="sum", fill_value=0)
            if y0 not in g.columns or y1 not in g.columns or g.empty:
                st.info("Not enough comparable data.")
            else:
                g["change"] = g[y1] - g[y0]
                g["growth_pct"] = g["change"] / g[y0].replace(0, np.nan) * 100
                g = enrich_zones(g.reset_index())
                top = g.nlargest(top_n, "change").sort_values("change")
                top = top.rename(columns={y0: f"trips_{y0}", y1: f"trips_{y1}"})
                fig = px.bar(top, x="change", y="Zone", orientation="h",
                             title=f"Largest absolute growth in pickups, {y0} → {y1} ({len(common)} comparable months)",
                             hover_data={"growth_pct": ":.1f", f"trips_{y0}": ":,", f"trips_{y1}": ":,"},
                             labels={"change": "Change in pickups", "Zone": "Taxi Zone"})
                fig.update_traces(marker_color=GREEN)
                show_chart(fig, top[["location_id", "Zone", f"trips_{y0}", f"trips_{y1}", "change", "growth_pct"]],
                           "top_growing_zones", 450)
                cap("Compares the same calendar months in both years; the year filter is not applied.")


# ---------- TAB 4: PAYMENTS & PASSENGERS ----------
def tab_payments():
    section_title("Payment & Passenger Intelligence", "Customer payment behaviour and passenger distribution.")

    if T["mpay"] is not None:
        pay = T["mpay"][T["mpay"]["period"].isin(sel_periods)].groupby("payment_type", as_index=False)["trips"].sum()
        pay_ml = True
    elif T["payment"] is not None:
        pay = T["payment"].copy()
        pay_ml = False
    else:
        pay, pay_ml = None, False

    if T["mpax"] is not None:
        pax = T["mpax"][T["mpax"]["period"].isin(sel_periods)].groupby("passenger_count", as_index=False)["trips"].sum()
        pax_ml = True
    elif T["passengers"] is not None:
        pax = T["passengers"].copy()
        pax_ml = False
    else:
        pax, pax_ml = None, False

    col1, col2 = st.columns(2)
    with col1:
        section_title("Payment Method Distribution")
        if pay is None or pay.empty:
            st.info("No payment data for this selection.")
        else:
            filter_notes(pay_ml, False, False)
            pay["payment_label"] = pay["payment_type"].map(PAY_LABELS).fillna(pay["payment_type"])
            fig = px.pie(pay, names="payment_label", values="trips", hole=0.64, title="Payment Type Share",
                         color_discrete_sequence=COLORS)
            show_chart(fig, pay, "payment_share")
    with col2:
        section_title("Passenger Count Distribution")
        if pax is None or pax.empty:
            st.info("No passenger data for this selection.")
        else:
            filter_notes(pax_ml, False, False)
            fig = px.bar(pax, x="passenger_count", y="trips", color="trips", title="Trips by Passenger Count",
                         color_continuous_scale=["#145B61", TEAL],
                         labels={"passenger_count": "Passengers", "trips": "Trips"})
            show_chart(fig, pax, "passenger_counts")

    section_title("Payment Trend by Month")
    if T["mpay"] is None:
        st.info("Payment trend needs **month_payment.csv**.")
    else:
        d = T["mpay"][T["mpay"]["period"].isin(sel_periods)].copy()
        if d.empty:
            st.info("No data for this selection.")
        else:
            d["Payment"] = d["payment_type"].map(PAY_LABELS).fillna(d["payment_type"])
            d = d.groupby(["period", "Payment"], as_index=False)["trips"].sum()
            fig = px.line(d, x="period", y="trips", color="Payment", markers=True, title="Payment Methods Over Time",
                          labels={"period": "Month", "trips": "Trips"})
            show_chart(fig, d.rename(columns={"period": "month"}), "payment_trend", 380, "x unified")

    if pay is not None and not pay.empty and pay["trips"].sum() > 0:
        card = pay[pay["payment_label"] == "Credit card"]["trips"].sum()
        cash = pay[pay["payment_label"] == "Cash"]["trips"].sum()
        tot = pay["trips"].sum()
        insight(f"Credit card accounts for {card / tot * 100:.2f}% and cash for {cash / tot * 100:.2f}% of payment records in this view.")
    if pax is not None and not pax.empty and pax["trips"].sum() > 0:
        solo = pax[pax["passenger_count"] == 1]["trips"].sum()
        insight(f"Single-passenger trips make up {solo / pax['trips'].sum() * 100:.2f}% of passenger-count records in this view.")


# ---------- TAB 5: INSIGHTS ----------
def tab_insights():
    section_title("Demand Intelligence & Operational Insights", "Auto-generated from the current filters.")
    filter_notes(HW_OK, True, HW_OK)

    if hourly_sel.empty or hourly_sel["trips"].sum() <= 0:
        st.info("Not enough hourly data for insights with these filters.")
    else:
        hs = hourly_sel
        ratio = safe_divide(hs["trips"].max(), hs["trips"].min())
        insight(f"Peak-hour demand is about {ratio:.2f}× the quietest hour in this selection.")
        rush = hs[hs["hour"].between(7, 9) | hs["hour"].between(17, 20)]["trips"].sum()
        insight(f"Morning (7–9 AM) and evening (5–8 PM) rush periods account for {rush / hs['trips'].sum() * 100:.2f}% of the trips in the selected hours.")
        if weekend_share is not None:
            insight(f"Weekends account for {weekend_share:.1f}% of trips; {busy_day} is the busiest day.")
        if best_month:
            insight(f"{best_month} is the highest-demand month in the selection.")
        if len(ms_sel) and BASE["fare"]:
            d = pct_change(K["fare"], BASE["fare"])
            if d is not None:
                insight(f"Average fare is ${K['fare']:.2f}, {abs(d):.1f}% {'above' if d >= 0 else 'below'} the baseline ({BASE_LABEL.replace('vs ', '')}).")

        col1, col2 = st.columns(2)
        with col1:
            section_title("Best 5 Hours to Drive")
            for _, r in hs.nlargest(5, "trips").iterrows():
                insight(f"{hour_label(r['hour'])} — {number(r['trips'])} trips")
        with col2:
            section_title("5 Quietest Hours")
            for _, r in hs.nsmallest(5, "trips").iterrows():
                insight(f"{hour_label(r['hour'])} — {number(r['trips'])} trips")

        section_title("High-Demand Hours")
        cap("Hours with trip counts above the 75th percentile of the selection.")
        hi = hs[hs["trips"] > hs["trips"].quantile(0.75)]
        st.write(", ".join(f"{int(x):02d}:00" for x in hi["hour"]) or "No hours above the threshold.")

        section_title("Fleet Capacity Planner")
        fleet = st.number_input("Enter your available taxi fleet", min_value=1, max_value=100000, value=100, step=10, key="fleet")
        fd = hs.copy()
        fd["suggested_taxis"] = (fd["trips"] / fd["trips"].sum() * fleet).round().astype(int)
        fig = px.bar(fd, x="hour", y="suggested_taxis", color="suggested_taxis", title="Illustrative Fleet Allocation by Hour",
                     color_continuous_scale=["#145B61", TEAL], labels={"hour": "Hour", "suggested_taxis": "Suggested taxis"})
        show_chart(fig, fd[["hour", "trips", "suggested_taxis"]], "fleet_planner")
        cap("Proportional allocation of your fleet by historical hourly trip share. Not a prediction of taxis actually required.")

    section_title("Fare & Revenue Estimates")
    c1, c2 = st.columns(2)
    with c1:
        kpi("Average fare per mile", f"${number(K['fpm'], 2)}", "Sum of fares ÷ sum of distance",
            pct_change(K["fpm"], BASE["fpm"]), BASE_LABEL)
    with c2:
        kpi("Estimated total revenue", f"${number(total_trips * K['total'], 0)}", "Estimate based on averages")
    cap("Estimate based on averages: total trips × weighted average total amount. Not an audited revenue figure.")


# ---------- TAB 6: COMPARE ----------
def period_label(periods):
    ps = sorted(periods)
    if len(ps) <= 3:
        return ", ".join(p.strftime("%b %Y") for p in ps)
    return f"{ps[0].strftime('%b %Y')} – {ps[-1].strftime('%b %Y')} ({len(ps)} months)"


def tab_compare():
    section_title("Compare Two Periods", "Pick any months for Period A and Period B (e.g. May 2024 vs May 2025).")
    opts = all_periods
    defA = [opts[-13]] if len(opts) >= 13 else [opts[0]]
    defB = [opts[-1]]
    c1, c2 = st.columns(2)
    with c1:
        a_sel = st.multiselect("Period A", opts, default=defA, format_func=lambda p: p.strftime("%b %Y"), key="cmp_a")
    with c2:
        b_sel = st.multiselect("Period B", opts, default=defB, format_func=lambda p: p.strftime("%b %Y"), key="cmp_b")
    if not a_sel or not b_sel:
        st.info("Select at least one month for both Period A and Period B.")
        return

    KA = kpi_calc(ms_all[ms_all["period"].isin(a_sel)])
    KB = kpi_calc(ms_all[ms_all["period"].isin(b_sel)])
    la, lb = period_label(a_sel), period_label(b_sel)
    per_month = len(a_sel) != len(b_sel)

    ha, hb = hourly_df(a_sel), hourly_df(b_sel)
    ea, eb = extremes(ha, "hour"), extremes(hb, "hour")
    wa, wb = weekday_df(a_sel), weekday_df(b_sel)
    da, db = extremes(wa, "weekday"), extremes(wb, "weekday")

    if per_month:
        cap("The periods have different numbers of months, so the trips change compares trips per month.")
    trips_d = pct_change(safe_divide(KB["trips"], KB["months"]), safe_divide(KA["trips"], KA["months"])) if per_month \
        else pct_change(KB["trips"], KA["trips"])

    cols = st.columns(6)
    with cols[0]:
        kpi("Total trips", number(KB["trips"]), f"A: {number(KA['trips'])}", trips_d, "B vs A")
    with cols[1]:
        kpi("Average fare", f"${number(KB['fare'], 2)}", f"A: ${number(KA['fare'], 2)}", pct_change(KB["fare"], KA["fare"]), "B vs A")
    with cols[2]:
        kpi("Avg distance", f"{number(KB['dist'], 2)} mi", f"A: {number(KA['dist'], 2)} mi", pct_change(KB["dist"], KA["dist"]), "B vs A")
    with cols[3]:
        kpi("Avg total", f"${number(KB['total'], 2)}", f"A: ${number(KA['total'], 2)}", pct_change(KB["total"], KA["total"]), "B vs A")
    with cols[4]:
        kpi("Fare per mile", f"${number(KB['fpm'], 2)}", f"A: ${number(KA['fpm'], 2)}", pct_change(KB["fpm"], KA["fpm"]), "B vs A")
    with cols[5]:
        kpi("Peak hour", hour_label(eb["peak"]) if eb else "N/A", f"A: {hour_label(ea['peak']) if ea else 'N/A'}")

    table = pd.DataFrame({
        "Metric": ["Total trips", "Trips per month", "Average fare ($)", "Average distance (mi)",
                   "Average total ($)", "Fare per mile ($)", "Peak hour", "Busiest weekday"],
        f"A · {la}": [number(KA["trips"]), number(safe_divide(KA["trips"], KA["months"])), f"{KA['fare']:.2f}", f"{KA['dist']:.2f}",
                      f"{KA['total']:.2f}", f"{KA['fpm']:.2f}", hour_label(ea["peak"]) if ea else "N/A", da["peak"] if da else "N/A"],
        f"B · {lb}": [number(KB["trips"]), number(safe_divide(KB["trips"], KB["months"])), f"{KB['fare']:.2f}", f"{KB['dist']:.2f}",
                      f"{KB['total']:.2f}", f"{KB['fpm']:.2f}", hour_label(eb["peak"]) if eb else "N/A", db["peak"] if db else "N/A"],
        "Change (B vs A)": [
            f"{pct_change(KB['trips'], KA['trips']):+.2f}%" if pct_change(KB["trips"], KA["trips"]) is not None else "—",
            f"{pct_change(safe_divide(KB['trips'], KB['months']), safe_divide(KA['trips'], KA['months'])):+.2f}%"
            if pct_change(safe_divide(KB["trips"], KB["months"]), safe_divide(KA["trips"], KA["months"])) is not None else "—",
            f"{pct_change(KB['fare'], KA['fare']):+.2f}%" if pct_change(KB["fare"], KA["fare"]) is not None else "—",
            f"{pct_change(KB['dist'], KA['dist']):+.2f}%" if pct_change(KB["dist"], KA["dist"]) is not None else "—",
            f"{pct_change(KB['total'], KA['total']):+.2f}%" if pct_change(KB["total"], KA["total"]) is not None else "—",
            f"{pct_change(KB['fpm'], KA['fpm']):+.2f}%" if pct_change(KB["fpm"], KA["fpm"]) is not None else "—",
            "—", "—"],
    })
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.download_button("↓ CSV", table.to_csv(index=False).encode("utf-8"), file_name="period_comparison.csv",
                       mime="text/csv", key="dl_period_comparison")

    if not HW_OK:
        st.info("Hourly and weekday comparison needs **month_weekday_hour.csv**.")
        return
    cap("Hourly and weekday charts also respect the sidebar hour-range and weekday filters.")
    mode = st.radio("Chart values", ["Trips", "Share of period (%)"], horizontal=True, key="cmp_mode")

    def combine(a, b, col):
        a = a.copy(); b = b.copy()
        a["Period"] = f"A · {la}"; b["Period"] = f"B · {lb}"
        d = pd.concat([a, b], ignore_index=True)
        if mode != "Trips" and not d.empty:
            d["trips"] = d["trips"] / d.groupby("Period")["trips"].transform("sum") * 100
        return d

    ycol = "Trips" if mode == "Trips" else "Share of period (%)"
    col1, col2 = st.columns(2)
    with col1:
        d = combine(ha, hb, "hour")
        if d.empty:
            st.info("No hourly data for these periods.")
        else:
            fig = px.line(d, x="hour", y="trips", color="Period", markers=True, title="Hourly Comparison",
                          labels={"hour": "Hour", "trips": ycol})
            show_chart(fig, d, "compare_hourly", 380, "x unified")
    with col2:
        d = combine(wa, wb, "weekday")
        if d.empty:
            st.info("No weekday data for these periods.")
        else:
            fig = px.bar(d, x="weekday", y="trips", color="Period", barmode="group", title="Weekday Comparison",
                         category_orders={"weekday": WEEKDAYS}, labels={"weekday": "Day", "trips": ycol})
            show_chart(fig, d, "compare_weekday", 380)


# ---------- TAB 7: FORECAST & ANOMALIES ----------
def tab_forecast():
    section_title("Forecast & Anomalies", "Based on the full monthly history; months in your current selection are flagged in the table.")
    cap("Estimate, not a guarantee. Uses total monthly trips (hour/weekday filters are not applied here).")
    s = ms_all[["period", "trips"]].sort_values("period").reset_index(drop=True)
    if len(s) < 6:
        st.info("At least 6 months of data are needed for anomaly detection and forecasting.")
        return

    med = s["trips"].rolling(5, center=True, min_periods=3).median()
    resid = s["trips"] - med
    sd = resid.std(ddof=0)
    s["rolling_median"] = med
    s["z_score"] = resid / sd if sd else 0.0
    s["anomaly"] = s["z_score"].abs() > 1.5
    s["in_selection"] = s["period"].isin(sel_periods)

    method = st.radio("Forecast method", ["Seasonal naive (same month last year)", "Linear trend"], horizontal=True, key="fc_method")
    n = 3
    last = s["period"].iloc[-1]
    future = [last + pd.DateOffset(months=i) for i in range(1, n + 1)]
    x = np.arange(len(s))
    coef = np.polyfit(x, s["trips"].values, 1)
    linear_vals = [coef[0] * (len(s) - 1 + i) + coef[1] for i in range(1, n + 1)]
    if method.startswith("Seasonal") and len(s) >= 12:
        hist = dict(zip(s["period"], s["trips"]))
        vals = []
        for f, lv in zip(future, linear_vals):
            ref = hist.get(f - pd.DateOffset(years=1), np.nan)
            vals.append(lv if pd.isna(ref) else ref)
    else:
        vals = linear_vals
    fc = pd.DataFrame({"month": future, "forecast_trips": [round(v) for v in vals]})

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=s["period"], y=s["trips"], mode="lines+markers", name="Actual",
                             line=dict(color=TEAL, width=3),
                             hovertemplate="%{x|%b %Y}<br>Trips: %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=s["period"], y=s["rolling_median"], mode="lines", name="Rolling median",
                             line=dict(color=MUTED, dash="dot"),
                             hovertemplate="%{x|%b %Y}<br>Median: %{y:,.0f}<extra></extra>"))
    an = s[s["anomaly"]]
    if not an.empty:
        fig.add_trace(go.Scatter(x=an["period"], y=an["trips"], mode="markers", name="Anomaly",
                                 marker=dict(color=RED, size=13, symbol="diamond"),
                                 hovertemplate="%{x|%b %Y}<br>Trips: %{y:,.0f}<extra>Anomaly</extra>"))
    fig.add_trace(go.Scatter(x=[last] + future, y=[s["trips"].iloc[-1]] + fc["forecast_trips"].tolist(),
                             mode="lines+markers", name="Forecast (estimate)",
                             line=dict(color=ORANGE, dash="dash", width=3),
                             hovertemplate="%{x|%b %Y}<br>Forecast: %{y:,.0f}<extra></extra>"))
    fig.update_layout(title="Monthly Trips, Anomalies and Next-3-Month Estimate")
    show_chart(fig, s.rename(columns={"period": "month"}), "forecast_anomalies", 420, "x unified")
    st.markdown('<span class="badge">Estimate, not a guarantee</span>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        section_title("Next 3 Months (estimate)")
        show = fc.copy()
        show["month"] = show["month"].dt.strftime("%b %Y")
        show["forecast_trips"] = show["forecast_trips"].map(lambda v: f"{v:,.0f}")
        st.dataframe(show, use_container_width=True, hide_index=True)
        cap("Seasonal naive repeats the same month of the previous year; linear trend extends a fitted straight line.")
    with col2:
        section_title("Flagged Months")
        cap("Flagged when more than 1.5 standard deviations away from a 5-month rolling median.")
        flag = s[s["anomaly"]].copy()
        if flag.empty:
            st.success("No months deviate strongly from the trend.")
        else:
            flag["month"] = flag["period"].dt.strftime("%b %Y")
            flag["Direction"] = np.where(flag["z_score"] > 0, "Above trend", "Below trend")
            flag["z_score"] = flag["z_score"].round(2)
            flag["In selection"] = flag["in_selection"].map({True: "Yes", False: "No"})
            st.dataframe(flag[["month", "trips", "z_score", "Direction", "In selection"]],
                         use_container_width=True, hide_index=True)


# ---------- TAB 8: DATA QUALITY ----------
def tab_quality():
    section_title("Data Quality & Cross-Validation", "Cross-check total trips across every output dataset (unfiltered).")
    totals = {}
    for key in ["monthly", "ms", "mwh", "hourly", "weekday", "pickup", "dropoff", "mpick", "mdrop",
                "payment", "mpay", "passengers", "mpax"]:
        df = T.get(key)
        if df is not None and "trips" in df.columns:
            totals[FILES[key]] = float(df["trips"].sum())

    if not totals:
        st.warning("No aggregation files available for validation.")
    else:
        ref_name = FILES["ms"] if FILES["ms"] in totals else FILES["monthly"] if FILES["monthly"] in totals else list(totals)[0]
        ref = totals[ref_name]
        rows = []
        for name, val in totals.items():
            diff = val - ref
            if name == ref_name:
                status = "Reference"
            elif abs(diff) < 1:
                status = "✅ Match"
            else:
                status = f"⚠ Difference ({diff:+,.0f})"
            rows.append({"Dataset": name, "Total trips": int(val), "Difference vs reference": int(diff), "Validation": status})
        out = pd.DataFrame(rows)
        st.dataframe(out, use_container_width=True, hide_index=True)
        st.download_button("↓ CSV", out.to_csv(index=False).encode("utf-8"), file_name="data_quality_totals.csv",
                           mime="text/csv", key="dl_dq_totals")
        cap(f"Reference: {ref_name}. Small differences can come from records outside the 24 months or invalid rows.")
        if all(abs(r["Difference vs reference"]) < 1 for r in rows):
            st.success("All available files agree on the total trip count.")

    section_title("CSV File Inventory")
    inv = []
    for key, filename in list(FILES.items()) + [("lookup", LOOKUP_NAME)]:
        p = lookup_path() if key == "lookup" else DATA_DIR / filename
        if p is not None and p.exists():
            df = read_csv_cached(str(p), p.stat().st_mtime)
            inv.append({
                "File": filename,
                "Rows": len(df) if df is not None else "—",
                "Size (KB)": round(p.stat().st_size / 1024, 2),
                "Last Modified": datetime.fromtimestamp(p.stat().st_mtime).strftime("%d %b %Y, %I:%M %p"),
                "Status": "Available" if df is not None else "Read error",
            })
        else:
            inv.append({"File": filename, "Rows": "—", "Size (KB)": "—", "Last Modified": "—",
                        "Status": "Missing (optional)" if key == "lookup" else "Missing"})
    st.dataframe(pd.DataFrame(inv), use_container_width=True, hide_index=True)

    missing_ml = [FILES[k] for k in ["ms", "mwh", "mpick", "mdrop", "mpay", "mpax"] if T.get(k) is None]
    if missing_ml:
        st.markdown(
            '<div class="warning-card">Month-level files not loaded: ' + esc(", ".join(missing_ml)) +
            ". Charts that depend on them show the all-time fallback with a badge.</div>",
            unsafe_allow_html=True,
        )


# ---------- TAB 9: PIPELINE ----------
def tab_pipeline():
    section_title("Big Data Processing Architecture")
    st.markdown('<div class="eyebrow">END-TO-END DATA ENGINEERING WORKFLOW</div>', unsafe_allow_html=True)
    steps = [
        ("01", "NYC TLC", "Parquet records"),
        ("02", "PyArrow", "Batch preparation"),
        ("03", "HDFS", "Distributed storage"),
        ("04", "MapReduce", "Mapper + Reducer"),
        ("05", "CSV", "Aggregated outputs"),
        ("06", "Streamlit", "Analytics dashboard"),
    ]
    cols = st.columns(6)
    for i, (num_id, title, desc) in enumerate(steps):
        with cols[i]:
            st.markdown(
                f'<div class="pipeline-step"><small>{num_id}</small><br><strong>{title}</strong><br><small>{desc}</small></div>',
                unsafe_allow_html=True,
            )

    st.divider()
    section_title("Hadoop Environment")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi("Parquet files", "24", "12 months × 2 years")
    with c2:
        kpi("Raw data size", "~1.5 GB", "NYC TLC records")
    with c3:
        kpi("Hadoop version", "3.5.0", "Apache Hadoop")
    with c4:
        kpi("Processing", "HDFS + MR", "Hadoop Streaming")
    cap("The pipeline statistics above describe the configured project environment. The dashboard does not execute Hadoop jobs.")


# ============================================================
# 10. TABS (in order) + GLOBAL FOOTER
# ============================================================

tabs = st.tabs([
    "◈ Overview", "◷ Demand", "⌖ Zones", "◉ Payments & Passengers", "✦ Insights",
    "⇄ Compare", "∿ Forecast & Anomalies", "✓ Data Quality", "⚙ Pipeline",
])

with tabs[0]:
    empty_msg() if no_data else tab_overview()
with tabs[1]:
    empty_msg() if no_data else tab_demand()
with tabs[2]:
    empty_msg() if no_data else tab_zones()
with tabs[3]:
    empty_msg() if no_data else tab_payments()
with tabs[4]:
    empty_msg() if no_data else tab_insights()
with tabs[5]:
    tab_compare()
with tabs[6]:
    tab_forecast()
with tabs[7]:
    tab_quality()
with tabs[8]:
    tab_pipeline()

footer()