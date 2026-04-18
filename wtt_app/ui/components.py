from __future__ import annotations

from html import escape
from textwrap import dedent
from typing import Any

import pandas as pd
import streamlit as st

from wtt_app.config import (
    DTA_SHEET,
    JUKI_SHEET,
    SIZE_WISE_DETAILS_SHEET,
    SIZE_WISE_SUMMARY_SHEET,
    SOURCE_WORKBOOK_PATH,
    STENTER_MANPOWER_SHEET,
    STENTER_PLAN_SHEET,
    TT_CUT_SEW_LC_SHEET,
    TT_CUT_SEW_LH_SHEET,
    WEAVING_BACKUP_SHEET,
    WTT_SHEET,
    WTT_EDITABLE_COLUMNS,
)
from wtt_app.core.formatters import (
    build_numeric_column_config,
    format_dataframe_for_display,
    format_number,
)
from wtt_app.core.workbook import build_export_bytes, get_workbook_state, reset_workbook_state


def render_hero() -> None:
    st.markdown(
        dedent(
            """
            <div class="hero-shell">
                <div class="hero-title">Welspun Vapi Terry Towel Engine</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def render_section_header(title: str, note: str | None = None) -> None:
    note_block = f'<div class="section-subtitle">{escape(note)}</div>' if note else ''
    st.markdown(
        f'<div class="panel-card"><div class="section-title">{escape(title)}</div>{note_block}</div>',
        unsafe_allow_html=True,
    )


def render_metric_grid(metrics: list[dict[str, Any]]) -> None:
    metric_columns = st.columns(len(metrics))
    for column, metric in zip(metric_columns, metrics):
        with column:
            st.markdown(
                dedent(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">{escape(str(metric['label']))}</div>
                        <div class="metric-value">{escape(format_number(metric['value']))}</div>
                        <div class="metric-note">{escape(str(metric['note']))}</div>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )


def render_read_only_table(
    title: str,
    dataframe: pd.DataFrame,
    height: int = 360,
    note: str | None = None,
) -> None:
    render_section_header(title, note)
    st.dataframe(
        format_dataframe_for_display(dataframe),
        use_container_width=True,
        hide_index=True,
        height=height,
    )


def render_editable_wtt_table(
    title: str,
    dataframe: pd.DataFrame,
    key_prefix: str,
    note: str | None = None,
) -> pd.DataFrame:
    render_section_header(title, note)
    disabled_columns = [
        column_name
        for column_name in dataframe.columns
        if column_name not in WTT_EDITABLE_COLUMNS
    ]
    editable_columns = [
        column_name
        for column_name in WTT_EDITABLE_COLUMNS
        if column_name in dataframe.columns
    ]
    return st.data_editor(
        dataframe.reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key=f"{key_prefix}_editor",
        disabled=disabled_columns,
        column_config=build_numeric_column_config(editable_columns),
    )


def render_section_summary(title: str, dataframe: pd.DataFrame) -> None:
    summary_dataframe = (
        dataframe.groupby("Section", dropna=False)[["Machine_Count", "BE_Final_Manpower"]]
        .sum(numeric_only=True)
        .reset_index()
    )
    render_read_only_table(
        title=title,
        dataframe=summary_dataframe,
        height=min(340, 70 + len(summary_dataframe) * 36),
    )


def render_validation_warning(dataframe: pd.DataFrame, section_name: str) -> None:
    required_columns = [
        "BE_Final_Manpower",
        "General_Shift",
        "Shift_A",
        "Shift_B",
        "Shift_C",
    ]
    if any(column_name not in dataframe.columns for column_name in required_columns):
        return

    validation_dataframe = dataframe.copy()
    validation_dataframe["Shift_Total"] = validation_dataframe[
        ["General_Shift", "Shift_A", "Shift_B", "Shift_C"]
    ].sum(axis=1)
    validation_dataframe["Difference"] = (
        validation_dataframe["BE_Final_Manpower"] - validation_dataframe["Shift_Total"]
    )
    mismatch_dataframe = validation_dataframe[
        validation_dataframe["Difference"].round(2) != 0.0
    ][["Designation", "BE_Final_Manpower", "Shift_Total", "Difference"]]

    if mismatch_dataframe.empty:
        st.success(f"{section_name}: shift allocation matches BE_Final_Manpower.")
        return

    st.warning(
        f"{section_name}: some rows have a gap between BE_Final_Manpower and shift allocation."
    )
    st.dataframe(
        format_dataframe_for_display(mismatch_dataframe),
        use_container_width=True,
        hide_index=True,
        height=min(260, 70 + len(mismatch_dataframe) * 36),
    )


def render_sidebar() -> None:
    workbook_state = get_workbook_state()
    sheets = workbook_state["sheets"]
    wtt_dataframe = sheets[WTT_SHEET]

    st.sidebar.markdown('<div class="sidebar-heading">Workbook source</div>', unsafe_allow_html=True)
    st.sidebar.code(str(SOURCE_WORKBOOK_PATH), language=None)
    st.sidebar.caption("Loaded directly from the local input folder. No upload step is required.")

    if st.sidebar.button("Reload source workbook"):
        reset_workbook_state()
        st.rerun()

    export_sheet_map = {
        SIZE_WISE_DETAILS_SHEET: sheets[SIZE_WISE_DETAILS_SHEET],
        SIZE_WISE_SUMMARY_SHEET: sheets[SIZE_WISE_SUMMARY_SHEET],
        WEAVING_BACKUP_SHEET: sheets[WEAVING_BACKUP_SHEET],
        STENTER_PLAN_SHEET: sheets[STENTER_PLAN_SHEET],
        STENTER_MANPOWER_SHEET: sheets[STENTER_MANPOWER_SHEET],
        TT_CUT_SEW_LC_SHEET: sheets[TT_CUT_SEW_LC_SHEET],
        TT_CUT_SEW_LH_SHEET: sheets[TT_CUT_SEW_LH_SHEET],
        DTA_SHEET: sheets[DTA_SHEET],
        JUKI_SHEET: sheets[JUKI_SHEET],
        WTT_SHEET: sheets[WTT_SHEET],
    }
    st.sidebar.download_button(
        label="Download updated workbook",
        data=build_export_bytes(export_sheet_map),
        file_name="WTT_updated_executive.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.sidebar.markdown('<div class="sidebar-heading divider-space">Quick totals</div>', unsafe_allow_html=True)
    st.sidebar.write(f"**BE Final Manpower:** {format_number(wtt_dataframe['BE_Final_Manpower'].sum())}")
    st.sidebar.write(f"**BE Scientific Manpower:** {format_number(wtt_dataframe['BE_Scientific_Manpower'].sum())}")
