
from __future__ import annotations

from typing import Any

import pandas as pd

from wtt_app.calculations.helpers import (
    build_dta,
    build_juki,
    build_stenter_outputs,
    build_tt_cut_sew_lc,
    build_tt_cut_sew_lh,
    get_weaving_backup_total,
)
from wtt_app.calculations.stenter import apply_stenter_to_wtt
from wtt_app.calculations.summary import build_size_summary, extract_summary_per_day_value
from wtt_app.config import (
    DTA_REFERENCE_VALUE,
    DTA_SHEET,
    JUKI_SHEET,
    LC_CATEGORY_SETTINGS,
    SIZE_WISE_DETAILS_SHEET,
    SIZE_WISE_SUMMARY_SHEET,
    STENTER_MANPOWER_SHEET,
    STENTER_PLAN_SHEET,
    TT_CUT_SEW_LC_SHEET,
    TT_CUT_SEW_LH_SHEET,
    WEAVING_BACKUP_SHEET,
    WTT_SHEET,
)
from wtt_app.core.formatters import split_value_across_shifts


def update_helper_driven_wtt_rows(workbook_state: dict[str, Any]) -> dict[str, Any]:
    sheets = workbook_state["sheets"]
    wtt_dataframe = sheets[WTT_SHEET].copy()

    for numeric_column in [
        "BE_Final_Manpower",
        "General_Shift",
        "Shift_A",
        "Shift_B",
        "Shift_C",
    ]:
        if numeric_column in wtt_dataframe.columns:
            wtt_dataframe[numeric_column] = pd.to_numeric(
                wtt_dataframe[numeric_column],
                errors="coerce",
            ).astype(float)

    weaving_backup = sheets[WEAVING_BACKUP_SHEET]
    summary_dataframe = sheets[SIZE_WISE_SUMMARY_SHEET]
    lc_dataframe = sheets[TT_CUT_SEW_LC_SHEET]
    lh_dataframe = sheets[TT_CUT_SEW_LH_SHEET]
    dta_dataframe = sheets[DTA_SHEET]
    juki_dataframe = sheets[JUKI_SHEET]

    lc_total_machines = float(lc_dataframe.iloc[-1][list(LC_CATEGORY_SETTINGS.keys())[-1]])
    lh_total_machines = float(lh_dataframe.iloc[-1][list(lh_dataframe.columns)[-1]])
    dta_scaled_row = dta_dataframe.iloc[-1]
    juki_including_cch = float(
        juki_dataframe.loc[
            juki_dataframe["CCH Metric Label"] == "Including CCH Prod.",
            "CCH Metric Value",
        ].iloc[0]
    )

    weaving_updates = {
        "Weaver": get_weaving_backup_total(weaving_backup, "Weaver/ Day"),
        "Weaver - Lunch Reliver": get_weaving_backup_total(weaving_backup, "Relievers/ Day") + 3.0,
        "Production Fitter": get_weaving_backup_total(weaving_backup, "Production Fitter"),
    }

    for designation_name, final_manpower_value in weaving_updates.items():
        row_mask = (
            (wtt_dataframe["Section"] == "Loom Shed")
            & (wtt_dataframe["Designation"] == designation_name)
        )
        if not row_mask.any():
            continue
        shift_a, shift_b, shift_c = split_value_across_shifts(final_manpower_value)
        wtt_dataframe.loc[row_mask, "BE_Final_Manpower"] = round(final_manpower_value, 2)
        wtt_dataframe.loc[row_mask, "General_Shift"] = 0.0
        wtt_dataframe.loc[row_mask, "Shift_A"] = shift_a
        wtt_dataframe.loc[row_mask, "Shift_B"] = shift_b
        wtt_dataframe.loc[row_mask, "Shift_C"] = shift_c

    cut_sew_updates = {
        "Length Cutting Operator": (lc_total_machines + 1.0) * 3.0,
        "L, C,Material Transport": (lc_total_machines + 1.0) * 3.0,
        "Length Hemming Operator": (lh_total_machines + 1.0) * 3.0,
        "Cross Cutting Operator": (lh_total_machines + 1.0) * 3.0,
        "DTA Jobber": float(dta_scaled_row["Sew-Jobber"] + dta_scaled_row["Pkg Jobber"]),
        "Line F./Trim B/ AQL/ Segr": float(
            dta_scaled_row["Line Feed"] + dta_scaled_row["AQL"] + dta_scaled_row["Trim Boy"]
        ),
        "DTA Stitcher": juki_including_cch,
        "Cartons Packers": round(
            extract_summary_per_day_value(summary_dataframe, "Sum of Order Kgs") * 112.0 / DTA_REFERENCE_VALUE,
            0,
        ),
    }

    for designation_name, final_manpower_value in cut_sew_updates.items():
        row_mask = (
            (wtt_dataframe["Section"] == "TT_Cut&Sew")
            & (wtt_dataframe["Designation"] == designation_name)
        )
        if not row_mask.any():
            continue
        shift_a, shift_b, shift_c = split_value_across_shifts(final_manpower_value)
        wtt_dataframe.loc[row_mask, "BE_Final_Manpower"] = round(final_manpower_value, 2)
        wtt_dataframe.loc[row_mask, "General_Shift"] = 0.0
        wtt_dataframe.loc[row_mask, "Shift_A"] = shift_a
        wtt_dataframe.loc[row_mask, "Shift_B"] = shift_b
        wtt_dataframe.loc[row_mask, "Shift_C"] = shift_c

    polybag_mask = (
        (wtt_dataframe["Section"] == "TT_Cut&Sew")
        & (wtt_dataframe["Designation"] == "DTA Polybag Packer (Table)")
    )
    if polybag_mask.any():
        polybag_value = round(juki_including_cch * 0.9, 2)
        shift_a, shift_b, shift_c = split_value_across_shifts(polybag_value)
        wtt_dataframe.loc[polybag_mask, "BE_Final_Manpower"] = polybag_value
        wtt_dataframe.loc[polybag_mask, "General_Shift"] = 0.0
        wtt_dataframe.loc[polybag_mask, "Shift_A"] = shift_a
        wtt_dataframe.loc[polybag_mask, "Shift_B"] = shift_b
        wtt_dataframe.loc[polybag_mask, "Shift_C"] = shift_c

    tqm_mask = (
        (wtt_dataframe["Section"] == "TT_Cut&Sew")
        & (wtt_dataframe["Designation"] == "TT TQM")
    )
    if tqm_mask.any():
        tqm_value = round((juki_including_cch * 0.75) + 48.0, 2)
        shift_a, shift_b, shift_c = split_value_across_shifts(tqm_value)
        wtt_dataframe.loc[tqm_mask, "BE_Final_Manpower"] = tqm_value
        wtt_dataframe.loc[tqm_mask, "General_Shift"] = 0.0
        wtt_dataframe.loc[tqm_mask, "Shift_A"] = shift_a
        wtt_dataframe.loc[tqm_mask, "Shift_B"] = shift_b
        wtt_dataframe.loc[tqm_mask, "Shift_C"] = shift_c

    stenter_manpower_dataframe = sheets[STENTER_MANPOWER_SHEET]
    wtt_dataframe = apply_stenter_to_wtt(wtt_dataframe, stenter_manpower_dataframe)

    sheets[WTT_SHEET] = wtt_dataframe
    workbook_state["sheets"] = sheets
    return workbook_state


def refresh_calculated_workbook(workbook_state: dict[str, Any]) -> dict[str, Any]:
    sheets = workbook_state["sheets"]
    size_wise_details = sheets[SIZE_WISE_DETAILS_SHEET].copy()
    summary_dataframe = build_size_summary(
        size_wise_details,
        workbook_state.get("summary_manual_override"),
    )
    sheets[SIZE_WISE_SUMMARY_SHEET] = summary_dataframe
    sheets[TT_CUT_SEW_LC_SHEET] = build_tt_cut_sew_lc(summary_dataframe)
    sheets[TT_CUT_SEW_LH_SHEET] = build_tt_cut_sew_lh(summary_dataframe)
    sheets[DTA_SHEET] = build_dta(summary_dataframe)
    sheets[JUKI_SHEET] = build_juki(summary_dataframe)

    stenter_plan, stenter_manpower = build_stenter_outputs(workbook_state["stenter_inputs"])
    sheets[STENTER_PLAN_SHEET] = stenter_plan
    sheets[STENTER_MANPOWER_SHEET] = stenter_manpower

    workbook_state["sheets"] = sheets
    return update_helper_driven_wtt_rows(workbook_state)
