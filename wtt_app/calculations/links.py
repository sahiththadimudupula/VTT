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
    FORMULA_TAG_COLUMN,
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


def _apply_helper_output_to_row(
    wtt_dataframe: pd.DataFrame,
    row_mask: pd.Series,
    final_manpower_value: float,
    formula_tag: str,
) -> None:
    if not row_mask.any():
        return
    shift_a, shift_b, shift_c = split_value_across_shifts(final_manpower_value)
    wtt_dataframe.loc[row_mask, "BE_Final_Manpower"] = round(final_manpower_value, 2)
    wtt_dataframe.loc[row_mask, "General_Shift"] = 0.0
    wtt_dataframe.loc[row_mask, "Shift_A"] = shift_a
    wtt_dataframe.loc[row_mask, "Shift_B"] = shift_b
    wtt_dataframe.loc[row_mask, "Shift_C"] = shift_c
    if FORMULA_TAG_COLUMN in wtt_dataframe.columns:
        wtt_dataframe.loc[row_mask, FORMULA_TAG_COLUMN] = formula_tag


def update_helper_driven_wtt_rows(workbook_state: dict[str, Any]) -> dict[str, Any]:
    sheets = workbook_state["sheets"]
    wtt_dataframe = sheets[WTT_SHEET].copy()

    if FORMULA_TAG_COLUMN not in wtt_dataframe.columns:
        wtt_dataframe[FORMULA_TAG_COLUMN] = ""

    for numeric_column in [
        "BE_Final_Manpower",
        "General_Shift",
        "Shift_A",
        "Shift_B",
        "Shift_C",
        "Reliever",
    ]:
        if numeric_column in wtt_dataframe.columns:
            wtt_dataframe[numeric_column] = pd.to_numeric(wtt_dataframe[numeric_column], errors="coerce").astype(float)

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
        "Weaver": (get_weaving_backup_total(weaving_backup, "Weaver/ Day"), "WEAVING_WEAVER_FROM_BACKUP"),
        "Weaver - Lunch Reliver": (get_weaving_backup_total(weaving_backup, "Relievers/ Day") + 3.0, "WEAVING_RELIEVER_FROM_BACKUP"),
        "Production Fitter": (get_weaving_backup_total(weaving_backup, "Production Fitter"), "WEAVING_PRODUCTION_FITTER_FROM_BACKUP"),
    }

    for designation_name, (final_manpower_value, formula_tag) in weaving_updates.items():
        row_mask = (
            (wtt_dataframe["Section"] == "Loom Shed")
            & (wtt_dataframe["Designation"] == designation_name)
        )
        _apply_helper_output_to_row(wtt_dataframe, row_mask, final_manpower_value, formula_tag)

    cut_sew_updates = {
        "Length Cutting Operator": ((lc_total_machines + 1.0) * 3.0, "CUTSEW_LC_FROM_LC_TOTAL_MACHINES"),
        "L, C,Material Transport": ((lc_total_machines + 1.0) * 3.0, "CUTSEW_LC_FROM_LC_TOTAL_MACHINES"),
        "Length Hemming Operator": ((lh_total_machines + 1.0) * 3.0, "CUTSEW_LH_FROM_LH_TOTAL_MACHINES"),
        "Cross Cutting Operator": ((lh_total_machines + 1.0) * 3.0, "CUTSEW_LH_FROM_LH_TOTAL_MACHINES"),
        "DTA Jobber": (float(dta_scaled_row["Sew-Jobber"] + dta_scaled_row["Pkg Jobber"]), "CUTSEW_DTA_FROM_DTA_SCALED_TOTALS"),
        "Line F./Trim B/ AQL/ Segr": (
            float(dta_scaled_row["Line Feed"] + dta_scaled_row["AQL"] + dta_scaled_row["Trim Boy"]),
            "CUTSEW_DTA_FROM_DTA_SCALED_TOTALS",
        ),
        "DTA Stitcher": (juki_including_cch, "CUTSEW_JUKI_FROM_INCLUDING_CCH"),
        "Cartons Packers": (
            round(extract_summary_per_day_value(summary_dataframe, "Sum of Order Kgs") * 112.0 / DTA_REFERENCE_VALUE, 0),
            "CUTSEW_CARTONS_FROM_SUMMARY_PER_DAY_KGS",
        ),
    }

    for designation_name, (final_manpower_value, formula_tag) in cut_sew_updates.items():
        row_mask = (
            (wtt_dataframe["Section"] == "TT_Cut&Sew")
            & (wtt_dataframe["Designation"] == designation_name)
        )
        _apply_helper_output_to_row(wtt_dataframe, row_mask, final_manpower_value, formula_tag)

    polybag_mask = (
        (wtt_dataframe["Section"] == "TT_Cut&Sew")
        & (wtt_dataframe["Designation"] == "DTA Polybag Packer (Table)")
    )
    _apply_helper_output_to_row(wtt_dataframe, polybag_mask, round(juki_including_cch * 0.9, 2), "CUTSEW_JUKI_FROM_INCLUDING_CCH")

    tqm_mask = (
        (wtt_dataframe["Section"] == "TT_Cut&Sew")
        & (wtt_dataframe["Designation"] == "TT TQM")
    )
    _apply_helper_output_to_row(wtt_dataframe, tqm_mask, round((juki_including_cch * 0.75) + 48.0, 2), "CUTSEW_JUKI_FROM_INCLUDING_CCH")

    stenter_manpower_dataframe = sheets[STENTER_MANPOWER_SHEET]
    stenter_applied_dataframe = apply_stenter_to_wtt(wtt_dataframe, stenter_manpower_dataframe)
    if FORMULA_TAG_COLUMN in stenter_applied_dataframe.columns:
        stenter_row_mask = (
            (stenter_applied_dataframe["Section"] == "Drying")
            & (stenter_applied_dataframe["Dept_Machine_Name"] == "Stenter")
            & (stenter_applied_dataframe["Designation"].isin(["Padder Operator", "Biancalanni", "Stenter Operator"]))
        )
        stenter_applied_dataframe.loc[stenter_row_mask, FORMULA_TAG_COLUMN] = "STENTER_FROM_STENTER_PLAN"

    sheets[WTT_SHEET] = stenter_applied_dataframe
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
