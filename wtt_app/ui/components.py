from __future__ import annotations

from html import escape
from textwrap import dedent
from typing import Any

import pandas as pd
import streamlit as st

from wtt_app.config import (
    DTA_SHEET,
    FORMULA_TAG_COLUMN,
    JUKI_SHEET,
    SIZE_WISE_DETAILS_SHEET,
    SIZE_WISE_SUMMARY_SHEET,
    SOURCE_WORKBOOK_PATH,
    STENTER_MANPOWER_SHEET,
    STENTER_PLAN_SHEET,
    TT_CUT_SEW_LC_SHEET,
    TT_CUT_SEW_LH_SHEET,
    WEAVING_BACKUP_SHEET,
    WTT_INTERNAL_ROW_ID_COLUMN,
    WTT_COMPACT_DISPLAY_COLUMNS,
    WTT_EDITABLE_COLUMNS,
    WTT_EXPANDED_DISPLAY_COLUMNS,
    WTT_SHEET,
)
from wtt_app.core.formatters import (
    build_numeric_column_config,
    format_dataframe_for_display,
    format_number,
)
from wtt_app.core.tables import (
    add_total_row,
    build_compact_section_table,
    build_expanded_editable_table,
)
from wtt_app.core.workbook import build_export_bytes, freeze_workbook_state, get_workbook_state, has_unsaved_changes, reset_workbook_state


def render_hero() -> None:
    st.markdown(
        dedent(
            """
            <div class="hero-shell">
                <div class="hero-title">Welspun Vapi Terry Tovals Engine</div>
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
    if not metrics:
        return
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


def render_filter_block(title: str) -> None:
    st.markdown(
        f'<div class="filter-shell"><div class="section-title" style="margin-bottom:0;">{escape(title)}</div></div>',
        unsafe_allow_html=True,
    )


def render_read_only_table(
    title: str,
    dataframe: pd.DataFrame,
    height: int = 360,
    note: str | None = None,
    label_column: str | None = None,
) -> None:
    render_section_header(title, note)
    dataframe_with_total = add_total_row(dataframe, label_column=label_column)
    st.dataframe(
        format_dataframe_for_display(dataframe_with_total),
        width='stretch',
        hide_index=True,
        height=height,
    )


def render_compact_section_table(section_name: str, section_dataframe: pd.DataFrame) -> None:
    compact_dataframe = build_compact_section_table(section_dataframe, WTT_COMPACT_DISPLAY_COLUMNS)
    render_read_only_table(
        title=section_name,
        dataframe=compact_dataframe,
        height=min(300, 90 + len(compact_dataframe) * 36),
        note="Visible section view",
        label_column="Section",
    )


def render_expandable_editable_section(
    section_name: str,
    section_dataframe: pd.DataFrame,
    key_prefix: str,
) -> pd.DataFrame:
    expanded_dataframe = build_expanded_editable_table(section_dataframe, WTT_EXPANDED_DISPLAY_COLUMNS)
    disabled_columns = [
        column_name
        for column_name in expanded_dataframe.columns
        if column_name not in WTT_EDITABLE_COLUMNS and column_name != WTT_INTERNAL_ROW_ID_COLUMN
    ]
    editable_numeric_columns = [
        column_name for column_name in WTT_EDITABLE_COLUMNS if column_name in expanded_dataframe.columns and column_name != "Remarks"
    ]
    column_config = build_numeric_column_config(editable_numeric_columns)
    column_config[WTT_INTERNAL_ROW_ID_COLUMN] = None

    with st.expander(f"Expand Section - {section_name}"):
        edited_dataframe = st.data_editor(
            expanded_dataframe.reset_index(drop=True),
            width='stretch',
            hide_index=True,
            num_rows="fixed",
            key=f"{key_prefix}_editor",
            disabled=disabled_columns,
            column_config=column_config,
        )
        return edited_dataframe


def render_section_summary(title: str, dataframe: pd.DataFrame) -> None:
    summary_dataframe = (
        dataframe.groupby("Section", dropna=False)[["Machine_Count", "BE_Final_Manpower"]]
        .sum(numeric_only=True)
        .reset_index()
    )
    render_read_only_table(
        title=title,
        dataframe=summary_dataframe,
        height=min(340, 80 + len(summary_dataframe) * 36),
        label_column="Section",
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
    validation_dataframe = validation_dataframe[validation_dataframe["Designation"].astype(str) != "Total"].copy() if "Designation" in validation_dataframe.columns else validation_dataframe
    validation_dataframe["Shift_Total"] = validation_dataframe[
        ["General_Shift", "Shift_A", "Shift_B", "Shift_C"]
    ].sum(axis=1)
    validation_dataframe["Difference"] = (
        pd.to_numeric(validation_dataframe["BE_Final_Manpower"], errors="coerce") - validation_dataframe["Shift_Total"]
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
        format_dataframe_for_display(add_total_row(mismatch_dataframe, label_column="Designation")),
        width='stretch',
        hide_index=True,
        height=min(260, 80 + len(mismatch_dataframe) * 36),
    )


def render_bottom_action_panel() -> None:
    workbook_state = get_workbook_state()
    sheets = workbook_state["sheets"]
    wtt_dataframe = sheets[WTT_SHEET]

    render_section_header(
        "Workbook controls",
        "Freeze current planning edits to the working workbook, reset to the latest PPC source, or download the current workbook.",
    )
    is_working_source = str(workbook_state.get("source_path", SOURCE_WORKBOOK_PATH)) == str(SOURCE_WORKBOOK_PATH) and False
    current_source_label = "Working File" if "output" in str(workbook_state.get("source_path", "")).lower() else "Original Input"
    unsaved_changes_label = "Yes" if has_unsaved_changes() else "No"
    st.markdown(
        f'<div class="bottom-action-shell"><div class="bottom-action-status">Current Source: <span>{escape(current_source_label)}</span> &nbsp;|&nbsp; Unsaved Changes: <span>{escape(unsaved_changes_label)}</span></div></div>',
        unsafe_allow_html=True,
    )

    action_column_1, action_column_2, action_column_3 = st.columns([1, 1, 1.35])
    with action_column_1:
        if st.button("Freeze Changes", key="freeze_workbook_bottom"):
            freeze_workbook_state()
            st.success("All current changes have been frozen to the working workbook.")
            st.rerun()
    with action_column_2:
        if st.button("Reset to original", key="reset_workbook_bottom"):
            reset_workbook_state()
            st.success("Workbook reset to the latest original input file.")
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
    with action_column_3:
        st.download_button(
            label="Download updated workbook",
            data=build_export_bytes(export_sheet_map),
            file_name="WTT_updated_executive.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_workbook_bottom",
        )

    metric_columns = st.columns(2)
    with metric_columns[0]:
        st.markdown(
            f'<div class="bottom-action-metric">Final Manpower: <span>{escape(format_number(pd.to_numeric(wtt_dataframe["BE_Final_Manpower"], errors="coerce").sum()))}</span></div>',
            unsafe_allow_html=True,
        )
    with metric_columns[1]:
        st.markdown(
            f'<div class="bottom-action-metric">Visible Sections: <span>{wtt_dataframe["Section"].nunique():,.0f}</span></div>',
            unsafe_allow_html=True,
        )

    formula_registry = pd.DataFrame(workbook_state.get("formula_registry", []))
    if not formula_registry.empty:
        with st.expander("Formula tags"):
            st.dataframe(formula_registry[[FORMULA_TAG_COLUMN, "Target Section", "Target Designation"]], width='stretch', hide_index=True)
