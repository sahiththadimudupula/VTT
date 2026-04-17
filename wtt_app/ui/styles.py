from __future__ import annotations

from textwrap import dedent

import streamlit as st


def inject_professional_styles() -> None:
    st.markdown(
        dedent(
            """
            <style>
            :root {
                --primary: #1e40af;
                --primary-2: #2563eb;
                --primary-3: #38bdf8;
                --bg-1: #f4f8ff;
                --bg-2: #edf4ff;
                --surface: rgba(255,255,255,0.82);
                --surface-strong: rgba(255,255,255,0.94);
                --text-1: #0f172a;
                --text-2: #334155;
                --text-3: #64748b;
                --border: rgba(148,163,184,0.18);
                --shadow-xs: 0 4px 12px rgba(15,23,42,0.04);
                --shadow-sm: 0 10px 28px rgba(15,23,42,0.07);
                --shadow-md: 0 18px 42px rgba(15,23,42,0.10);
            }

            html, body, [class*="css"] {
                font-family: "Inter", "Segoe UI", sans-serif;
            }

            header, [data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu, footer, [data-testid="stDecoration"], [data-testid="stStatusWidget"] {
                display: none !important;
                height: 0 !important;
                visibility: hidden !important;
            }

            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(56,189,248,0.08), transparent 22%),
                    radial-gradient(circle at top right, rgba(37,99,235,0.09), transparent 25%),
                    linear-gradient(180deg, var(--bg-1) 0%, var(--bg-2) 100%);
                color: var(--text-1);
            }

            .block-container, .main .block-container {
                max-width: 1540px;
                padding-top: 0.4rem !important;
                padding-bottom: 1rem !important;
                margin-top: 0 !important;
            }

            .element-container {
                margin-bottom: 0.25rem !important;
            }

            div[data-testid="stTabs"] [role="tablist"] {
                gap: 0.35rem;
                background: rgba(255,255,255,0.60);
                border: 1px solid rgba(148,163,184,0.16);
                padding: 0.35rem;
                border-radius: 16px;
                backdrop-filter: blur(12px);
                box-shadow: var(--shadow-xs);
            }

            div[data-testid="stTabs"] button {
                font-weight: 700;
                font-size: 0.92rem;
                padding: 0.62rem 0.92rem;
                color: var(--text-2) !important;
                border-radius: 12px !important;
                transition: all 0.22s ease;
            }

            div[data-testid="stTabs"] button:hover {
                background: rgba(37, 99, 235, 0.08) !important;
                color: var(--primary-2) !important;
            }

            div[data-testid="stTabs"] button[aria-selected="true"] {
                background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%) !important;
                color: #ffffff !important;
                box-shadow: 0 10px 24px rgba(37, 99, 235, 0.22);
            }

            div[data-testid="stTabs"] button p {
                color: inherit !important;
            }

            .stButton > button, .stDownloadButton > button {
                width: 100%;
                min-height: 46px;
                border-radius: 14px;
                border: 1px solid rgba(255,255,255,0.18);
                background: linear-gradient(135deg, #1e40af 0%, #2563eb 58%, #38bdf8 100%);
                color: #ffffff !important;
                font-weight: 700;
                font-size: 0.93rem;
                box-shadow: 0 14px 30px rgba(37,99,235,0.20);
            }

            .hero-shell {
                background: rgba(255,255,255,0.72);
                border-radius: 22px;
                padding: 0.8rem 1rem 0.8rem 1rem;
                box-shadow: var(--shadow-sm);
                border: 1px solid rgba(255,255,255,0.46);
                margin-bottom: 0.65rem;
                backdrop-filter: blur(16px);
            }

            .hero-title {
                font-size: 1.45rem !important;
                font-weight: 900;
                line-height: 1.02;
                color: var(--text-1) !important;
                margin: 0;
            }

            .metric-card {
                background: linear-gradient(180deg, rgba(255,255,255,0.86) 0%, rgba(255,255,255,0.76) 100%);
                border-radius: 20px;
                padding: 0.88rem 1rem 0.82rem 1rem;
                box-shadow: var(--shadow-sm);
                border: 1px solid rgba(255,255,255,0.45);
                min-height: 108px;
                position: relative;
                overflow: hidden;
                backdrop-filter: blur(16px);
            }

            .metric-card::after {
                content: "";
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 4px;
                background: linear-gradient(90deg, #1e40af 0%, #2563eb 55%, #38bdf8 100%);
            }

            .metric-label {
                color: var(--text-3);
                font-size: 0.78rem;
                font-weight: 800;
                margin-bottom: 0.34rem;
                text-transform: uppercase;
                letter-spacing: 0.25px;
            }

            .metric-value {
                color: var(--text-1);
                font-size: 1.68rem;
                font-weight: 900;
                line-height: 1.04;
                margin-bottom: 0.16rem;
            }

            .metric-note {
                color: var(--text-3);
                font-size: 0.78rem;
                font-weight: 500;
            }

            .panel-card {
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
                padding: 0 !important;
                margin: 0 !important;
            }

            .section-title {
                font-size: 1rem;
                font-weight: 900;
                color: var(--text-1);
                margin-bottom: 0.08rem;
            }

            .section-subtitle {
                color: var(--text-3);
                font-size: 0.84rem;
                margin-bottom: 0.75rem;
                line-height: 1.5;
            }

            div[data-testid="stDataEditor"], div[data-testid="stDataFrame"] {
                border-radius: 18px;
                overflow: hidden;
                border: 1px solid rgba(148,163,184,0.18);
                background: rgba(255,255,255,0.82);
                backdrop-filter: blur(14px);
                box-shadow: var(--shadow-sm);
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, rgba(255,255,255,0.84) 0%, rgba(255,255,255,0.72) 100%);
                border-right: 1px solid rgba(148,163,184,0.14);
            }

            .sidebar-heading {
                font-size: 0.88rem;
                font-weight: 800;
                color: var(--text-1);
                margin-bottom: 0.2rem;
            }

            .divider-space {
                margin-top: 0.6rem;
            }
            </style>
            """
        ),
        unsafe_allow_html=True,
    )
