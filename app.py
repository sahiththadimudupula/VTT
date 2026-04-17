
from __future__ import annotations

import streamlit as st

from wtt_app.config import (
    APP_ICON,
    APP_TITLE,
    SOURCE_WORKBOOK_PATH,
    TAB_CUT_SEW,
    TAB_PROCESSING,
    TAB_SIZE_WISE,
    TAB_VTT,
    TAB_WEAVING,
)
from wtt_app.core.workbook import initialize_workbook_state
from wtt_app.ui.components import render_hero, render_sidebar
from wtt_app.ui.styles import inject_professional_styles
from wtt_app.ui.tabs import (
    render_cut_sew_tab,
    render_processing_tab,
    render_size_wise_tab,
    render_vtt_tab,
    render_weaving_tab,
)

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
    inject_professional_styles()

    if not SOURCE_WORKBOOK_PATH.exists():
        st.error(f"Source workbook not found at: {SOURCE_WORKBOOK_PATH}")
        st.stop()

    initialize_workbook_state()
    render_sidebar()
    render_hero()

    tabs = st.tabs([TAB_SIZE_WISE, TAB_WEAVING, TAB_PROCESSING, TAB_CUT_SEW, TAB_VTT])

    with tabs[0]:
        render_size_wise_tab()
    with tabs[1]:
        render_weaving_tab()
    with tabs[2]:
        render_processing_tab()
    with tabs[3]:
        render_cut_sew_tab()
    with tabs[4]:
        render_vtt_tab()


if __name__ == "__main__":
    main()
