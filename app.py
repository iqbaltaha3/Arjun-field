import time
from datetime import datetime, timezone
import html
import os

import pandas as pd
import streamlit as st

from config import (
    APP_NAME,
    LOCATION_INTERVAL_SECONDS,
    ADMIN_ID,
    ADMIN_PASSWORD,
)
import db
from location import get_location, parse_location
from sarvam_voice import transcribe
from llm import extract

st.set_page_config(
    page_title=APP_NAME,
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def inject_css():
    st.markdown(
        """
        <style>
        :root {
            --arjun-bg: #090c0f;
            --arjun-panel: #11171c;
            --arjun-panel-2: #151c22;
            --arjun-border: #26313a;
            --arjun-gold: #ffc300;
            --arjun-gold-2: #f7ad17;
            --arjun-white: #f6f7f8;
            --arjun-muted: #9aa5ae;
            --arjun-green: #34c77b;
            --arjun-red: #ff5d5d;
            --arjun-blue: #51a7ff;
            --arjun-purple: #a58bff;
        }

        .stApp {
            background:
                radial-gradient(circle at 18% 10%, rgba(255,195,0,.08), transparent 24%),
                radial-gradient(circle at 85% 0%, rgba(81,167,255,.05), transparent 22%),
                var(--arjun-bg);
            color: var(--arjun-white);
        }

        .block-container {
            max-width: 1440px;
            padding: 1.3rem 1.8rem 3rem;
        }

        header[data-testid="stHeader"] { background: rgba(9,12,15,.92); }
        div[data-testid="stToolbar"] { visibility: hidden; height: 0; }
        footer { visibility: hidden; }

        /* Typography */
        h1, h2, h3, h4, p, span, label, div {
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        h1, h2, h3 { letter-spacing: -0.02em; }
        .caption-muted { color: var(--arjun-muted); font-size: .9rem; }
        .gold { color: var(--arjun-gold); }

        /* Buttons */
        .stButton > button {
            min-height: 48px;
            border-radius: 12px;
            border: 1px solid #36414a;
            background: #172027;
            color: #f4f6f7;
            font-weight: 700;
            transition: transform .15s ease, border-color .15s ease, background .15s ease;
        }
        .stButton > button:hover {
            border-color: var(--arjun-gold);
            background: #1c252d;
            transform: translateY(-1px);
        }
        .stButton > button[kind="primary"] {
            background: linear-gradient(180deg, #ffd24a 0%, #ffb800 100%);
            color: #111;
            border: none;
        }
        .stButton > button[kind="primary"]:hover { background: linear-gradient(180deg, #ffe07c 0%, #ffc21e 100%); }

        /* Inputs */
        div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="select"] > div {
            background: #10161b !important;
            border-color: #2c3740 !important;
        }
        input, textarea { color: #f6f7f8 !important; }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: #0d1318;
            border-right: 1px solid #1e272e;
        }
        section[data-testid="stSidebar"] .block-container { padding: 1rem .8rem; }
        section[data-testid="stSidebar"] .stRadio label {
            padding: .55rem .65rem;
            border-radius: 9px;
        }
        
        /* Native tabs */
        button[data-baseweb="tab"] { color: #aeb7bf; }
        button[data-baseweb="tab"][aria-selected="true"] { color: var(--arjun-gold); }

        /* Metric cards */
        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, #141b21 0%, #11171c 100%);
            border: 1px solid var(--arjun-border);
            border-radius: 16px;
            padding: 1rem 1.1rem;
        }
        [data-testid="stMetricValue"] { color: var(--arjun-gold); }
        [data-testid="stMetricLabel"] { color: #b3bdc5; }

        /* Dataframes */
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--arjun-border);
            border-radius: 14px;
            overflow: hidden;
        }

        /* Audio */
        audio { width: 100%; border-radius: 12px; }

        .brand-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: .65rem;
            font-size: 1.55rem;
            line-height: 1;
            font-weight: 900;
            letter-spacing: -.04em;
        }
        .brand-mark {
            width: 36px;
            height: 36px;
            border-radius: 11px;
            display: grid;
            place-items: center;
            background: linear-gradient(145deg, #ffd34d, #ffb400);
            color: #161616;
            font-size: 1.15rem;
            box-shadow: 0 5px 22px rgba(255,195,0,.15);
        }
        .brand-sub {
            color: var(--arjun-muted);
            font-size: .82rem;
            margin-left: 2.8rem;
            margin-top: -.25rem;
        }

        .hero-card {
            background:
                radial-gradient(circle at 76% 0%, rgba(255,195,0,.13), transparent 26%),
                linear-gradient(135deg, #111a20 0%, #0e1419 100%);
            border: 1px solid #25313a;
            border-radius: 20px;
            padding: 1.2rem 1.25rem;
            box-shadow: 0 12px 35px rgba(0,0,0,.22);
        }
        .hero-title { font-size: 1.6rem; font-weight: 850; margin-bottom: .15rem; }
        .hero-meta { color: #a8b2ba; font-size: .93rem; }
        .pill {
            display: inline-flex;
            align-items: center;
            gap: .35rem;
            padding: .32rem .6rem;
            border-radius: 999px;
            font-size: .77rem;
            font-weight: 800;
            border: 1px solid #35414a;
            background: #172027;
            color: #e9edf0;
        }
        .pill-gold { border-color: rgba(255,195,0,.35); background: rgba(255,195,0,.09); color: #ffd95f; }
        .pill-green { border-color: rgba(52,199,123,.3); background: rgba(52,199,123,.1); color: #5fe09a; }
        .pill-red { border-color: rgba(255,93,93,.3); background: rgba(255,93,93,.09); color: #ff8e8e; }

        .identity-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }
        .identity-left { display: flex; gap: .85rem; align-items: center; }
        .avatar {
            width: 52px;
            height: 52px;
            border-radius: 50%;
            background: #efe6d3;
            color: #25211a;
            display: grid;
            place-items: center;
            font-size: 1.35rem;
            border: 2px solid rgba(255,195,0,.35);
        }
        .identity-name { font-size: 1rem; font-weight: 800; }
        .identity-role { color: #9ba6ae; font-size: .82rem; }

        .booth-card {
            background: #12191f;
            border: 1px solid var(--arjun-border);
            border-radius: 17px;
            padding: 1rem 1.1rem;
        }
        .booth-title { font-size: 1rem; font-weight: 800; margin-bottom: .7rem; }
        .kv-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:.8rem 1.1rem; }
        .kv-label { color:#818e98; font-size:.72rem; text-transform:uppercase; letter-spacing:.06em; }
        .kv-value { font-weight:700; font-size:.93rem; margin-top:.14rem; }

        .status-card {
            border-radius: 18px;
            padding: 1rem 1.05rem;
            border: 1px solid var(--arjun-border);
            background: #11181e;
        }
        .status-off { background: linear-gradient(135deg, rgba(255,195,0,.08), rgba(255,195,0,.03)); border-color: rgba(255,195,0,.2); }
        .status-on { background: linear-gradient(135deg, rgba(52,199,123,.10), rgba(52,199,123,.035)); border-color: rgba(52,199,123,.24); }
        .status-line { display:flex; gap:.7rem; align-items:center; }
        .status-icon {
            width: 42px; height: 42px; border-radius: 13px; display:grid; place-items:center;
            background:#182128; font-size:1.2rem; border:1px solid #2d3841;
        }
        .status-name { font-weight:850; }
        .status-text { color:#9da8b0; font-size:.82rem; margin-top:.12rem; }

        .gps-box {
            background: #0f151a;
            border: 1px solid #27333c;
            border-radius: 15px;
            padding: .8rem .9rem;
        }
        .gps-top { display:flex; justify-content:space-between; gap:1rem; }
        .gps-title { font-weight:800; }
        .gps-coord { color:#a1acb4; font-size:.78rem; margin-top:.2rem; }
        .accuracy { color:#57d998; font-weight:800; font-size:.8rem; }

        .record-card {
            background: linear-gradient(180deg, #161e25 0%, #11171c 100%);
            border: 1px solid #293640;
            border-radius: 20px;
            padding: 1.2rem;
        }
        .record-orb {
            width: 108px;
            height: 108px;
            margin: .4rem auto .75rem;
            display:grid;
            place-items:center;
            border-radius:50%;
            background: radial-gradient(circle at 50% 45%, #252d34 0%, #182026 58%, #10161a 100%);
            border: 1px solid rgba(255,195,0,.5);
            box-shadow: inset 0 0 0 12px rgba(255,195,0,.03), 0 0 0 6px rgba(255,195,0,.04), 0 16px 36px rgba(0,0,0,.3);
            font-size: 2.25rem;
        }
        .record-title { text-align:center; font-size:1.35rem; font-weight:850; }
        .record-help { text-align:center; color:#929ea7; font-size:.84rem; max-width:520px; margin:.25rem auto 1rem; }

        .feature-row { display:grid; grid-template-columns:repeat(3,1fr); gap:.7rem; }
        .feature-card {
            background:#11181e; border:1px solid #27323b; border-radius:15px; padding:.8rem .75rem; text-align:center;
        }
        .feature-icon { font-size:1.25rem; }
        .feature-label { font-size:.76rem; color:#b6c0c7; margin-top:.2rem; }

        .report-card {
            background:#11181e; border:1px solid #26313a; border-radius:16px; padding:1rem;
        }
        .report-head { display:flex; justify-content:space-between; gap:1rem; align-items:center; }
        .report-title { font-weight:800; }
        .report-meta { color:#87939c; font-size:.78rem; margin-top:.15rem; }
        .report-body { color:#dde2e6; font-size:.9rem; line-height:1.55; margin-top:.7rem; }

        .section-head { display:flex; justify-content:space-between; align-items:end; gap:1rem; margin:1.1rem 0 .7rem; }
        .section-title { font-size:1.1rem; font-weight:850; }
        .section-note { color:#8c989f; font-size:.8rem; }

        .admin-header {
            display:flex; justify-content:space-between; align-items:center; gap:1rem;
            background:linear-gradient(180deg,#141d23,#10161b);
            border:1px solid #27343d; border-radius:18px; padding:.85rem 1rem;
            margin-bottom:1rem;
        }
        .admin-header-left { display:flex; align-items:center; gap:.7rem; }
        .admin-title { font-size:1.12rem; font-weight:900; }
        .admin-sub { color:#87939b; font-size:.76rem; }

        .mini-card { background:#12191f; border:1px solid #26323b; border-radius:14px; padding:.85rem; }
        .mini-label { color:#818d96; font-size:.73rem; }
        .mini-value { font-size:1.15rem; font-weight:850; margin-top:.15rem; }
        .mini-note { color:#7ecf9f; font-size:.72rem; margin-top:.2rem; }

        .sidebar-brand { padding:.2rem .4rem .9rem; border-bottom:1px solid #1c252d; margin-bottom:.8rem; }
        .sidebar-name { font-weight:900; font-size:1.1rem; }
        .sidebar-sub { color:#7d8891; font-size:.72rem; margin-top:.2rem; }

        .login-shell {
            max-width: 760px;
            margin: 7vh auto 0;
        }
        .login-card {
            background: linear-gradient(180deg,#131b20,#0f151a);
            border:1px solid #28343d;
            border-radius:24px;
            padding:1.4rem;
            box-shadow:0 25px 70px rgba(0,0,0,.28);
        }
        .login-title { font-size:2.1rem; font-weight:900; letter-spacing:-.04em; }
        .login-sub { color:#8f9ba3; margin:.4rem 0 1.2rem; }

        @media (max-width: 850px) {
            .block-container { padding: .8rem .75rem 2rem; }
            .kv-grid { grid-template-columns:repeat(2,1fr); }
            .feature-row { grid-template-columns:1fr 1fr 1fr; }
            .hero-title { font-size:1.35rem; }
            .brand { font-size:1.35rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_css()
db.init_db()

for key, default in {
    "role": None,
    "worker_id": None,
    "session_id": None,
    "pending_location": None,
    "current_location": None,
    "draft_transcript": None,
    "draft_struct": None,
    "admin_page": "Dashboard",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def esc(value):
    return html.escape("" if value is None else str(value))


def logout():
    st.session_state.clear()
    st.rerun()


def logo_block(compact=False):
    subtitle = "Field Operations Platform" if not compact else ""
    st.markdown(
        f'''
        <div class="brand-row">
            <div>
                <div class="brand"><span class="brand-mark">📍</span> ARJUN <span class="gold">FIELD</span></div>
                <div class="brand-sub">{subtitle}</div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def login_page():
    st.markdown('<div class="login-shell">', unsafe_allow_html=True)
    st.markdown(
        '''
        <div class="login-card">
            <div class="brand"><span class="brand-mark">📍</span> ARJUN <span class="gold">FIELD</span></div>
            <div class="login-title" style="margin-top:.9rem">Field Intelligence, made simple.</div>
            <div class="login-sub">Fast reporting for the field. Clear command view for the admin. Location sharing is explicit and session-based.</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )
    mode = st.radio("", ["Worker", "Admin"], horizontal=True, key="login_mode", label_visibility="collapsed")
    if mode == "Worker":
        with st.container(border=True):
            st.subheader("Worker login")
            wid = st.text_input("Worker ID", placeholder="W001", key="worker_login_id")
            st.caption("Use the ID created by the admin.")
            if st.button("Continue as Worker →", type="primary", use_container_width=True, key="worker_login_button"):
                w = db.get_worker(wid.strip())
                if w and w["active"]:
                    st.session_state.role = "worker"
                    st.session_state.worker_id = w["worker_id"]
                    st.rerun()
                st.error("Invalid or inactive Worker ID.")
    else:
        with st.container(border=True):
            st.subheader("Admin login")
            aid = st.text_input("Admin ID", key="admin_login_id")
            pw = st.text_input("Admin password", type="password", key="admin_login_password")
            if st.button("Enter Command →", type="primary", use_container_width=True, key="admin_login_button"):
                if aid.strip() == ADMIN_ID and pw == ADMIN_PASSWORD:
                    st.session_state.role = "admin"
                    st.rerun()
                st.error("Invalid admin credentials.")
    if ADMIN_PASSWORD == "change-me-now":
        st.warning("Change ADMIN_PASSWORD in .env before deployment.")
    st.markdown('</div>', unsafe_allow_html=True)


def location_from_component():
    return parse_location(get_location())


def worker_header(w):
    st.markdown(
        f'''
        <div class="hero-card">
            <div class="identity-row">
                <div class="identity-left">
                    <div class="avatar">👤</div>
                    <div>
                        <div class="identity-name">{esc(w['name'])}</div>
                        <div class="identity-role">Field Coordinator · Uttar Pradesh</div>
                    </div>
                </div>
                <div class="pill pill-gold">Booth {esc(w['booth_id'])}</div>
            </div>
            <div style="height:.95rem"></div>
            <div class="hero-title">Today’s field workspace</div>
            <div class="hero-meta">Keep reports short, factual and easy to verify. Arjun will structure the details for you.</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def booth_details(w):
    district = os.getenv("ARJUN_DISTRICT", "Uttar Pradesh")
    st.markdown(
        f'''
        <div class="booth-card">
            <div class="booth-title">📍 Booth details · बूथ विवरण</div>
            <div class="kv-grid">
                <div><div class="kv-label">District · जिला</div><div class="kv-value">{esc(district)}</div></div>
                <div><div class="kv-label">Assembly / Region · क्षेत्र</div><div class="kv-value">{esc(w['region'])}</div></div>
                <div><div class="kv-label">Booth · बूथ</div><div class="kv-value">{esc(w['booth_id'])}</div></div>
                <div><div class="kv-label">Area / क्षेत्र</div><div class="kv-value">{esc(w['area'])}</div></div>
                <div><div class="kv-label">Phone / संपर्क</div><div class="kv-value">{esc(w['phone']) or '—'}</div></div>
                <div><div class="kv-label">Field Mode · फील्ड मोड</div><div class="kv-value">Session based</div></div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def render_report_preview(d, transcript):
    activity = d.get("activity_type") or "Field observation"
    observation = d.get("observation") or "No observation captured."
    attendance = d.get("attendance_estimate")
    follow_up = d.get("follow_up") or ""
    st.markdown('<div class="section-head"><div class="section-title">Arjun understood</div><div class="section-note">Review before saving</div></div>', unsafe_allow_html=True)
    st.markdown(
        f'''
        <div class="report-card">
            <div class="report-head">
                <div>
                    <div class="report-title">{esc(activity)}</div>
                    <div class="report-meta">Structured from your voice note</div>
                </div>
                <span class="pill pill-green">Ready to save</span>
            </div>
            <div class="report-body">{esc(observation)}</div>
            <div class="feature-row" style="margin-top:.8rem">
                <div class="mini-card"><div class="mini-label">Attendance estimate</div><div class="mini-value">{esc(attendance if attendance is not None else '—')}</div></div>
                <div class="mini-card"><div class="mini-label">Follow-up</div><div class="mini-value" style="font-size:.92rem">{esc(follow_up or 'None')}</div></div>
                <div class="mini-card"><div class="mini-label">Audio storage</div><div class="mini-value" style="font-size:.92rem">Not stored</div></div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )
    with st.expander("View transcript"):
        st.write(transcript)


def worker_app():
    w = db.get_worker(st.session_state.worker_id)
    if not w:
        logout()
        return

    logo_block()
    left, right = st.columns([3.0, 1.0], gap="large")
    with left:
        worker_header(w)
    with right:
        if st.button("Logout", key="worker_logout", use_container_width=True):
            logout()

    st.write("")
    booth_details(w)
    st.write("")

    session = db.active_session(w["worker_id"])
    if session:
        st.markdown(
            '''
            <div class="status-card status-on">
                <div class="status-line">
                    <div class="status-icon">🟢</div>
                    <div>
                        <div class="status-name">FIELD MODE ACTIVE</div>
                        <div class="status-text">Location sharing is ON for this session.</div>
                    </div>
                </div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="mini-card"><div class="mini-label">Started</div><div class="mini-value" style="font-size:.95rem">{esc(session["started_at"])}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="mini-card"><div class="mini-label">GPS cadence</div><div class="mini-value" style="font-size:.95rem">Every {LOCATION_INTERVAL_SECONDS//60} min</div></div>', unsafe_allow_html=True)
        c3.markdown('<div class="mini-card"><div class="mini-label">Privacy</div><div class="mini-value" style="font-size:.95rem">Session only</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="section-head"><div class="section-title">📍 Current location</div><div class="section-note">Refresh while Field Mode is active</div></div>', unsafe_allow_html=True)
        loc = location_from_component()
        if loc:
            st.session_state["current_location"] = loc
            db.add_location(session["session_id"], w["worker_id"], *loc)
        else:
            loc = st.session_state.get("current_location")

        if loc:
            st.markdown(
                f'''
                <div class="gps-box">
                    <div class="gps-top">
                        <div>
                            <div class="gps-title">GPS connected</div>
                            <div class="gps-coord">{loc[0]:.6f}, {loc[1]:.6f}</div>
                        </div>
                        <div class="accuracy">± {loc[2]:.0f} m</div>
                    </div>
                </div>
                ''',
                unsafe_allow_html=True,
            )
        else:
            st.info("Use the location control below to refresh your GPS position.")

        c1, c2 = st.columns([3, 1])
        with c1:
            if st.button("Stop Field Mode", key="stop_field_mode", use_container_width=True):
                db.end_session(w["worker_id"])
                st.session_state.session_id = None
                st.rerun()
        with c2:
            st.caption("Your location is visible to the admin only while this session is active.")

        st.divider()
        st.markdown('<div class="section-head"><div class="section-title">🎙️ Field report</div><div class="section-note">Speak naturally · up to 10 minutes</div></div>', unsafe_allow_html=True)
        st.markdown(
            '''
            <div class="record-card">
                <div class="record-orb">🎙️</div>
                <div class="record-title">Record your field report</div>
                <div class="record-help">Explain what you observed in your own words. Arjun can process a multi-minute recording by splitting it into smaller transcription chunks automatically.</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

        audio = st.audio_input("🎙️ Record report", sample_rate=16000, key="field_audio")
        if audio:
            st.success("Recording captured. Ready for Arjun to understand it.")
            if st.button("✨ Understand recording", type="primary", use_container_width=True, key="understand_audio"):
                try:
                    with st.spinner("Arjun is transcribing and structuring your report…"):
                        transcript = transcribe(audio.getvalue())
                        structured = extract(transcript)
                    st.session_state["draft_transcript"] = transcript
                    st.session_state["draft_struct"] = structured
                except Exception as e:
                    st.error("Voice processing failed. The recording is still available in this session. Please try again.")
                    st.caption(str(e))

        with st.expander("⌨️ Type a report instead"):
            typed = st.text_area("Field note", placeholder="Describe what happened in your own words.", key="typed_note")
            if st.button("Understand typed note", key="understand_typed"):
                if typed.strip():
                    try:
                        st.session_state["draft_transcript"] = typed.strip()
                        st.session_state["draft_struct"] = extract(typed.strip())
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not understand note: {e}")
                else:
                    st.warning("Enter a field note first.")

        if st.session_state.get("draft_transcript"):
            d = st.session_state.get("draft_struct") or {}
            render_report_preview(d, st.session_state["draft_transcript"])
            if st.button("Save report →", type="primary", use_container_width=True, key="save_report"):
                loc = st.session_state.get("current_location") or (None, None, None)
                db.add_report(
                    {
                        "worker_id": w["worker_id"],
                        "session_id": session["session_id"],
                        "booth_id": w["booth_id"],
                        "region": w["region"],
                        "activity_type": d.get("activity_type", "field_observation"),
                        "observation": d.get("observation", ""),
                        "attendance_estimate": d.get("attendance_estimate"),
                        "follow_up": d.get("follow_up", ""),
                        "transcript": st.session_state["draft_transcript"],
                        "latitude": loc[0],
                        "longitude": loc[1],
                    }
                )
                st.session_state.pop("draft_transcript", None)
                st.session_state.pop("draft_struct", None)
                st.success("Report saved successfully.")
                st.rerun()

        st.markdown('<div class="section-head"><div class="section-title">📄 My reports</div><div class="section-note">Your latest field notes</div></div>', unsafe_allow_html=True)
        rows = db.worker_reports(w["worker_id"])
        if rows:
            for row in rows[:8]:
                r = dict(row)
                st.markdown(
                    f'''
                    <div class="report-card" style="margin-bottom:.65rem">
                        <div class="report-head">
                            <div>
                                <div class="report-title">{esc(r.get('activity_type') or 'Field observation')}</div>
                                <div class="report-meta">{esc(r.get('created_at') or '')}</div>
                            </div>
                            <span class="pill pill-gold">Saved</span>
                        </div>
                        <div class="report-body">{esc(r.get('observation') or 'No observation text.')}</div>
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No reports yet. Your first saved field report will appear here.")

        try:
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=LOCATION_INTERVAL_SECONDS * 1000, key="gps_refresh")
        except Exception:
            pass

    else:
        st.markdown(
            '''
            <div class="status-card status-off">
                <div class="status-line">
                    <div class="status-icon">🟡</div>
                    <div>
                        <div class="status-name">FIELD MODE OFF</div>
                        <div class="status-text">Location sharing is off. Start it only when you are working in the field.</div>
                    </div>
                </div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="section-head"><div class="section-title">📍 1. अपनी लोकेशन पाएं</div><div class="section-note">Get location before Field Mode</div></div>', unsafe_allow_html=True)
        st.info("नीचे location control दबाएं। जरूरत होने पर browser GPS permission मांगेगा।")
        pending_loc = location_from_component()
        if pending_loc:
            st.session_state["pending_location"] = pending_loc

        pending_loc = st.session_state.get("pending_location")
        if pending_loc:
            st.markdown(
                f'''
                <div class="gps-box">
                    <div class="gps-top">
                        <div>
                            <div class="gps-title">Location ready</div>
                            <div class="gps-coord">{pending_loc[0]:.6f}, {pending_loc[1]:.6f}</div>
                        </div>
                        <div class="accuracy">± {pending_loc[2]:.0f} m</div>
                    </div>
                </div>
                ''',
                unsafe_allow_html=True,
            )
        else:
            st.caption("No GPS position captured yet. Press the geolocation control above and wait for the result.")

        st.markdown('<div class="section-head"><div class="section-title">▶ 2. फील्ड मोड शुरू करें</div><div class="section-note">Session-only location sharing</div></div>', unsafe_allow_html=True)
        can_start = bool(pending_loc)
        if st.button("▶ फील्ड मोड शुरू करें", type="primary", use_container_width=True, disabled=not can_start, key="start_field_mode"):
            sid = db.start_session(w["worker_id"])
            db.add_location(sid, w["worker_id"], *pending_loc)
            st.session_state.session_id = sid
            st.session_state["current_location"] = pending_loc
            st.session_state.pop("pending_location", None)
            st.rerun()

        st.markdown('<div class="feature-row" style="margin-top:1rem"><div class="feature-card"><div class="feature-icon">📍</div><div class="feature-label">GPS · केवल session में</div></div><div class="feature-card"><div class="feature-icon">🎙️</div><div class="feature-label">आवाज़ से रिपोर्ट</div></div><div class="feature-card"><div class="feature-icon">🔒</div><div class="feature-label">Audio save नहीं</div></div></div>', unsafe_allow_html=True)


def admin_sidebar():
    with st.sidebar:
        st.markdown(
            '''
            <div class="sidebar-brand">
                <div class="brand"><span class="brand-mark">📍</span> ARJUN <span class="gold">FIELD</span></div>
                <div class="sidebar-sub">Command Center · उत्तर प्रदेश</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )
        page = st.radio(
            "",
            ["Dashboard", "Live workers", "Reports", "Workers"],
            key="admin_nav",
            label_visibility="collapsed",
        )
        st.markdown("---")
        st.caption("Admin")
        if st.button("Logout", use_container_width=True, key="admin_logout"):
            logout()
    return page


def admin_header():
    st.markdown(
        '''
        <div class="admin-header">
            <div class="admin-header-left">
                <div class="brand-mark">📍</div>
                <div><div class="admin-title">ARJUN FIELD · COMMAND</div><div class="admin-sub">Field operations dashboard · Uttar Pradesh</div></div>
            </div>
            <div><span class="pill pill-green">System online</span></div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def dashboard_view():
    total, active, reports, booths = db.stats()
    a, b, c, d = st.columns(4)
    a.metric("Registered workers", total if total is not None else 0)
    b.metric("Active now", active if active is not None else 0)
    c.metric("Reports today", reports if reports is not None else 0)
    d.metric("Booths reported", booths if booths is not None else 0)

    st.write("")
    st.markdown('<div class="section-head"><div class="section-title">Live operations</div><div class="section-note">Current worker positions and latest activity</div></div>', unsafe_allow_html=True)
    left, right = st.columns([1.5, 1], gap="large")
    with left:
        rows = db.latest_locations()
        if rows:
            data = [dict(r) for r in rows]
            df = pd.DataFrame(data)
            mapped = df.dropna(subset=["latitude", "longitude"])[["latitude", "longitude"]]
            if not mapped.empty:
                st.map(mapped, zoom=10, use_container_width=True)
            else:
                st.info("Workers are active but no valid map points are available yet.")
        else:
            st.info("No workers are currently in Field Mode.")
    with right:
        st.markdown('<div class="mini-card"><div class="mini-label">Live worker list</div><div class="mini-value">Who is active right now</div></div>', unsafe_allow_html=True)
        rows = db.latest_locations()
        if rows:
            for r0 in rows[:8]:
                r = dict(r0)
                st.markdown(
                    f'''
                    <div class="report-card" style="margin:.55rem 0;padding:.75rem">
                        <div class="report-head"><div><div class="report-title">{esc(r.get('name'))}</div><div class="report-meta">Booth {esc(r.get('booth_id'))} · {esc(r.get('region'))}</div></div><span class="pill pill-green">Online</span></div>
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No active workers.")


def live_workers_view():
    st.subheader("Live workers")
    st.caption("Workers currently visible because they have an active Field Mode session.")
    rows = db.latest_locations()
    if not rows:
        st.info("No workers are currently active.")
        return
    data = [dict(r) for r in rows]
    df = pd.DataFrame(data)
    st.dataframe(df[["worker_id", "name", "booth_id", "region", "started_at", "latitude", "longitude", "recorded_at"]], use_container_width=True, hide_index=True)
    mapped = df.dropna(subset=["latitude", "longitude"])[["latitude", "longitude"]]
    if not mapped.empty:
        st.map(mapped, zoom=10, use_container_width=True)


def reports_view():
    st.subheader("Field reports")
    rows = db.recent_reports()
    if rows:
        df = pd.DataFrame([dict(r) for r in rows])
        wanted = ["created_at", "name", "worker_id", "booth_id", "region", "activity_type", "observation", "attendance_estimate", "follow_up"]
        st.dataframe(df[[c for c in wanted if c in df.columns]], use_container_width=True, hide_index=True)
    else:
        st.info("No reports yet.")


def workers_view():
    st.subheader("Worker management")
    st.caption("Create, review and deactivate field workers.")
    with st.form("add_worker"):
        st.markdown("#### Add worker")
        x, y, z = st.columns(3)
        wid = x.text_input("Worker ID")
        name = y.text_input("Name")
        booth = z.text_input("Booth ID")
        r1, r2, r3 = st.columns(3)
        region = r1.text_input("Region")
        area = r2.text_input("Area")
        phone = r3.text_input("Phone")
        if st.form_submit_button("+ Create worker", type="primary"):
            try:
                db.add_worker(wid, name, booth, region, area, phone)
                st.success(f"Worker {wid} created.")
            except Exception as e:
                st.error(f"Could not create worker: {e}")

    workers = db.list_workers()
    if workers:
        df = pd.DataFrame([dict(r) for r in workers])
        cols = ["worker_id", "name", "booth_id", "region", "area", "phone", "active", "created_at"]
        st.dataframe(df[[c for c in cols if c in df.columns]], use_container_width=True, hide_index=True)
        options = [r["worker_id"] for r in workers if r["active"]]
        if options:
            target = st.selectbox("Deactivate worker", options)
            if st.button("Deactivate selected worker", key="deactivate_worker"):
                db.deactivate_worker(target)
                st.success("Worker deactivated.")
                st.rerun()
    else:
        st.info("No workers created yet.")


def admin_app():
    page = admin_sidebar()
    admin_header()
    if page == "Dashboard":
        dashboard_view()
    elif page == "Live workers":
        live_workers_view()
    elif page == "Reports":
        reports_view()
    elif page == "Workers":
        workers_view()


if st.session_state.role == "worker":
    worker_app()
elif st.session_state.role == "admin":
    admin_app()
else:
    login_page()