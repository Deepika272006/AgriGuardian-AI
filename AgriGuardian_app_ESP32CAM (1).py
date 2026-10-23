import json
import os
from pathlib import Path

import httpx
import streamlit as st
from google import genai
from google.genai import types

DEFAULT_TOKEN_FILE = Path.home() / "agriguardian-mcp" / ".mcp_token"
DEFAULT_MCP_URL = "https://fantasy-chaffing-postage.ngrok-free.dev/mcp"
GEMINI_MODEL = "gemini-flash-latest"

st.set_page_config(page_title="AgriGuardian AI", page_icon="🌱", layout="wide")
import hashlib
import html
import urllib.parse
from datetime import datetime, timedelta, timezone

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    /* AG_CSS_V3: reference design (hickory + emerald), version-tolerant selectors */
    :root {
      --hickory:#3b2a23; --hickory-dark:#211611; --hickory-soft:#6a4b3d;
      --emerald:#087a59; --emerald-dark:#04563f; --emerald-bright:#12a874;
      --mint:#4bd29f; --cream:#f3efe5; --paper:#faf8f2; --sage:#e4efe8;
      --line:#ddd7ca; --ink:#241914; --ink-soft:#5f574d;
      --warn:#b7791f; --warn-bg:#fdf3dc; --danger:#a63d33; --danger-bg:#fbe9e6;
    }
    html { scroll-behavior:smooth; }
    .stApp { background:radial-gradient(circle at 8% 8%,rgba(18,168,116,.22),transparent 26%),radial-gradient(circle at 94% 90%,rgba(255,255,255,.07),transparent 26%),#3b2a23 !important; color:var(--ink); }
    [data-testid="stHeader"] { background:rgba(33,22,17,.9) !important; }
    [data-testid="stHeader"] * { color:#f7f2e9 !important; }
    [data-testid="stBottom"], [data-testid="stBottom"] > div { background:transparent !important; }

    /* Main cream panel (works on old and new Streamlit DOMs) */
    .stMain .block-container, [data-testid="stMainBlockContainer"], .main .block-container {
      max-width:1180px !important; width:100% !important; margin:4.5rem auto 2rem !important;
      padding:1rem clamp(1rem,4vw,3rem) 3rem !important; background:var(--cream) !important;
      border:1px solid rgba(255,255,255,.14); border-radius:34px; box-shadow:0 40px 90px rgba(10,5,2,.45);
    }
    [data-testid="stMainBlockContainer"] :is(h1,h2,h3,h4) { color:var(--hickory-dark) !important; letter-spacing:-.035em; }
    [data-testid="stMainBlockContainer"] [data-testid="stMarkdownContainer"] :is(p,li) { color:var(--ink); }
    [data-testid="stMainBlockContainer"] [data-testid="stCaptionContainer"] { color:var(--ink-soft) !important; }
    [data-testid="stMainBlockContainer"] label p { color:var(--ink) !important; font-weight:600; }

    /* Sidebar: dark, readable, never clipped */
    [data-testid="stSidebar"] { background:#211611 !important; border-right:1px solid rgba(255,255,255,.1); overflow-x:hidden; }
    [data-testid="stSidebar"] * { color:#f7f2e9 !important; }
    [data-testid="stSidebarContent"], [data-testid="stSidebarUserContent"] { overflow-x:hidden !important; }
    [data-testid="stSidebar"] [data-testid="stCode"], [data-testid="stSidebar"] [data-testid="stCode"] pre, [data-testid="stSidebar"] [data-testid="stCode"] code { background:#33251e !important; }
    [data-testid="stSidebar"] [data-testid="stCode"] { border:1px solid #5a463a; border-radius:12px; }
    [data-testid="stSidebar"] pre, [data-testid="stSidebar"] code { white-space:pre-wrap !important; word-break:break-all !important; overflow-wrap:anywhere !important; }
    [data-testid="stSidebar"] [data-testid="stAlert"], [data-testid="stSidebar"] [data-testid="stAlertContainer"], [data-testid="stSidebar"] [data-baseweb="notification"] { background:#2b3243 !important; border:1px solid rgba(255,255,255,.18) !important; border-radius:14px !important; }
    [data-testid="stSidebar"] .stButton button, [data-testid="stSidebar"] [data-testid="stButton"] button { background:#087a59 !important; border:1px solid #65d6a7 !important; border-radius:999px !important; font-weight:700 !important; }
    [data-testid="stSidebar"] .stButton button:hover, [data-testid="stSidebar"] [data-testid="stButton"] button:hover { background:#04563f !important; border-color:#ffffff !important; }

    /* Buttons in the main panel */
    .stMain .stButton button, [data-testid="stMainBlockContainer"] .stButton button { border-radius:999px !important; font-weight:700 !important; background:var(--sage) !important; color:var(--emerald-dark) !important; border:1px solid #bcd3c5 !important; }
    .stMain .stButton button *, [data-testid="stMainBlockContainer"] .stButton button * { color:inherit !important; }
    .stMain .stButton button[kind="primary"], .stMain .stButton button[data-testid="stBaseButton-primary"] { background:var(--emerald) !important; color:#ffffff !important; border:0 !important; box-shadow:0 10px 20px rgba(8,122,89,.22); }
    .stMain .stButton button:hover { filter:brightness(.96); }
    [data-testid^="stBaseLinkButton"] { border-radius:999px !important; font-weight:700 !important; background:var(--sage) !important; color:var(--emerald-dark) !important; border:1px solid #bcd3c5 !important; }
    [data-testid^="stBaseLinkButton"] * { color:var(--emerald-dark) !important; }

    /* Tabs become the pill navigation from the reference */
    [role="tablist"], [data-baseweb="tab-list"] { display:flex !important; justify-content:center; align-items:center; gap:4px; background:var(--hickory-dark) !important; padding:5px !important; border-radius:999px; width:fit-content; max-width:100%; margin:6px auto 26px !important; box-shadow:0 10px 26px rgba(33,22,17,.2); overflow-x:auto; }
    [role="tab"], [data-baseweb="tab"] { flex:0 0 auto; border-radius:999px !important; padding:9px clamp(10px,2vw,19px) !important; font-size:.82rem; font-weight:700 !important; border:0 !important; opacity:1 !important; }
    [role="tab"][aria-selected="false"], [data-baseweb="tab"][aria-selected="false"] { background:transparent !important; color:#f5efe6 !important; }
    [role="tab"][aria-selected="false"]:hover { background:rgba(255,255,255,.14) !important; }
    [role="tab"][aria-selected="true"], [data-baseweb="tab"][aria-selected="true"] { background:#ffffff !important; color:var(--hickory-dark) !important; box-shadow:0 4px 12px rgba(0,0,0,.14); }
    [role="tab"] *, [data-baseweb="tab"] * { color:inherit !important; opacity:1 !important; font-weight:inherit !important; }
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display:none !important; }
    [role="tab"]:focus, [role="tab"]:focus-visible { outline:2px solid #f3c969 !important; outline-offset:2px; }

    /* Other widgets on cream */
    [data-testid="stExpander"] { background:#ffffff; border:1px solid var(--line) !important; border-radius:16px !important; }
    [data-testid="stFileUploaderDropzone"] { background:var(--paper) !important; border:1.5px dashed var(--line) !important; border-radius:16px !important; }
    [data-testid="stSelectbox"] [data-baseweb="select"] > div { border-radius:14px !important; background:#ffffff !important; }

    /* ---------- Brand bar, hero, showcase ---------- */
    .ag-nav { display:flex; align-items:center; justify-content:space-between; gap:14px; min-height:64px; }
    .ag-brand { display:flex; align-items:center; gap:10px; font-weight:800; letter-spacing:-.03em; font-size:1.08rem; color:var(--hickory-dark); }
    .ag-mark { width:36px; height:36px; border-radius:50%; display:grid; place-items:center; font-size:17px; color:#fff; background:linear-gradient(135deg,var(--emerald-dark),var(--emerald-bright)); box-shadow:0 8px 20px rgba(8,122,89,.28); }
    .ag-conn { display:inline-flex; align-items:center; gap:8px; padding:10px 16px; border-radius:999px; color:#fff; font-size:.76rem; font-weight:700; background:linear-gradient(135deg,var(--emerald-dark),var(--emerald)); box-shadow:0 8px 18px rgba(8,122,89,.25); }
    .ag-conn i { width:8px; height:8px; border-radius:50%; background:#7dffc6; box-shadow:0 0 0 4px rgba(125,255,198,.25); }
    .ag-conn.off { background:linear-gradient(135deg,#7d2e26,var(--danger)); }
    .ag-conn.off i { background:#ffb4ab; box-shadow:none; }
    .ag-hero2 { position:relative; text-align:center; padding:30px 0 30px; overflow:hidden; }
    .ag-water { position:absolute; left:50%; top:46px; transform:translateX(-50%); font-size:clamp(70px,16vw,210px); font-weight:900; letter-spacing:-.07em; color:rgba(59,42,35,.07); white-space:nowrap; pointer-events:none; user-select:none; }
    .ag-eye { display:inline-flex; align-items:center; gap:9px; padding:6px 14px 6px 8px; background:rgba(255,255,255,.7); border:1px solid var(--line); border-radius:999px; font-size:.72rem; color:var(--ink-soft); position:relative; }
    .ag-eye b { background:var(--emerald); color:#fff; border-radius:999px; padding:3px 9px; font-size:.62rem; letter-spacing:.05em; }
    .ag-h1 { position:relative; margin:18px auto 0; max-width:860px; font-size:clamp(2.3rem,6.4vw,4.6rem); line-height:.97; letter-spacing:-.065em; font-weight:800; color:var(--hickory-dark); }
    .ag-h1 span { display:block; color:var(--emerald-dark); }
    .ag-lead { position:relative; max-width:560px; margin:18px auto 0; color:var(--ink-soft); font-size:.95rem; line-height:1.7; }
    .ag-showcase { border-radius:30px; overflow:hidden; background:var(--hickory-dark); box-shadow:0 32px 60px rgba(33,22,17,.32); margin:6px 0 8px; }
    .ag-visual { position:relative; min-height:400px; overflow:hidden; display:grid; place-items:center; padding:28px; }
    .ag-scene { position:absolute; inset:0; width:100%; height:100%; }
    .ag-glass { position:relative; width:min(600px,100%); border-radius:26px; padding:22px 24px 24px; color:#fff; background:rgba(33,22,17,.62); border:1px solid rgba(255,255,255,.22); backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px); box-shadow:0 24px 50px rgba(10,5,2,.4); }
    .ag-glass-top { display:flex; justify-content:space-between; align-items:center; font-size:.66rem; letter-spacing:.12em; color:#d8e8df; font-weight:700; }
    .ag-live { display:inline-flex; align-items:center; gap:6px; padding:6px 11px; border-radius:999px; background:rgba(255,255,255,.1); border:1px solid rgba(255,255,255,.18); letter-spacing:.06em; }
    .ag-live i { width:7px; height:7px; border-radius:50%; background:#7dffc6; }
    .ag-glass-title { margin:24px 0 0; font-size:clamp(1.35rem,3.2vw,1.9rem); line-height:1.1; letter-spacing:-.045em; font-weight:800; max-width:440px; color:#fff; }
    .ag-flow { margin-top:9px; font-size:.76rem; color:#cfe0d7; }
    .ag-readings { display:grid; grid-template-columns:repeat(4,1fr); gap:9px; margin-top:20px; }
    .ag-reading { background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.1); border-radius:14px; padding:11px 12px; }
    .ag-reading b { display:block; font-size:1.2rem; letter-spacing:-.03em; color:#fff; }
    .ag-reading span { font-size:.6rem; color:#c3d6cb; letter-spacing:.06em; }
    .ag-badge { position:absolute; left:30px; top:24px; width:100px; height:100px; border-radius:50%; background:rgba(33,22,17,.8); border:1px solid rgba(255,255,255,.25); display:grid; place-items:center; }
    .ag-badge svg { position:absolute; inset:0; animation:ag-spin 22s linear infinite; }
    .ag-badge .core { width:42px; height:42px; border-radius:50%; background:#fff; color:var(--emerald-dark); display:grid; place-items:center; font-size:19px; }
    .ag-services { padding:6px 30px 26px; background:linear-gradient(180deg,#2c1f19,#1c130f); }
    .ag-svc { display:flex; align-items:center; justify-content:space-between; gap:14px; padding:18px 6px; border-bottom:1px solid rgba(255,255,255,.08); color:#f5f1ea; }
    .ag-svc { cursor:pointer; transition:background .2s ease; border-radius:12px; }
    .ag-svc:hover { background:rgba(255,255,255,.06); }
    .ag-svc:hover .arrow { background:#ffffff; color:#211611; border-color:#ffffff; transform:translateX(3px); }
    .ag-svc .arrow { transition:all .2s ease; }
    .ag-svc:last-child { border-bottom:0; }
    .ag-svc .t { font-size:clamp(1.05rem,2.2vw,1.45rem); font-weight:600; letter-spacing:-.03em; color:#f5f1ea; }
    .ag-svc small { display:block; font-size:.62rem; letter-spacing:.1em; color:#a89d90; margin-top:4px; font-weight:600; }
    .ag-svc .arrow { width:36px; height:36px; border-radius:50%; display:grid; place-items:center; border:1px solid rgba(255,255,255,.18); color:#f5f1ea; flex:0 0 auto; }

    /* ---------- Sections and cards ---------- */
    .ag-intro { display:grid; grid-template-columns:.7fr 1.3fr; gap:40px; padding:34px 6px 12px; }
    .ag-kicker { display:inline-flex; align-items:center; gap:8px; font-size:.72rem; font-weight:700; color:var(--ink-soft); }
    .ag-kicker:before { content:""; width:7px; height:7px; border-radius:50%; background:var(--emerald); }
    .ag-intro-text { font-size:clamp(1.05rem,2vw,1.3rem); line-height:1.55; letter-spacing:-.02em; color:#463a33; }
    .ag-stats { display:grid; grid-template-columns:repeat(4,1fr); gap:18px; padding:20px 6px 34px; border-bottom:1px solid var(--line); margin-bottom:6px; }
    .ag-stat b { display:block; font-size:clamp(1.5rem,3.2vw,2.1rem); font-weight:800; letter-spacing:-.05em; color:var(--hickory-dark); }
    .ag-stat span { display:block; font-size:.72rem; color:var(--ink-soft); margin-top:2px; }
    .ag-st { display:flex; justify-content:space-between; align-items:flex-end; gap:16px; margin:26px 0 16px; }
    .ag-h2 { font-size:clamp(1.55rem,3vw,2.1rem); letter-spacing:-.045em; font-weight:800; color:var(--hickory-dark); line-height:1.1; }
    .ag-sub { margin-top:5px; font-size:.84rem; color:var(--ink-soft); }
    .ag-tag { font-size:.66rem; font-weight:700; color:var(--emerald-dark); background:var(--sage); border-radius:999px; padding:7px 12px; white-space:nowrap; }
    .ag-metrics { display:grid; grid-template-columns:repeat(auto-fit,minmax(176px,1fr)); gap:14px; }
    .ag-metric { background:#fff; border:1px solid var(--line); border-radius:20px; padding:20px; box-shadow:0 10px 26px rgba(58,42,31,.05); }
    .ag-metric .icon { width:42px; height:42px; border-radius:13px; display:grid; place-items:center; font-size:21px; background:var(--sage); }
    .ag-metric .label { font-size:.78rem; color:var(--ink-soft); margin-top:14px; }
    .ag-metric .value { font-size:2rem; font-weight:800; letter-spacing:-.045em; color:var(--hickory-dark); line-height:1.15; }
    .ag-metric .value.sm { font-size:1.3rem; line-height:1.75; }
    .ag-metric .note { font-size:.74rem; color:var(--ink-soft); min-height:18px; }
    .ag-meter { height:6px; border-radius:99px; background:#ece8dc; margin-top:12px; overflow:hidden; }
    .ag-meter i { display:block; height:100%; border-radius:99px; background:linear-gradient(90deg,var(--emerald),var(--emerald-bright)); }
    .ag-metric.low .ag-meter i { background:#d9822b; }
    .ag-metric.low .note { color:var(--warn); font-weight:700; }
    .ag-card2 { background:rgba(255,255,255,.88); border:1px solid var(--line); border-radius:24px; padding:24px; box-shadow:0 14px 36px rgba(58,42,31,.07); margin:6px 0 18px; }
    .ag-card2-title { font-size:1.15rem; font-weight:800; letter-spacing:-.03em; color:var(--hickory-dark); }
    .ag-steps { display:flex; gap:6px; margin:16px 0 18px; }
    .ag-step { flex:1; text-align:center; font-size:.62rem; font-weight:800; letter-spacing:.05em; text-transform:uppercase; color:#8f867a; }
    .ag-step i { display:block; height:5px; border-radius:99px; background:#e8e2d5; margin-bottom:7px; }
    .ag-step.done, .ag-step.now { color:var(--emerald-dark); }
    .ag-step.done i { background:var(--emerald-bright); }
    .ag-step.now i { background:var(--emerald); box-shadow:0 0 0 3px rgba(8,122,89,.16); }
    .ag-verdict { display:flex; gap:14px; padding:17px; border-radius:16px; align-items:flex-start; }
    .ag-verdict.yes { background:var(--sage); }
    .ag-verdict.no { background:#f1ece0; }
    .ag-verdict .vi { font-size:28px; line-height:1; }
    .ag-verdict b { display:block; font-size:1.05rem; letter-spacing:-.025em; color:var(--hickory-dark); }
    .ag-verdict span { font-size:.84rem; color:#4a4137; }
    .ag-note { margin-top:14px; font-size:.78rem; color:var(--ink-soft); background:var(--warn-bg); border-radius:14px; padding:10px 13px; }
    .ag-crop-side { background:linear-gradient(145deg,var(--hickory-dark),var(--emerald-dark)); color:#fff; border-radius:22px; padding:24px; position:relative; overflow:hidden; }
    .ag-crop-side:after { content:"🍃"; position:absolute; right:-8px; bottom:-26px; font-size:110px; opacity:.14; }
    .ag-crop-side .ag-card2-title { color:#fff; }
    .ag-crop-side div.s { color:#d3e5da; font-size:.86rem; margin-top:6px; line-height:1.55; }
    .ag-cinfo { background:#fff; border:1px solid var(--line); border-radius:22px; padding:20px; margin-top:14px; }
    .ag-cinfo-h { font-size:1.25rem; font-weight:800; letter-spacing:-.03em; color:var(--hickory-dark); display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
    .ag-cinfo-h small { font-size:.82rem; color:var(--ink-soft); font-weight:600; }
    .ag-cfacts { display:grid; grid-template-columns:repeat(2,1fr); gap:12px; margin-top:14px; }
    .ag-cfact { background:var(--paper); border:1px solid var(--line); border-radius:16px; padding:12px 14px; }
    .ag-cfact span { display:block; font-size:.64rem; font-weight:800; letter-spacing:.06em; color:var(--ink-soft); }
    .ag-cfact b { display:block; font-size:.86rem; margin-top:3px; line-height:1.35; color:var(--ink); }
    .ag-wbar { display:flex; gap:4px; margin-top:7px; }
    .ag-wbar i { flex:1; height:7px; border-radius:99px; background:#e1dccf; }
    .ag-wbar i.on { background:var(--emerald-bright); }
    .ag-mstrip { display:grid; grid-template-columns:repeat(12,1fr); gap:4px; margin-top:8px; }
    .ag-mstrip i { font-style:normal; text-align:center; font-size:.66rem; font-weight:700; padding:5px 0; border-radius:8px; background:#ebe6d9; color:var(--ink-soft); }
    .ag-mstrip i.sow { background:var(--emerald); color:#fff; }
    .ag-mstrip i.cur { outline:2px solid var(--hickory-dark); outline-offset:1px; }
    .ag-ctip { margin-top:12px; font-size:.8rem; color:#5c4a1c; background:var(--warn-bg); border-radius:14px; padding:10px 13px; }
    .ag-sowbadge { display:inline-block; font-size:.62rem; font-weight:800; letter-spacing:.05em; color:#fff; background:var(--emerald); border-radius:999px; padding:3px 9px; }
    .ag-panel { background:var(--paper); border:1px solid var(--line); border-radius:22px; padding:22px 24px; margin:12px 0 20px; box-shadow:0 10px 28px rgba(58,42,31,.05); color:var(--ink); }
    .ag-footer { color:#6f675d; font-size:.78rem; text-align:center; margin-top:34px; padding-top:18px; border-top:1px solid var(--line); }
    @keyframes ag-spin { to { transform:rotate(360deg); } }
    @media(max-width:900px){ .ag-intro{grid-template-columns:1fr;gap:14px;padding-top:24px} .ag-stats{grid-template-columns:repeat(2,1fr)} }
    @media(max-width:760px){ .stMain .block-container,[data-testid="stMainBlockContainer"]{margin:3.8rem auto .6rem !important;border-radius:22px} .ag-readings{grid-template-columns:repeat(2,1fr)} .ag-badge{display:none} .ag-cfacts{grid-template-columns:1fr} [role="tablist"]{width:100%;justify-content:flex-start;border-radius:18px} .ag-services{padding:4px 16px 20px} }
    @media(prefers-reduced-motion:reduce){ *,*:before,*:after{ animation:none !important; transition:none !important; scroll-behavior:auto !important; } }

    /* AG_CSS_V4: motion, depth, learning hub, video cards */
    .stApp :is(p,li,h1,h2,h3,h4,label,button,input,textarea,a,summary,.ag-h1,.ag-h2,.ag-brand) { font-family:'Plus Jakarta Sans','Segoe UI',system-ui,sans-serif; }
    ::selection { background:#12a874; color:#fff; }
    ::-webkit-scrollbar { width:10px; height:10px; }
    ::-webkit-scrollbar-thumb { background:#b9b09f; border-radius:99px; border:2px solid var(--cream); }
    @keyframes ag-rise { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:none; } }
    @keyframes ag-float { 0%,100% { transform:translateY(0); } 50% { transform:translateY(-8px); } }
    @keyframes ag-shine { to { background-position:200% center; } }
    @keyframes ag-pulse { 0% { box-shadow:0 0 0 0 rgba(125,255,198,.55); } 100% { box-shadow:0 0 0 10px rgba(125,255,198,0); } }
    .ag-h1 span { background:linear-gradient(90deg,#04563f,#12a874,#04563f); background-size:200% auto; -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; color:transparent; animation:ag-shine 7s linear infinite; }
    .ag-hero2 .ag-eye, .ag-hero2 .ag-h1, .ag-hero2 .ag-lead { animation:ag-rise .8s both; }
    .ag-hero2 .ag-h1 { animation-delay:.1s; } .ag-hero2 .ag-lead { animation-delay:.2s; }
    .ag-badge { animation:ag-float 6s ease-in-out infinite; }
    .ag-conn i, .ag-live i { animation:ag-pulse 1.8s ease-out infinite; }
    .ag-showcase { transition:transform .4s ease, box-shadow .4s ease; }
    .ag-showcase:hover { transform:translateY(-4px); box-shadow:0 40px 70px rgba(33,22,17,.4); }
    .ag-metric, .ag-card2, .ag-cinfo, .ag-panel, .ag-season, .ag-learn { animation:ag-rise .6s both; }
    .ag-metric { transition:transform .25s ease, box-shadow .25s ease, border-color .25s ease; }
    .ag-metric:hover { transform:translateY(-5px); box-shadow:0 18px 36px rgba(58,42,31,.13); border-color:#bcd3c5; }
    .ag-metric:nth-child(2) { animation-delay:.06s; } .ag-metric:nth-child(3) { animation-delay:.12s; } .ag-metric:nth-child(4) { animation-delay:.18s; } .ag-metric:nth-child(5) { animation-delay:.24s; }
    .ag-stat { transition:transform .25s ease; } .ag-stat:hover { transform:translateY(-3px); }
    .ag-cfact { transition:border-color .2s ease, transform .2s ease; } .ag-cfact:hover { border-color:var(--emerald); transform:translateY(-2px); }
    [role="tab"] { transition:background .2s ease, transform .2s ease; } [role="tab"]:hover { transform:translateY(-1px); }
    .stMain .stButton button, [data-testid^="stBaseLinkButton"] { transition:transform .2s ease, box-shadow .2s ease, background .2s ease; }
    .stMain .stButton button:hover, [data-testid^="stBaseLinkButton"]:hover { transform:translateY(-2px); box-shadow:0 10px 20px rgba(8,122,89,.18); }
    [data-testid="stVideo"], [data-testid="stVideo"] iframe, [data-testid="stVideo"] video { border-radius:22px !important; box-shadow:0 18px 40px rgba(33,22,17,.22); }
    [data-testid="stTextInput"] input { border-radius:14px !important; background:#fff !important; border:1px solid var(--line) !important; padding:.65rem .9rem !important; }
    [data-testid="stTextInput"] input:focus { border-color:var(--emerald) !important; box-shadow:0 0 0 3px rgba(8,122,89,.18) !important; }
    [data-testid="stRadio"] [role="radiogroup"] { gap:8px; }
    [data-testid="stRadio"] [role="radiogroup"] > label { background:#fff; border:1px solid var(--line); border-radius:999px; padding:6px 15px; margin:0; transition:all .2s ease; }
    [data-testid="stRadio"] [role="radiogroup"] > label:hover { border-color:var(--emerald); background:var(--sage); transform:translateY(-1px); }
    [data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) { background:var(--emerald); border-color:var(--emerald); }
    [data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) * { color:#fff !important; }
    .ag-season { display:flex; align-items:center; justify-content:space-between; gap:14px; flex-wrap:wrap; background:linear-gradient(120deg,#fff,var(--sage)); border:1px solid #bcd3c5; border-radius:20px; padding:14px 18px; margin:4px 0 14px; }
    .ag-season-t { font-size:.86rem; color:var(--ink); }
    .ag-chips { display:flex; flex-wrap:wrap; gap:8px; }
    .ag-chip { display:inline-block; font-size:.74rem; font-weight:700; color:var(--emerald-dark); background:#fff; border:1px solid #bcd3c5; border-radius:999px; padding:6px 12px; }
    .ag-chip.lt { background:rgba(255,255,255,.14); color:#fff; border-color:rgba(255,255,255,.28); }
    .ag-learn { position:relative; overflow:hidden; border-radius:28px; padding:30px 30px 26px; margin:34px 0 16px; color:#fff; background:linear-gradient(135deg,#211611 0%,#04563f 62%,#12a874 100%); box-shadow:0 26px 52px rgba(8,60,44,.3); }
    .ag-learn:after { content:"🌾"; position:absolute; right:18px; bottom:-30px; font-size:150px; opacity:.16; transform:rotate(-12deg); }
    .ag-learn-k { font-size:.66rem; font-weight:800; letter-spacing:.14em; color:#a7f0cf; }
    .ag-learn-t { font-size:clamp(1.5rem,3.6vw,2.3rem); font-weight:800; letter-spacing:-.045em; line-height:1.08; margin-top:8px; color:#fff; }
    .ag-learn-s { max-width:560px; margin:10px 0 16px; font-size:.9rem; line-height:1.6; color:#d3e8dc; }
    .ag-vnow { margin:12px 2px 10px; font-size:.9rem; font-weight:800; letter-spacing:-.02em; color:var(--hickory-dark); }
    .ag-vnow span { font-weight:600; color:var(--ink-soft); }
    .ag-vcard { background:#fff; border:1px solid var(--line); border-radius:16px; overflow:hidden; transition:transform .25s ease, box-shadow .25s ease, border-color .25s ease; margin-bottom:6px; animation:ag-rise .5s both; }
    .ag-vcard:hover { transform:translateY(-4px); box-shadow:0 14px 28px rgba(58,42,31,.16); }
    .ag-vcard.on { border-color:var(--emerald); box-shadow:0 0 0 2px var(--emerald); }
    .ag-vcard img { width:100%; aspect-ratio:16/9; object-fit:cover; display:block; background:#e4efe8; }
    .ag-vcard .vt { font-size:.72rem; font-weight:700; line-height:1.35; padding:8px 10px 2px; color:var(--ink); display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; min-height:2.9em; }
    .ag-vcard .vb { font-size:.64rem; color:var(--ink-soft); padding:0 10px 9px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .ag-footer { background:linear-gradient(135deg,#211611,#3b2a23); color:#d9d0c3 !important; border:0; border-radius:20px; padding:18px 20px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def secret(name, default=""):
    try:
        value = st.secrets.get(name, default)
        if value:
            return str(value)
    except Exception:
        pass
    return os.environ.get(name, default)


def get_token():
    value = secret("MCP_TOKEN")
    if value:
        return value.strip()
    token_file = Path(secret("MCP_TOKEN_FILE", str(DEFAULT_TOKEN_FILE)))
    try:
        return token_file.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def mcp_request(method, params=None, request_id=1):
    url = secret("MCP_URL", DEFAULT_MCP_URL).strip()
    token = get_token()
    if not token:
        raise RuntimeError(
            "MCP token not found. Configure MCP_TOKEN_FILE or MCP_TOKEN in Streamlit secrets."
        )
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        init = client.post(
            url,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "AgriGuardian-Dashboard", "version": "1.0.0"},
                },
            },
        )
        if init.status_code >= 400:
            raise RuntimeError(
                f"MCP initialization failed (HTTP {init.status_code}). Check token, endpoint, and tunnel."
            )
        session_id = init.headers.get("mcp-session-id")
        if not session_id:
            raise RuntimeError("MCP initialize response did not include a session ID.")
        headers["MCP-Session-Id"] = session_id
        headers["MCP-Protocol-Version"] = "2025-11-25"
        response = client.post(
            url,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": request_id + 1,
                "method": method,
                "params": params or {},
            },
        )
        if response.status_code >= 400:
            raise RuntimeError(f"MCP request failed (HTTP {response.status_code}).")
        payload = None
        for line in response.text.splitlines():
            if line.startswith("data:"):
                try:
                    payload = json.loads(line[5:].strip())
                    break
                except json.JSONDecodeError:
                    continue
        if payload is None:
            try:
                payload = response.json()
            except ValueError:
                raise RuntimeError("MCP returned an unrecognized response.")
        if "error" in payload:
            raise RuntimeError(str(payload["error"]))
        return payload.get("result", payload)


def call_tool(name):
    result = mcp_request("tools/call", {"name": name, "arguments": {}}, 10)
    text_parts = [
        x.get("text", "")
        for x in result.get("content", [])
        if x.get("type") == "text"
    ]
    if result.get("isError"):
        raise RuntimeError("\n".join(text_parts) or "MCP tool reported an error.")
    text = "\n".join(text_parts)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"result": text}


def farm_context():
    return {
        "sensor_readings": call_tool("get_sensor_readings"),
        "irrigation_advice": call_tool("get_irrigation_recommendation"),
    }


def gemini_client():
    key = secret("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Gemini API key missing. Add GEMINI_API_KEY to .streamlit/secrets.toml.")
    return genai.Client(api_key=key)


def answer_question(question, context):
    prompt = f"""You are AgriGuardian, an agricultural support assistant.
Answer the user's question using the farm data below.
Important: the values are SIMULATED, not live hardware readings. Do not claim a pump or device was operated. Do not invent measurements or weather forecasts. Give cautious practical advice and state when data is insufficient.

Farm data:
{json.dumps(context, indent=2)}

User question: {question}
"""
    response = gemini_client().models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.3),
    )
    return response.text or "Gemini did not return text."


def analyze_leaf(upload):
    prompt = """Analyze this plant/crop leaf image for preliminary agricultural assistance.
Provide: (1) likely plant/crop or uncertainty, (2) visible symptoms, (3) possible disease/pest/nutrient/environmental issue, (4) confidence and reasons, (5) practical next steps, (6) what further evidence would help.
Do not claim a definitive diagnosis from one image. Do not prescribe pesticide dosage. Recommend local agricultural expert confirmation for consequential treatment decisions. If blurry or too close, say so."""
    response = gemini_client().models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            prompt,
            types.Part.from_bytes(data=upload.getvalue(), mime_type=upload.type or "image/jpeg"),
        ],
        config=types.GenerateContentConfig(temperature=0.2),
    )
    return response.text or "Gemini did not return text."



def esc(value):
    return html.escape(str(value), quote=True)


def md(markup):
    """Render HTML without newlines so Markdown never turns indentation into code blocks."""
    st.markdown("".join(line.strip() for line in markup.strip().splitlines()), unsafe_allow_html=True)


def to_num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def pct(value):
    return "--" if value in (None, "", "\u2014") else f"{esc(value)}%"


def as_dict(value):
    return value if isinstance(value, dict) else {}


def metric(icon, label, value, note="", meter=None, low=False, small=False):
    bar = ""
    n = to_num(meter)
    if n is not None:
        bar = f'<div class="ag-meter"><i style="width:{max(0, min(100, n)):.0f}%"></i></div>'
    return (
        f'<div class="ag-metric{" low" if low else ""}"><div class="icon">{icon}</div>'
        f'<div class="label">{esc(label)}</div><div class="value{" sm" if small else ""}">{value}</div>'
        f'<div class="note">{esc(note)}</div>{bar}</div>'
    )


def section_head(title, subtitle, tag=""):
    tag_html = f'<span class="ag-tag">{esc(tag)}</span>' if tag else ""
    md(f'<div class="ag-st"><div><div class="ag-h2">{esc(title)}</div><div class="ag-sub">{esc(subtitle)}</div></div>{tag_html}</div>')


def is_recommended(text):
    t = str(text or "").lower()
    negative = ("not recommended", "not required", "not needed", "no irrigation", "skip", "do not")
    if any(n in t for n in negative):
        return False
    return any(k in t for k in ("recommend", "start", "irrigat", "water"))


IST_NOW = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
NOW_M = IST_NOW.month
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def season_of(m):
    if 6 <= m <= 9:
        return "Kharif"
    if m in (10, 11, 12, 1, 2):
        return "Rabi"
    return "Zaid"


# Crop guide data (general guidance for Tamil Nadu / India; confirm with a local agriculture office).
CROPS = [{'id': 'rice',
  'e': '🌾',
  'name': 'Rice (Paddy)',
  'ta': 'நெல்',
  'seasons': ['Kharif', 'Rabi'],
  'sow': [6, 8, 12, 1],
  'sowText': 'Kuruvai Jun · Samba Aug · Navarai Dec–Jan',
  'days': '110–150 days',
  'water': 5,
  'waterText': 'Very high · keep 2–5 cm standing water',
  'soil': 'Clay / clay loam, pH 5.5–7',
  'temp': '20–35 °C',
  'tip': 'Drain the field 1–2 weeks before harvest. Alternate wetting and drying can save a lot of water.',
  'q': 'paddy rice cultivation complete guide Tamil Nadu'},
 {'id': 'maize',
  'e': '🌽',
  'name': 'Maize',
  'ta': 'மக்காச்சோளம்',
  'seasons': ['Kharif', 'Rabi'],
  'sow': [6, 7, 10, 11],
  'sowText': 'Jun–Jul (Kharif) · Oct–Nov (Rabi)',
  'days': '90–120 days',
  'water': 3,
  'waterText': 'Medium · critical at tasselling and silking',
  'soil': 'Well-drained loam, pH 5.8–7',
  'temp': '21–30 °C',
  'tip': 'Never let it dry out at flowering — that is when yield is decided. Waterlogging kills seedlings.',
  'q': 'maize corn cultivation guide India farmers'},
 {'id': 'cotton',
  'e': '☁️',
  'name': 'Cotton',
  'ta': 'பருத்தி',
  'seasons': ['Kharif'],
  'sow': [6, 7, 8],
  'sowText': 'Jun–Aug (rainfed) · irrigated crop can start earlier',
  'days': '150–180 days',
  'water': 3,
  'waterText': 'Medium · most needed at flowering and boll formation',
  'soil': 'Deep black or red loam, pH 6–8',
  'temp': '21–35 °C',
  'tip': 'Stop irrigating as bolls open. Scout for bollworm and whitefly every week.',
  'q': 'cotton cultivation guide India'},
 {'id': 'groundnut',
  'e': '🥜',
  'name': 'Groundnut',
  'ta': 'நிலக்கடலை',
  'seasons': ['Kharif', 'Rabi'],
  'sow': [6, 7, 12, 1],
  'sowText': 'Jun–Jul (Kharif) · Dec–Jan (Rabi/summer)',
  'days': '100–130 days',
  'water': 2,
  'waterText': 'Low–medium · avoid waterlogging',
  'soil': 'Sandy loam, loose and well drained, pH 6–7',
  'temp': '25–30 °C',
  'tip': 'Loose soil lets pegs enter the ground. Water at pegging and pod filling, and keep drainage open.',
  'q': 'groundnut peanut cultivation guide India'},
 {'id': 'ragi',
  'e': '🌿',
  'name': 'Ragi (Finger millet)',
  'ta': 'கேழ்வரகு',
  'seasons': ['Kharif', 'Rabi'],
  'sow': [7, 8, 12, 1],
  'sowText': 'Jul–Aug (Kharif) · Dec–Jan (irrigated)',
  'days': '90–120 days',
  'water': 1,
  'waterText': 'Low · drought tolerant',
  'soil': 'Red loam / light soils, pH 5–8',
  'temp': '20–30 °C',
  'tip': 'A good choice for dry land. Transplanting 3–4 week old seedlings gives better yield than '
         'broadcasting.',
  'q': 'ragi finger millet cultivation guide'},
 {'id': 'wheat',
  'e': '🌾',
  'name': 'Wheat',
  'ta': 'கோதுமை',
  'seasons': ['Rabi'],
  'sow': [11, 12],
  'sowText': 'Nov–Dec',
  'days': '120–150 days',
  'water': 3,
  'waterText': 'Medium · 4–6 irrigations, first at ~21 days',
  'soil': 'Loam / clay loam, pH 6–7.5',
  'temp': '10–25 °C (cool season)',
  'tip': 'Needs a cool growing period. Late sowing after December cuts yield because of heat at grain '
         'filling.',
  'q': 'wheat cultivation guide India'},
 {'id': 'tomato',
  'e': '🍅',
  'name': 'Tomato',
  'ta': 'தக்காளி',
  'seasons': ['Kharif', 'Rabi'],
  'sow': [6, 7, 10, 11, 12, 1],
  'sowText': 'Jun–Jul · Oct–Jan (best winter crop)',
  'days': '100–140 days from sowing',
  'water': 3,
  'waterText': 'Medium · light, even moisture (drip is ideal)',
  'soil': 'Sandy loam, rich in organic matter, pH 6–7',
  'temp': '18–27 °C',
  'tip': 'Irregular watering causes fruit cracking and blossom-end rot. Stake plants and mulch the soil.',
  'q': 'tomato cultivation guide farmers India'},
 {'id': 'watermelon',
  'e': '🍉',
  'name': 'Watermelon',
  'ta': 'தர்பூசணி',
  'seasons': ['Zaid'],
  'sow': [1, 2, 3],
  'sowText': 'Jan–Mar (summer crop)',
  'days': '80–100 days',
  'water': 3,
  'waterText': 'Medium · regular, reduce near ripening for sweeter fruit',
  'soil': 'Sandy loam, pH 6–7',
  'temp': '24–35 °C (warm)',
  'tip': 'Keep leaves dry to limit disease and ease off watering as fruits ripen.',
  'q': 'watermelon cultivation guide India'}]


@st.cache_data(ttl=86400, show_spinner=False)
def youtube_videos(query, api_key, lang_code=""):
    """Embeddable how-to videos. The API key stays on the server and is never shown."""
    out = []
    for duration in ("medium", "any"):
        params = {"part": "snippet", "type": "video", "videoEmbeddable": "true",
                  "videoDuration": duration, "safeSearch": "strict",
                  "maxResults": 5, "q": query, "key": api_key}
        if lang_code:
            params["relevanceLanguage"] = lang_code
        r = httpx.get("https://www.googleapis.com/youtube/v3/search", params=params, timeout=15)
        if r.status_code != 200:
            raise RuntimeError(f"YouTube API error {r.status_code}")
        out = []
        for item in (r.json().get("items") or []):
            vid = (item.get("id") or {}).get("videoId")
            if vid:
                snip = item.get("snippet") or {}
                out.append({"id": vid, "title": html.unescape(snip.get("title", "Video")), "by": html.unescape(snip.get("channelTitle", ""))})
        if len(out) >= 3:
            break
    return out


VIDEO_LANGS = {"English": ("", "en"), "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd (Tamil)": (" Tamil", "ta"), "\u0939\u093f\u0928\u094d\u0926\u0940 (Hindi)": (" Hindi", "hi")}

TOPIC_GROUPS = [
    ("\U0001F33E Crops", [(f"{c['e']} {c['name']}", c["q"]) for c in CROPS]),
    ("\U0001F9F1 Land and soil", [
        ("Soil testing and health", "soil testing and soil health for farmers"),
        ("Land preparation", "land preparation and ploughing for farmers"),
        ("Mulching", "mulching in farming benefits and methods"),
        ("Vermicompost", "vermicompost making for farmers"),
        ("Green manure", "green manure crops for farmers")]),
    ("\U0001F4A7 Water", [
        ("Drip irrigation", "drip irrigation setup for farmers"),
        ("Sprinkler irrigation", "sprinkler irrigation setup for farmers"),
        ("Farm pond and rainwater", "farm pond and rainwater harvesting for farmers"),
        ("Solar water pump", "solar water pump for farmers"),
        ("When to irrigate", "when and how much to irrigate crops")]),
    ("\U0001F6E1\uFE0F Crop care", [
        ("Seed treatment and sowing", "seed treatment and sowing methods for farmers"),
        ("Fertilizer schedule", "fertilizer application schedule for crops farmers"),
        ("Organic pest control", "organic pest control for farmers"),
        ("Plant disease signs", "crop disease identification symptoms for farmers"),
        ("Weed management", "weed management in crops for farmers"),
        ("Harvest and storage", "post harvest handling and storage for farmers")]),
    ("\U0001F404 Livestock", [
        ("Dairy cow care", "dairy cow farming care for farmers"),
        ("Goat farming", "goat farming guide for beginners"),
        ("Poultry farming", "poultry farming guide for beginners India"),
        ("Fish farming", "fish farming pond guide India"),
        ("Fodder crops", "green fodder cultivation for farmers")]),
    ("\U0001F41D Allied farming", [
        ("Beekeeping", "beekeeping for beginners India"),
        ("Mushroom farming", "mushroom farming guide India"),
        ("Banana farming", "banana cultivation guide India"),
        ("Coconut farming", "coconut farming guide India"),
        ("Terrace garden", "terrace vegetable garden guide India"),
        ("Agroforestry", "agroforestry farming India")]),
    ("\U0001F4B0 Farm business", [
        ("Government schemes", "government schemes for farmers India explained"),
        ("PM-KISAN", "PM Kisan Samman Nidhi how to apply"),
        ("Crop insurance", "PMFBY crop insurance how to apply"),
        ("Selling produce", "how farmers sell produce eNAM mandi"),
        ("Farmer producer group", "farmer producer organisation FPO how to start")]),
    ("\U0001F69C Machines and tech", [
        ("Tractor and tools", "tractor and implements for small farmers"),
        ("Drone spraying", "agriculture drone spraying farmers India"),
        ("Farming apps", "best farming apps for Indian farmers"),
        ("Smart irrigation sensors", "soil moisture sensor smart irrigation for farmers")]),
]


def yt_search_url(query):
    return "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)


def render_videos(query, lang, key):
    """Show a player plus clickable thumbnails when a YouTube API key exists; always offer a YouTube search link."""
    suffix, code = VIDEO_LANGS[lang]
    full_q = query + suffix
    yt_key = secret("YOUTUBE_API_KEY").strip()
    if yt_key:
        vids = None
        try:
            vids = youtube_videos(full_q, yt_key, code)
        except RuntimeError as e:
            st.warning(str(e))
        except Exception:
            st.warning("Could not load videos right now. Try the YouTube search button below.")
        if vids:
            sel_key, sig_key = key + "_sel", key + "_sig"
            sig = hashlib.md5(full_q.encode("utf-8")).hexdigest()
            if st.session_state.get(sig_key) != sig:
                st.session_state[sig_key] = sig
                st.session_state[sel_key] = 0
            sel = min(int(st.session_state.get(sel_key, 0)), len(vids) - 1)
            st.video("https://www.youtube.com/watch?v=" + vids[sel]["id"])
            md(f'<div class="ag-vnow">\u25B6 {esc(vids[sel]["title"])} <span>\u00B7 {esc(vids[sel]["by"])}</span></div>')
            cols = st.columns(len(vids), gap="small")
            for i, (col, v) in enumerate(zip(cols, vids)):
                with col:
                    md(
                        f'<div class="ag-vcard{" on" if i == sel else ""}"><img src="https://i.ytimg.com/vi/{esc(v["id"])}/mqdefault.jpg" alt="" loading="lazy">'
                        f'<div class="vt">{esc(v["title"])}</div><div class="vb">{esc(v["by"])}</div></div>'
                    )
                    if st.button("Playing" if i == sel else "Play", key=f"{key}_b{i}", disabled=(i == sel), use_container_width=True):
                        st.session_state[sel_key] = i
                        st.rerun()
        elif vids is not None:
            st.info("No embeddable videos were found. Use the YouTube search button below.")
    else:
        st.info("Videos play here once a YouTube API key is added to the server (YOUTUBE_API_KEY in the Streamlit secrets). Until then, the YouTube button opens the best matching videos.")
    st.link_button("Open these videos on YouTube", yt_search_url(full_q))


def enable_service_links():
    """Make the five service rows switch to the matching tab (rows are in the same order as the tabs)."""
    try:
        import streamlit.components.v1 as components
        components.html(
            """<script>
            (function () {
              var win = window.parent, d;
              try { d = win.document; } catch (e) { return; }
              if (win.__agNav) { return; }
              win.__agNav = true;
              d.addEventListener("click", function (ev) {
                var row = ev.target && ev.target.closest ? ev.target.closest(".ag-svc") : null;
                if (!row) { return; }
                var rows = d.querySelectorAll(".ag-svc");
                var tabs = d.querySelectorAll('[role="tab"]');
                var idx = Array.prototype.indexOf.call(rows, row);
                if (idx >= 0 && tabs[idx]) {
                  tabs[idx].click();
                  tabs[idx].scrollIntoView({ behavior: "smooth", block: "center" });
                }
              });
            })();
            </script>""",
            height=0,
        )
    except Exception:
        pass


def crop_info_html(c):
    strip = "".join(
        f'<i class="{"sow" if i + 1 in c["sow"] else ""} {"cur" if i + 1 == NOW_M else ""}">{m[0]}</i>'
        for i, m in enumerate(MONTHS)
    )
    water = "".join(f'<i class="{"on" if n <= c["water"] else ""}"></i>' for n in range(1, 6))
    seasons = "".join(f'<span class="ag-tag">{esc(s)}</span>' for s in c["seasons"])
    sow_now = NOW_M in c["sow"]
    window = "This month is a good sowing window." if sow_now else "Not a main sowing month right now."
    return (
        f'<div class="ag-cinfo"><div class="ag-cinfo-h">{c["e"]} {esc(c["name"])} <small>{esc(c["ta"])}</small> {seasons}'
        f'{"<span class=ag-sowbadge>SOW NOW</span>" if sow_now else ""}</div>'
        f'<div class="ag-cfacts">'
        f'<div class="ag-cfact"><span>\U0001F4A7 WATER NEED</span><b>{esc(c["waterText"])}</b><div class="ag-wbar">{water}</div></div>'
        f'<div class="ag-cfact"><span>\U0001F9F1 SOIL</span><b>{esc(c["soil"])}</b></div>'
        f'<div class="ag-cfact"><span>\U0001F321\uFE0F TEMPERATURE</span><b>{esc(c["temp"])}</b></div>'
        f'<div class="ag-cfact"><span>\u23F1\uFE0F DURATION</span><b>{esc(c["days"])}</b></div></div>'
        f'<div class="ag-cfact" style="margin-top:12px"><span>\U0001F4C5 BEST TIME TO SOW \u00B7 {esc(c["sowText"])}</span>'
        f'<div class="ag-mstrip">{strip}</div>'
        f'<div style="font-size:.74rem;color:#5f574d;margin-top:7px">{window} Green = sowing months, outlined = this month.</div></div>'
        f'<div class="ag-ctip">\U0001F4A1 {esc(c["tip"])}</div></div>'
    )


with st.sidebar:
    st.markdown("## 🌿 Farm connections")
    st.caption("Private server-side authentication")
    st.write("**MCP endpoint**")
    st.code(secret("MCP_URL", DEFAULT_MCP_URL), language=None)
    st.write(f"**AI model:** `{GEMINI_MODEL}`")
    st.info("Prototype mode: readings are simulated. Physical pump control is not enabled.")
    if st.button("Test MCP Connection", use_container_width=True):
        try:
            st.session_state["farm"] = farm_context()
            st.success("Authenticated MCP tools responded.")
        except Exception as e:
            st.error(str(e))
    if st.button("Refresh Farm Readings", use_container_width=True):
        try:
            st.session_state["farm"] = farm_context()
            st.success("Farm data refreshed.")
        except Exception as e:
            st.error(str(e))
    st.markdown("---")
    st.caption("AgriGuardian AI • Safe decision support")

# Load data once on initial visit, preserving a visible error if the backend is unavailable.
if "farm" not in st.session_state:
    try:
        st.session_state["farm"] = farm_context()
        st.session_state["farm_error"] = ""
    except Exception as e:
        st.session_state["farm"] = None
        st.session_state["farm_error"] = str(e)


# ------------------------------------------------------------------ page
farm = st.session_state.get("farm")
farm_d = as_dict(farm)
sensors = as_dict(as_dict(farm_d.get("sensor_readings")).get("sensors"))
advice = as_dict(farm_d.get("irrigation_advice"))
soil = sensors.get("soil_moisture_percent", "\u2014")
ambient = sensors.get("ambient_temperature_c", "\u2014")
storage = sensors.get("storage_temperature_c", "\u2014")
water = sensors.get("water_level_percent", "\u2014")
smoke = "Detected" if sensors.get("smoke_detected") else "Not detected"
connected = bool(farm)
conn_txt = "Connected \u00B7 simulated data" if connected else "Offline \u2014 check MCP in sidebar"
ambient_txt = "--" if ambient == "\u2014" else esc(ambient) + "\u00B0C"
storage_txt = "--" if storage == "\u2014" else esc(storage) + "\u00B0C"

SCENE_SVG = """<svg class="ag-scene" viewBox="0 0 1000 440" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
        <defs>
          <linearGradient id="sky" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#2b1d17"/><stop offset=".5" stop-color="#04563f"/><stop offset="1" stop-color="#18b27b"/>
          </linearGradient>
          <radialGradient id="sun"><stop offset="0" stop-color="#ffe9a8" stop-opacity=".95"/><stop offset="1" stop-color="#ffe9a8" stop-opacity="0"/></radialGradient>
          <linearGradient id="h1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b6b4e"/><stop offset="1" stop-color="#063d2d"/></linearGradient>
          <linearGradient id="h2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#087a59"/><stop offset="1" stop-color="#05503b"/></linearGradient>
          <linearGradient id="field" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a8f5c"/><stop offset="1" stop-color="#14583b"/></linearGradient>
        </defs>
        <rect width="1000" height="440" fill="url(#sky)"/>
        <circle cx="770" cy="150" r="190" fill="url(#sun)"/>
        <circle cx="770" cy="150" r="46" fill="#ffecb5" opacity=".9"/>
        <path d="M0 250 C150 190 260 215 400 235 C520 252 640 190 780 215 C880 232 950 220 1000 205 L1000 440 L0 440Z" fill="url(#h1)" opacity=".85"/>
        <path d="M0 290 C140 245 290 270 430 282 C580 295 700 245 840 262 C920 272 970 266 1000 258 L1000 440 L0 440Z" fill="url(#h2)"/>
        <path d="M0 440 L0 318 C200 300 360 300 500 300 C640 300 800 300 1000 318 L1000 440Z" fill="url(#field)"/>
        <g stroke="#9be9c1" stroke-opacity=".28" stroke-width="2.4" fill="none">
          <line x1="-300" y1="440" x2="500" y2="302"/><line x1="-120" y1="440" x2="500" y2="302"/>
          <line x1="60" y1="440" x2="500" y2="302"/><line x1="240" y1="440" x2="500" y2="302"/>
          <line x1="420" y1="440" x2="500" y2="302"/><line x1="580" y1="440" x2="500" y2="302"/>
          <line x1="760" y1="440" x2="500" y2="302"/><line x1="940" y1="440" x2="500" y2="302"/>
          <line x1="1120" y1="440" x2="500" y2="302"/><line x1="1300" y1="440" x2="500" y2="302"/>
        </g>
        <!-- sprinkler drops -->
        <g fill="#bfeeff" opacity=".7">
          <path d="M150 330 q8 14 0 20 q-8 -6 0 -20z"/><path d="M178 322 q8 14 0 20 q-8 -6 0 -20z"/><path d="M122 324 q8 14 0 20 q-8 -6 0 -20z"/>
          <path d="M860 338 q8 14 0 20 q-8 -6 0 -20z"/><path d="M890 328 q8 14 0 20 q-8 -6 0 -20z"/>
        </g>
        <!-- foreground leaves -->
        <g fill="#043f2e">
          <path d="M-10 440 C20 340 90 300 170 296 C150 360 90 410 -10 440Z"/>
          <path d="M40 440 C60 370 130 330 210 332 C190 390 120 430 40 440Z" fill="#06543c"/>
          <path d="M1010 440 C980 350 910 305 830 300 C850 365 915 415 1010 440Z"/>
          <path d="M960 440 C945 375 880 335 800 338 C815 395 880 432 960 440Z" fill="#06543c"/>
        </g>
        <g stroke="#0c8a62" stroke-width="2" fill="none" opacity=".7">
          <path d="M0 436 C60 380 110 335 165 300"/><path d="M1000 436 C940 382 890 340 835 304"/>
        </g>
      </svg>"""
BADGE_SVG = """<svg viewBox="0 0 100 100"><defs><path id="circ" d="M50 50 m-38 0 a38 38 0 1 1 76 0 a38 38 0 1 1 -76 0"/></defs>
          <text font-size="8.2" font-weight="700" letter-spacing="2.4" fill="#e8f3ed"><textPath href="#circ">SIMULATED DATA • SMART FARMING • </textPath></text>
        </svg>"""

md(f'''
<div class="ag-nav">
  <div class="ag-brand"><div class="ag-mark">\u2726</div><span>AgriGuardian.</span></div>
  <div class="ag-conn{"" if connected else " off"}"><i></i><span>{conn_txt}</span></div>
</div>
<div class="ag-hero2">
  <div class="ag-water">AgriGuardian</div>
  <div class="ag-eye"><b>AI</b> Sense \u00B7 Understand \u00B7 Decide \u00B7 Ask \u00B7 Act \u00B7 Verify</div>
  <div class="ag-h1">Smarter Farming With <span>Intelligent Automation</span></div>
  <div class="ag-lead">Monitor your farm, get AI-assisted irrigation advice, approve every action yourself, and verify the result \u2014 all from one connected workspace.</div>
</div>
<div class="ag-showcase">
  <div class="ag-visual">
    {SCENE_SVG}
    <div class="ag-badge">{BADGE_SVG}<div class="core">\U0001F33E</div></div>
    <div class="ag-glass">
      <div class="ag-glass-top"><span>AGRI COMMAND CENTER</span><span class="ag-live"><i></i>PROTOTYPE \u00B7 SIMULATED</span></div>
      <div class="ag-glass-title">Your farm. Connected, understood, and ready to act.</div>
      <div class="ag-flow">Sense \u2192 Understand \u2192 Decide \u2192 Ask \u2192 Act \u2192 Verify</div>
      <div class="ag-readings">
        <div class="ag-reading"><b>{pct(soil)}</b><span>SOIL MOISTURE</span></div>
        <div class="ag-reading"><b>{ambient_txt}</b><span>AMBIENT TEMP</span></div>
        <div class="ag-reading"><b>{storage_txt}</b><span>STORAGE TEMP</span></div>
        <div class="ag-reading"><b>{pct(water)}</b><span>WATER TANK</span></div>
      </div>
    </div>
  </div>
  <div class="ag-services">
    <div class="ag-svc"><div><div class="t">Farm Monitoring</div><small>SIMULATED SENSOR DATA</small></div><div class="arrow">\u2192</div></div>
    <div class="ag-svc"><div><div class="t">AI Irrigation Advice</div><small>RECOMMEND \u00B7 YOU DECIDE</small></div><div class="arrow">\u2192</div></div>
    <div class="ag-svc"><div><div class="t">Crop Health</div><small>GEMINI VISION</small></div><div class="arrow">\u2192</div></div>
    <div class="ag-svc"><div><div class="t">Learn Farming</div><small>CROPS \u00B7 VIDEOS \u00B7 SKILLS</small></div><div class="arrow">\u2192</div></div>
    <div class="ag-svc"><div><div class="t">Authenticated MCP</div><small>PRIVATE SERVER-SIDE ACCESS</small></div><div class="arrow">\u2192</div></div>
  </div>
</div>
''')

dashboard, assistant, leaf, guide, about = st.tabs(
    ["Farm Dashboard", "Ask AgriGuardian", "Crop Health", "Farm Guide", "About AgriGuardian"]
)

with dashboard:
    md('''
    <div class="ag-intro"><div><div class="ag-kicker">Introduction</div></div>
    <div class="ag-intro-text">AgriGuardian AI combines farm sensor data with an MCP agent layer so your farm can be monitored, interpreted, acted on and verified \u2014 while you stay in control of every decision.</div></div>
    <div class="ag-stats">
    <div class="ag-stat"><b>Simulated</b><span>Prototype data mode</span></div>
    <div class="ag-stat"><b>2</b><span>MCP tools in use</span></div>
    <div class="ag-stat"><b>6-step</b><span>Decision workflow</span></div>
    <div class="ag-stat"><b>You decide</b><span>Nothing runs without you</span></div>
    </div>
    ''')
    section_head("Farm Monitoring", "Key conditions from the connected farm node (prototype values are simulated).", "SIMULATED DATA")
    if farm:
        soil_n, water_n = to_num(soil), to_num(water)
        soil_note = "Sensor reading" if soil_n is None else "Dry \u2014 may need irrigation" if soil_n < 30 else "Moderate moisture" if soil_n < 60 else "Moist soil"
        water_note = "Sensor reading" if water_n is None else "Low \u2014 refill the tank" if water_n < 20 else "Moderate level" if water_n < 60 else "Good level"
        cards = "".join([
            metric("\U0001F331", "Soil moisture", pct(soil), soil_note, soil, soil_n is not None and soil_n < 30),
            metric("\u2600\uFE0F", "Ambient temperature", "--" if ambient == "\u2014" else f"{esc(ambient)} \u00B0C", "Farm environment"),
            metric("\U0001F3E1", "Storage temperature", "--" if storage == "\u2014" else f"{esc(storage)} \u00B0C", "Storage environment"),
            metric("\U0001F6B0", "Water level", pct(water), water_note, water, water_n is not None and water_n < 20),
            metric("\U0001F6E1\uFE0F", "Smoke status", esc(smoke), "Gas/smoke status from prototype data", None, smoke == "Detected", True),
        ])
        md(f'<div class="ag-metrics">{cards}</div>')
        section_head("Irrigation guidance", "AgriGuardian recommends. You decide. Pump control is not enabled in this demo.", "ADVICE ONLY")
        recommendation = advice.get("recommendation", "No recommendation available")
        yes = is_recommended(recommendation)
        verdict_icon = "\U0001F4A7" if yes else "\U0001F33F"
        steps_html = "".join(
            f'<div class="ag-step {cls}"><i></i>{label}</div>'
            for label, cls in [("Sense", "done"), ("Understand", "done"), ("Decide", "done"), ("Ask", "now"), ("Act*", ""), ("Verify*", "")]
        )
        md(
            f'''<div class="ag-card2"><div class="ag-card2-title">\U0001F916 AI irrigation advisor</div>
            <div class="ag-steps">{steps_html}</div>
            <div class="ag-verdict {"yes" if yes else "no"}"><div class="vi">{verdict_icon}</div>
            <div><b>{"Irrigation may be needed" if yes else "Irrigation not needed right now"}</b><span>{esc(recommendation)}</span></div></div>
            <div class="ag-note">*Act and Verify are planned workflow stages. Physical pump control is not enabled in this demo.</div></div>'''
        )
        with st.expander("View raw MCP response"):
            st.json(farm)
    else:
        st.warning("Farm data could not be loaded. Use Test MCP Connection in the sidebar.")
        if st.session_state.get("farm_error"):
            st.code(st.session_state["farm_error"])

with assistant:
    section_head("Ask AgriGuardian", "Ask about farm conditions or irrigation. Answers use the current prototype data.", "GEMINI AI")
    if "chat" not in st.session_state:
        st.session_state["chat"] = []
    for message in st.session_state["chat"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    question = st.chat_input("e.g. Should I consider irrigation?")
    if question:
        st.session_state["chat"].append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Checking farm context and asking Gemini..."):
                try:
                    context = farm_context()
                    st.session_state["farm"] = context
                    answer = answer_question(question, context)
                except Exception as e:
                    answer = f"Request failed: {e}"
                st.markdown(answer)
        st.session_state["chat"].append({"role": "assistant", "content": answer})

with leaf:
    section_head("Crop Health", "View your ESP32-CAM and capture a crop image for preliminary AI observations.", "ESP32-CAM + GEMINI")
    camera_url = secret("ESP32CAM_URL", "http://10.202.111.228").strip().rstrip("/")
    left, right = st.columns([1, 1.25], gap="large")
    with left:
        md(
            '''<div class="ag-crop-side"><div class="ag-card2-title">\U0001F343 ESP32-CAM crop camera</div>
            <div class="s">Keep this computer connected to the same Wi-Fi/mobile hotspot as the ESP32-CAM. Use the refresh button to request a new camera snapshot.</div>
            <div class="s">AI findings are preliminary, not a definitive diagnosis.</div></div>'''
        )
        import streamlit.components.v1 as components
        components.html(f'''
          <div style="font-family:Arial,sans-serif;color:#241914">
            <img id="agcam" src="{html.escape(camera_url, quote=True)}/capture?ts=1"
              style="width:100%;border-radius:16px;border:1px solid #ddd7ca;min-height:180px;object-fit:contain;background:#211611"
              alt="ESP32-CAM snapshot" />
            <button onclick="document.getElementById('agcam').src='{html.escape(camera_url, quote=True)}/capture?ts='+Date.now()"
              style="margin-top:10px;padding:10px 16px;border:0;border-radius:24px;background:#087a59;color:white;font-weight:bold;cursor:pointer">Refresh camera image</button>
            <a href="{html.escape(camera_url, quote=True)}/capture" target="_blank" rel="noopener"
              style="margin-left:8px;color:#04563f;font-weight:bold">Open full image</a>
          </div>''', height=390, scrolling=False)
        st.caption("If the preview is blocked on the HTTPS dashboard, browser security is preventing an HTTPS page from loading the camera's local HTTP address.")
    with right:
        st.markdown("**Analyze a crop image**")
        st.write("Capture the image from the camera, save it, then upload it here for Gemini analysis.")
        upload = st.file_uploader("Upload captured crop image", type=["jpg", "jpeg", "png", "webp"], key="crop_health_upload")
        if upload:
            st.image(upload, caption="Crop image selected for analysis", use_container_width=True)
            if st.button("Analyze leaf with Gemini", type="primary"):
                with st.spinner("Gemini is analyzing the image..."):
                    try:
                        st.markdown(analyze_leaf(upload))
                    except Exception as e:
                        st.error(f"Leaf analysis failed: {e}")

with guide:
    section_head("Farm Guide and Learning Hub", "Crop facts, sowing windows and how-to videos for every part of farming.", f"NOW \u00B7 {season_of(NOW_M).upper()} \u00B7 {MONTHS[NOW_M - 1].upper()}")
    sow_now = [c for c in CROPS if NOW_M in c["sow"]]
    chips = "".join(f'<span class="ag-chip">{c["e"]} {esc(c["name"])}</span>' for c in sow_now) or '<span class="ag-chip">No main sowing month for the listed crops</span>'
    md(f'<div class="ag-season"><div class="ag-season-t"><b>\U0001F331 Sow now</b> \u00B7 {MONTHS[NOW_M - 1]} \u00B7 {season_of(NOW_M)} season</div><div class="ag-chips">{chips}</div></div>')
    vlang = st.radio("Video language", list(VIDEO_LANGS), horizontal=True, key="vid_lang")

    st.markdown("### \U0001F33E Crop guide")
    choice_filter = st.radio("Filter crops", ["All", "Sow now", "Kharif", "Rabi", "Zaid"], horizontal=True)
    visible = [
        c for c in CROPS
        if choice_filter == "All"
        or (choice_filter == "Sow now" and NOW_M in c["sow"])
        or choice_filter in c["seasons"]
    ]
    if visible:
        labels = {f"{c['e']} {c['name']}": c for c in visible}
        picked = labels[st.selectbox("Choose a crop", list(labels))]
        md(crop_info_html(picked))
        st.markdown("### \U0001F3AC How to grow this crop")
        render_videos(picked["q"], vlang, "crop_vid")
    else:
        st.info("No crops match this filter this month.")

    md(
        '<div class="ag-learn"><div class="ag-learn-k">LEARNING HUB</div>'
        '<div class="ag-learn-t">Learn anything about farming</div>'
        '<div class="ag-learn-s">Soil, water, pests, livestock, schemes and machines. Pick a topic or search your own, in English, Tamil or Hindi.</div>'
        '<div class="ag-chips"><span class="ag-chip lt">8 topic groups</span><span class="ag-chip lt">40+ topics</span><span class="ag-chip lt">3 languages</span></div></div>'
    )
    search = st.text_input("Search any farming topic", placeholder="For example: banana leaf spot, goat shed, tractor loan", key="hub_search")
    if search.strip():
        q = search.strip()
        render_videos(q if "farm" in q.lower() else q + " farming", vlang, "search_vid")
    else:
        group_names = [g[0] for g in TOPIC_GROUPS]
        group = st.radio("Category", group_names, horizontal=True, key="hub_group")
        gi = group_names.index(group)
        topics = TOPIC_GROUPS[gi][1]
        topic = st.radio("Topic", [t[0] for t in topics], horizontal=True, key=f"hub_topic_{gi}")
        render_videos(dict(topics)[topic], vlang, "hub_vid")

    with st.expander("Browse every topic on YouTube"):
        suffix = VIDEO_LANGS[vlang][0]
        for gname, topics in TOPIC_GROUPS:
            st.markdown(f"**{gname}**")
            cols = st.columns(3)
            for i, (lbl, q) in enumerate(topics):
                cols[i % 3].link_button(lbl, yt_search_url(q + suffix))
    with st.expander("Sensor and smart-irrigation setup videos (for this dashboard)"):
        t1, t2 = st.columns(2, gap="large")
        with t1:
            st.video("https://www.youtube.com/watch?v=8UG_jWSij04")
            st.caption("Install a soil moisture sensor \u00B7 Mobitech Wireless")
        with t2:
            st.video("https://www.youtube.com/watch?v=EX7sC-ksH4o")
            st.caption("ESP32 smart plant watering \u00B7 IoT Circuit Hub")
    st.info("Crop figures are general guidance, so confirm with your local agriculture office.")

with about:
    st.markdown('<div class="ag-st"><div><div class="ag-h2">About AgriGuardian AI</div></div></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="ag-panel">
        <strong>Purpose</strong><br>
        Demonstrate an AI-assisted farm monitoring and irrigation decision-support workflow.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("- **Cloud backend:** AWS EC2 MCP server.")
    st.markdown("- **AI assistant and leaf analysis:** Google Gemini API.")
    st.markdown("- **MCP tools:** `get_sensor_readings` and `get_irrigation_recommendation`.")
    st.markdown("- **Data status:** fixed simulated values in this dashboard.")
    st.markdown("- **Safety:** no pump-control command is exposed by this dashboard.")
    st.warning("Do not present simulated values as live field measurements. Leaf analysis is preliminary and may be incorrect.")


md('''<div class="ag-footer">AgriGuardian AI \u00B7 Sense \u2022 Understand \u2022 Decide \u2022 Ask \u2022 Act \u2022 Verify \u00B7 Prototype with simulated data</div>''')
enable_service_links()
