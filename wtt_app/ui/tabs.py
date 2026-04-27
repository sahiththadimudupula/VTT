from __future__ import annotations

import pandas as pd
import streamlit as st

from wtt_app.calculations.summary import (
    extract_summary_category_value,
    extract_summary_per_day_value,
)
from wtt_app.config import (
    DECIMAL_STEP,
    DTA_SHEET,
    JUKI_SHEET,
    SECTION_ORDER_CUT_SEW,
    SECTION_ORDER_PROCESSING,
    SECTION_ORDER_WEAVING,
    SIZE_CATEGORY_ORDER,
    SIZE_WISE_DETAILS_SHEET,
    SIZE_WISE_SUMMARY_SHEET,
    STENTER_MANPOWER_SHEET,
    STENTER_PLAN_SHEET,
    STREAMLIT_NUMBER_FORMAT,
    SUMMARY_EDITABLE_COLUMNS,
    TT_CUT_SEW_LC_SHEET,
    TT_CUT_SEW_LH_SHEET,
    WEAVING_BACKUP_SHEET,
    WTT_SHEET,
)
from wtt_app.calculations.links import refresh_calculated_workbook
from wtt_app.core.formatters import build_numeric_column_config, format_dataframe_for_display
from wtt_app.core.tables import (
    add_total_row,
    apply_designation_filter,
    available_designations,
    remove_total_row,
)
from wtt_app.core.workbook import (
    build_export_bytes,
    get_workbook_state,
    mark_unsaved_changes,
    replace_size_wise_details_sheet,
    set_workbook_state,
    update_wtt_section,
)
from wtt_app.ui.components import (
    render_compact_section_table,
    render_expandable_editable_section,
    render_filter_block,
    render_metric_grid,
    render_read_only_table,
    render_section_header,
    render_section_summary,
    render_validation_warning,
)


def build_summary_override_editor(summary_dataframe: pd.DataFrame) -> pd.DataFrame:
    editable_dataframe = summary_dataframe[
        summary_dataframe["Row Labels"].isin(SIZE_CATEGORY_ORDER)
    ][["Row Labels", "Sum of Order Pcs", "Sum of Order Kgs"]].copy()
    return editable_dataframe.reset_index(drop=True)


def _render_designation_filter(filter_key: str, dataframe: pd.DataFrame) -> list[str]:
    designation_values = available_designations(dataframe)
    render_filter_block("Designation filter")
    return st.multiselect(
        "Designation",
        options=designation_values,
        default=[],
        key=filter_key,
        label_visibility="collapsed",
        placeholder="All designations",
    )


def _render_section_collection(
    section_order: list[str],
    tab_key_prefix: str,
    tab_dataframe: pd.DataFrame,
) -> None:
    for section_name in section_order:
        section_dataframe = tab_dataframe[tab_dataframe["Section"] == section_name].copy()
        if section_dataframe.empty:
            continue
        render_compact_section_table(section_name, section_dataframe)
        edited_dataframe = render_expandable_editable_section(
            section_name,
            section_dataframe,
            f"{tab_key_prefix}_{section_name}",
        )
        action_column, _ = st.columns([1, 6])
        with action_column:
            if st.button(f"Apply {section_name}", key=f"save_{tab_key_prefix}_{section_name}"):
                update_wtt_section(section_name, edited_dataframe, persist=False)
                st.success(f"{section_name} updated in the live workbook state. Freeze Changes to keep it after refresh.")
                st.rerun()
        render_validation_warning(remove_total_row(edited_dataframe), section_name)


def render_size_wise_tab() -> None:
    workbook_state = get_workbook_state()
    summary_dataframe = workbook_state["sheets"][SIZE_WISE_SUMMARY_SHEET]
    size_wise_details = workbook_state["sheets"][SIZE_WISE_DETAILS_SHEET]

    render_metric_grid(
        [
            {
                "label": "Total Order Pcs",
                "value": extract_summary_category_value(summary_dataframe, "Total", "Sum of Order Pcs"),
                "note": "3% prediction adjustment included",
            },
            {
                "label": "Total Order Kgs",
                "value": extract_summary_category_value(summary_dataframe, "Total", "Sum of Order Kgs"),
                "note": "3% prediction adjustment included",
            },
            {
                "label": "Per Day Pcs",
                "value": extract_summary_per_day_value(summary_dataframe, "Sum of Order Pcs"),
                "note": "Driver for all Cut&Sew calculators",
            },
            {
                "label": "Pcs / Kg",
                "value": extract_summary_per_day_value(summary_dataframe, "Pcs/Kg"),
                "note": "PER DAY Pcs divided by PER DAY Kgs",
            },
        ]
    )

    render_section_header(
        "Editable Size_wise_details_summary inputs",
        "You can directly edit Sum of Order Pcs and Sum of Order Kgs. Percentage, Grms/Pc, and Pcs/Kg recalculate automatically.",
    )
    edited_override_dataframe = st.data_editor(
        build_summary_override_editor(summary_dataframe),
        width='stretch',
        hide_index=True,
        num_rows="fixed",
        key="summary_override_editor",
        disabled=["Row Labels"],
        column_config=build_numeric_column_config(SUMMARY_EDITABLE_COLUMNS),
    )

    action_column_1, action_column_2 = st.columns([1, 1])
    with action_column_1:
        if st.button("Apply summary changes"):
            workbook_state["summary_manual_override"] = edited_override_dataframe.copy()
            mark_unsaved_changes()
            set_workbook_state(refresh_calculated_workbook(workbook_state), persist=False)
            st.success("Summary values updated in the live workbook state. Freeze Changes to keep them after refresh.")
            st.rerun()
    with action_column_2:
        if st.button("Reset summary to production data"):
            workbook_state["summary_manual_override"] = None
            mark_unsaved_changes()
            set_workbook_state(refresh_calculated_workbook(workbook_state), persist=False)
            st.success("Summary reset to the live Size_wise_details production data in the app state.")
            st.rerun()

    render_read_only_table(
        "Size_wise_details_summary",
        summary_dataframe,
        height=430,
        note="Summary view with recalculated percentage, Grms/Pc, SAM, and Pcs/Kg.",
        label_column="Row Labels",
    )

    render_section_header(
        "Replace Size_wise_details source sheet",
        "Optional. Upload a workbook only when you want to replace the raw production sheet.",
    )
    replacement_file = st.file_uploader(
        "Upload Size_wise_details workbook",
        type=["xlsx", "xls"],
        key="size_wise_file_uploader",
        label_visibility="collapsed",
    )
    if replacement_file is not None and st.button("Replace Size_wise_details now"):
        is_success, message = replace_size_wise_details_sheet(replacement_file.getvalue())
        if is_success:
            st.success("Size_wise_details replaced in input/WTT.xlsx. Summary and Cut&Sew helper tables refreshed from the new PPC source.")
            st.rerun()
        else:
            st.error(f"Missing required columns: {message}")

    render_read_only_table(
        "Size_wise_details production data",
        size_wise_details,
        height=420,
        note="Raw production sheet currently driving the summary.",
    )


def render_weaving_tab() -> None:
    workbook_state = get_workbook_state()
    wtt_dataframe = workbook_state["sheets"][WTT_SHEET]
    weaving_backup_dataframe = workbook_state["sheets"][WEAVING_BACKUP_SHEET]
    weaving_dataframe = wtt_dataframe[wtt_dataframe["Section"].isin(SECTION_ORDER_WEAVING)].copy()
    selected_designations = _render_designation_filter("weaving_designation_filter", weaving_dataframe)
    filtered_weaving_dataframe = apply_designation_filter(weaving_dataframe, selected_designations)

    render_metric_grid(
        [
            {
                "label": "Visible Sections",
                "value": filtered_weaving_dataframe["Section"].nunique(),
                "note": "Sections after designation filter",
            },
            {
                "label": "Sum of BE_Final_Manpower",
                "value": pd.to_numeric(filtered_weaving_dataframe["BE_Final_Manpower"], errors="coerce").sum(),
                "note": "Live total for visible rows",
            },
        ]
    )
    render_section_summary("Weaving summary", filtered_weaving_dataframe)
    _render_section_collection(SECTION_ORDER_WEAVING, "weaving", filtered_weaving_dataframe)
    render_read_only_table(
        "Weaving Back-Up",
        weaving_backup_dataframe,
        height=360,
        note="Display-only support table. Machine counts are not edited on this screen.",
        label_column="Details" if "Details" in weaving_backup_dataframe.columns else None,
    )


def render_processing_tab() -> None:
    workbook_state = get_workbook_state()
    wtt_dataframe = workbook_state["sheets"][WTT_SHEET]
    processing_dataframe = wtt_dataframe[wtt_dataframe["Section"].isin(SECTION_ORDER_PROCESSING)].copy()
    selected_designations = _render_designation_filter("processing_designation_filter", processing_dataframe)
    filtered_processing_dataframe = apply_designation_filter(processing_dataframe, selected_designations)

    render_metric_grid(
        [
            {
                "label": "Visible Sections",
                "value": filtered_processing_dataframe["Section"].nunique(),
                "note": "Sections after designation filter",
            },
            {
                "label": "Sum of BE_Final_Manpower",
                "value": pd.to_numeric(filtered_processing_dataframe["BE_Final_Manpower"], errors="coerce").sum(),
                "note": "Live total for visible rows",
            },
        ]
    )
    render_section_summary("Processing summary", filtered_processing_dataframe)
    _render_section_collection(SECTION_ORDER_PROCESSING, "processing", filtered_processing_dataframe)

    render_section_header(
        "Stenter dynamic planning",
        "Change the three driver values below to refresh the Stenter shift plan and manpower block.",
    )
    current_stenter_inputs = workbook_state["stenter_inputs"]
    input_column_1, input_column_2, input_column_3 = st.columns(3)
    with input_column_1:
        required_production = st.number_input(
            "Required Production / Day (MT)",
            min_value=0.0,
            value=float(current_stenter_inputs["required_production_mt_per_day"]),
            step=DECIMAL_STEP,
            format=STREAMLIT_NUMBER_FORMAT,
        )
    with input_column_2:
        capacity_per_machine = st.number_input(
            "Capacity / Machine / Shift (MT)",
            min_value=0.0,
            value=float(current_stenter_inputs["capacity_per_machine_per_shift_mt"]),
            step=DECIMAL_STEP,
            format=STREAMLIT_NUMBER_FORMAT,
        )
    with input_column_3:
        available_machines = st.number_input(
            "Available Machines",
            min_value=0.0,
            value=float(current_stenter_inputs["available_machines"]),
            step=DECIMAL_STEP,
            format=STREAMLIT_NUMBER_FORMAT,
        )

    if st.button("Refresh Stenter"):
        workbook_state["stenter_inputs"] = {
            "required_production_mt_per_day": required_production,
            "capacity_per_machine_per_shift_mt": capacity_per_machine,
            "available_machines": available_machines,
        }
        mark_unsaved_changes()
        set_workbook_state(refresh_calculated_workbook(workbook_state), persist=False)
        st.success("Stenter planning refreshed in the live workbook state. Freeze Changes to keep it after refresh.")
        st.rerun()

    render_read_only_table(
        "Stenter shift plan",
        workbook_state["sheets"][STENTER_PLAN_SHEET],
        height=260,
        label_column="Shift",
    )
    render_read_only_table(
        "Stenter manpower",
        workbook_state["sheets"][STENTER_MANPOWER_SHEET],
        height=220,
        label_column="Designation",
    )


def render_cut_sew_tab() -> None:
    workbook_state = get_workbook_state()
    sheets = workbook_state["sheets"]
    cut_sew_dataframe = sheets[WTT_SHEET][
        sheets[WTT_SHEET]["Section"].isin(SECTION_ORDER_CUT_SEW)
    ].copy()
    selected_designations = _render_designation_filter("cut_sew_designation_filter", cut_sew_dataframe)
    filtered_cut_sew_dataframe = apply_designation_filter(cut_sew_dataframe, selected_designations)

    juki_including_cch = float(
        sheets[JUKI_SHEET].loc[
            sheets[JUKI_SHEET]["CCH Metric Label"] == "Including CCH Prod.",
            "CCH Metric Value",
        ].iloc[0]
    )
    render_metric_grid(
        [
            {
                "label": "Per Day Pcs",
                "value": extract_summary_per_day_value(sheets[SIZE_WISE_SUMMARY_SHEET], "Sum of Order Pcs"),
                "note": "Driver from Size_wise_details_summary",
            },
            {
                "label": "Per Day Kgs",
                "value": extract_summary_per_day_value(sheets[SIZE_WISE_SUMMARY_SHEET], "Sum of Order Kgs"),
                "note": "Driver from Size_wise_details_summary",
            },
            {
                "label": "Pcs / Kg",
                "value": extract_summary_per_day_value(sheets[SIZE_WISE_SUMMARY_SHEET], "Pcs/Kg"),
                "note": "Executive productivity indicator",
            },
            {
                "label": "JUKI incl. CCH",
                "value": juki_including_cch,
                "note": "Linked to DTA Stitcher manpower",
            },
        ]
    )
    render_section_summary("Cut&Sew summary", filtered_cut_sew_dataframe)
    _render_section_collection(SECTION_ORDER_CUT_SEW, "cut_sew", filtered_cut_sew_dataframe)

    render_read_only_table(TT_CUT_SEW_LC_SHEET, sheets[TT_CUT_SEW_LC_SHEET], height=360, label_column="Parameters")
    render_read_only_table(TT_CUT_SEW_LH_SHEET, sheets[TT_CUT_SEW_LH_SHEET], height=400, label_column="Parameters")
    render_read_only_table(DTA_SHEET, sheets[DTA_SHEET], height=240)
    render_read_only_table(JUKI_SHEET, sheets[JUKI_SHEET], height=380, label_column="Parameters" if "Parameters" in sheets[JUKI_SHEET].columns else None)


def render_vtt_tab() -> None:
    workbook_state = get_workbook_state()
    wtt_dataframe = workbook_state["sheets"][WTT_SHEET].copy()
    selected_designations = _render_designation_filter("vtt_designation_filter", wtt_dataframe)
    filtered_wtt_dataframe = apply_designation_filter(wtt_dataframe, selected_designations)

    render_metric_grid(
        [
            {
                "label": "Sections",
                "value": filtered_wtt_dataframe["Section"].nunique(),
                "note": "Across the Vapi operating model",
            },
            {
                "label": "Final Manpower",
                "value": pd.to_numeric(filtered_wtt_dataframe["BE_Final_Manpower"], errors="coerce").sum(),
                "note": "Live total from current state",
            },
        ]
    )

    render_read_only_table(
        "Final VTT table",
        filtered_wtt_dataframe,
        height=720,
        note="The full WTT sheet after all live calculations and manual edits.",
        label_column="Section",
    )

    download_map = {"VTT": filtered_wtt_dataframe}
    st.download_button(
        label="Download VTT table",
        data=build_export_bytes(download_map),
        file_name="VTT_final_table.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
