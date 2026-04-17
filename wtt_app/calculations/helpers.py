from __future__ import annotations

from typing import Any

import pandas as pd

from wtt_app.calculations.summary import extract_summary_category_value, extract_summary_per_day_value
from wtt_app.config import (
    DTA_LINE_SETTINGS,
    DTA_REFERENCE_VALUE,
    JUKI_AVAILABLE_MINUTES_PER_SHIFT,
    JUKI_CATEGORY_SETTINGS,
    JUKI_CCH_AVAIL_SECONDS_PER_MACHINE,
    JUKI_CCH_MACHINE_PLANNED,
    JUKI_CCH_TOTAL_PRODUCTION,
    JUKI_EFFICIENCY,
    JUKI_HAND_CCH_FACTOR,
    JUKI_MACHINE_WIDTH,
    JUKI_STITCHERS_PER_MACHINE,
    JUKI_TQM_CHECKER_FACTOR,
    JUKI_WASH_CCH_FACTOR,
    LC_AVAILABLE_HOURS_PER_DAY,
    LC_CATEGORY_SETTINGS,
    LC_EFFICIENCY,
    LC_MACHINE_WIDTH,
    LC_ROUNDING_BUFFER,
    LC_SPEED_MPM,
    LH_AVAILABLE_HOURS_PER_DAY,
    LH_CATEGORY_SETTINGS,
    LH_EFFICIENCY,
    LH_HEMMING_SPEED_MPM,
    LH_MACHINE_WIDTH,
    LH_ROUNDING_BUFFER,
    LH_SAMPLE_AND_MAINTENANCE,
    LH_SPEED_MPM,
)
from wtt_app.core.math_utils import excel_round
from wtt_app.calculations.stenter import build_stenter_tables, read_stenter_inputs_from_raw


def parse_stenter_inputs(stenter_sheet: pd.DataFrame) -> dict[str, float]:
    return read_stenter_inputs_from_raw(stenter_sheet)


def _build_ratio_value(summary_dataframe: pd.DataFrame, summary_label: str | None) -> float:
    if not summary_label:
        return 0.0
    return extract_summary_category_value(summary_dataframe, summary_label, "percentage")


def _build_qty_value(ratio_value: float, per_day_order_pcs: float) -> float:
    return ratio_value * per_day_order_pcs / 100.0


def _build_size_split_value(machine_width: float, towel_width: float) -> float:
    if not towel_width:
        return 0.0
    return excel_round((machine_width / towel_width) - 0.5, 0)


def calculate_cutting_helper_rows(
    summary_dataframe: pd.DataFrame,
    category_settings: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    per_day_order_pcs = extract_summary_per_day_value(summary_dataframe, "Sum of Order Pcs")

    helper_rows: list[dict[str, Any]] = []
    ratio_row = {"Sr. No": 1.0, "Parameters": "Ratio"}
    length_row = {"Sr. No": 2.0, "Parameters": "Size Per Towel (In Mtrs)_Length in cm"}
    width_row = {"Sr. No": 3.0, "Parameters": "Size Per Towel (In Mtrs)_Width in cm"}
    machine_width_row = {"Sr. No": 4.0, "Parameters": "Machine Width"}
    qty_row = {"Sr. No": 5.0, "Parameters": "Qty (In Pcs)"}
    size_splits_row = {"Sr. No": 6.0, "Parameters": "Size -wise Splits"}
    pcs_per_meter_row = {"Sr. No": 7.0, "Parameters": "Pcs/mtr"}
    total_pieces_width_row = {"Sr. No": 8.0, "Parameters": "Total Pieces/ Width"}
    speed_row = {"Sr. No": 9.0, "Parameters": "Speed mpm"}
    pcs_per_minute_row = {"Sr. No": 10.0, "Parameters": "Pcs/min"}
    efficiency_row = {"Sr. No": 11.0, "Parameters": "Eff"}
    pcs_per_minute_efficiency_row = {"Sr. No": 12.0, "Parameters": "Pcs/min at given eff"}
    available_time_row = {"Sr. No": 13.0, "Parameters": "Available time"}
    production_per_machine_row = {"Sr. No": 14.0, "Parameters": "Production/m/c"}
    machines_required_row = {"Sr. No": 15.0, "Parameters": "No of machines required"}
    total_machines_row = {"Sr. No": 16.0, "Parameters": "Total no of machines reqd"}
    rounded_row = {"Sr. No": None, "Parameters": "ROUND"}

    total_machine_requirement = 0.0

    for column_name, settings in category_settings.items():
        ratio_value = _build_ratio_value(summary_dataframe, settings["summary_label"])
        length_value = float(settings["length_cm"])
        width_value = float(settings["width_cm"])
        qty_value = _build_qty_value(ratio_value, per_day_order_pcs)
        size_splits_value = _build_size_split_value(LC_MACHINE_WIDTH, width_value)
        pcs_per_meter_value = 100.0 / length_value if length_value else 0.0
        total_pieces_width_value = size_splits_value * pcs_per_meter_value
        pcs_per_minute_value = LC_SPEED_MPM * total_pieces_width_value
        pcs_per_minute_efficiency_value = pcs_per_minute_value * LC_EFFICIENCY
        production_per_machine_value = LC_AVAILABLE_HOURS_PER_DAY * 60.0 * pcs_per_minute_efficiency_value
        machines_required_value = qty_value / production_per_machine_value if production_per_machine_value else 0.0
        total_machine_requirement += machines_required_value

        ratio_row[column_name] = ratio_value
        length_row[column_name] = length_value
        width_row[column_name] = width_value
        machine_width_row[column_name] = LC_MACHINE_WIDTH
        qty_row[column_name] = qty_value
        size_splits_row[column_name] = size_splits_value
        pcs_per_meter_row[column_name] = pcs_per_meter_value
        total_pieces_width_row[column_name] = total_pieces_width_value
        speed_row[column_name] = LC_SPEED_MPM
        pcs_per_minute_row[column_name] = pcs_per_minute_value
        efficiency_row[column_name] = LC_EFFICIENCY
        pcs_per_minute_efficiency_row[column_name] = pcs_per_minute_efficiency_value
        available_time_row[column_name] = LC_AVAILABLE_HOURS_PER_DAY
        production_per_machine_row[column_name] = production_per_machine_value
        machines_required_row[column_name] = machines_required_value

    last_column_name = list(category_settings.keys())[-1]
    total_machines_row[last_column_name] = total_machine_requirement
    rounded_row[last_column_name] = excel_round(total_machine_requirement + LC_ROUNDING_BUFFER, 0)

    helper_rows.extend([
        ratio_row,
        length_row,
        width_row,
        machine_width_row,
        qty_row,
        size_splits_row,
        pcs_per_meter_row,
        total_pieces_width_row,
        speed_row,
        pcs_per_minute_row,
        efficiency_row,
        pcs_per_minute_efficiency_row,
        available_time_row,
        production_per_machine_row,
        machines_required_row,
        total_machines_row,
        rounded_row,
    ])
    return pd.DataFrame(helper_rows)


def build_tt_cut_sew_lc(summary_dataframe: pd.DataFrame) -> pd.DataFrame:
    return calculate_cutting_helper_rows(summary_dataframe, LC_CATEGORY_SETTINGS)


def build_tt_cut_sew_lh(summary_dataframe: pd.DataFrame) -> pd.DataFrame:
    per_day_order_pcs = extract_summary_per_day_value(summary_dataframe, "Sum of Order Pcs")
    helper_rows: list[dict[str, Any]] = []

    ratio_row = {"Sr. No": 1.0, "Parameters": "Ratio"}
    length_row = {"Sr. No": 2.0, "Parameters": "Size Per Towel (In Mtrs)_Length in cm"}
    width_row = {"Sr. No": 3.0, "Parameters": "Size Per Towel (In Mtrs)_Width in cm"}
    machine_width_row = {"Sr. No": 4.0, "Parameters": "Machine Width"}
    qty_row = {"Sr. No": 5.0, "Parameters": "Qty (In Pcs)"}
    size_splits_row = {"Sr. No": 6.0, "Parameters": "Size -wise Splits"}
    pcs_per_meter_row = {"Sr. No": 7.0, "Parameters": "Pcs/mtr"}
    total_pieces_width_row = {"Sr. No": 8.0, "Parameters": "Total Pieces/ Width"}
    speed_row = {"Sr. No": 9.0, "Parameters": "Speed mpm"}
    hemming_speed_row = {"Sr. No": None, "Parameters": "Speed mpm"}
    pieces_per_minute_row = {"Sr. No": None, "Parameters": "Pieces / min"}
    efficiency_row = {"Sr. No": None, "Parameters": "Eff  %"}
    pieces_per_minute_efficiency_row = {"Sr. No": None, "Parameters": "Pcs/min at given eff"}
    available_time_row = {"Sr. No": None, "Parameters": "Available time hrs/ day"}
    production_per_machine_row = {"Sr. No": None, "Parameters": "Production/m/c/ day in pcs"}
    machines_required_row = {"Sr. No": None, "Parameters": "No of machines required"}
    total_machines_row = {"Sr. No": None, "Parameters": "Total No. Of Machines Reqd"}
    sample_row = {"Sr. No": None, "Parameters": "Sample & Maint"}
    final_machine_row = {"Sr. No": None, "Parameters": "No. of M/C"}

    total_machine_requirement = 0.0

    for column_name, settings in LH_CATEGORY_SETTINGS.items():
        ratio_value = _build_ratio_value(summary_dataframe, settings["summary_label"])
        length_value = float(settings["length_cm"])
        width_value = float(settings["width_cm"])
        qty_value = _build_qty_value(ratio_value, per_day_order_pcs)
        size_splits_value = _build_size_split_value(LH_MACHINE_WIDTH, width_value)
        pcs_per_meter_value = 100.0 / length_value if length_value else 0.0
        total_pieces_width_value = size_splits_value * pcs_per_meter_value
        pieces_per_minute_value = LH_HEMMING_SPEED_MPM * pcs_per_meter_value
        pieces_per_minute_efficiency_value = pieces_per_minute_value * LH_EFFICIENCY
        production_per_machine_value = LH_AVAILABLE_HOURS_PER_DAY * 60.0 * pieces_per_minute_efficiency_value
        machines_required_value = qty_value / production_per_machine_value if production_per_machine_value else 0.0
        total_machine_requirement += machines_required_value

        ratio_row[column_name] = ratio_value
        length_row[column_name] = length_value
        width_row[column_name] = width_value
        machine_width_row[column_name] = LH_MACHINE_WIDTH
        qty_row[column_name] = qty_value
        size_splits_row[column_name] = size_splits_value
        pcs_per_meter_row[column_name] = pcs_per_meter_value
        total_pieces_width_row[column_name] = total_pieces_width_value
        speed_row[column_name] = LH_SPEED_MPM
        hemming_speed_row[column_name] = LH_HEMMING_SPEED_MPM
        pieces_per_minute_row[column_name] = pieces_per_minute_value
        efficiency_row[column_name] = LH_EFFICIENCY
        pieces_per_minute_efficiency_row[column_name] = pieces_per_minute_efficiency_value
        available_time_row[column_name] = LH_AVAILABLE_HOURS_PER_DAY
        production_per_machine_row[column_name] = production_per_machine_value
        machines_required_row[column_name] = machines_required_value

    last_column_name = list(LH_CATEGORY_SETTINGS.keys())[-1]
    total_machines_row[last_column_name] = total_machine_requirement
    sample_row[last_column_name] = LH_SAMPLE_AND_MAINTENANCE
    final_machine_row[last_column_name] = excel_round(
        total_machine_requirement + LH_SAMPLE_AND_MAINTENANCE + LH_ROUNDING_BUFFER,
        0,
    )

    helper_rows.extend([
        ratio_row,
        length_row,
        width_row,
        machine_width_row,
        qty_row,
        size_splits_row,
        pcs_per_meter_row,
        total_pieces_width_row,
        speed_row,
        hemming_speed_row,
        pieces_per_minute_row,
        efficiency_row,
        pieces_per_minute_efficiency_row,
        available_time_row,
        production_per_machine_row,
        machines_required_row,
        total_machines_row,
        sample_row,
        final_machine_row,
    ])
    return pd.DataFrame(helper_rows)


def build_dta(summary_dataframe: pd.DataFrame) -> pd.DataFrame:
    per_day_order_kgs = extract_summary_per_day_value(summary_dataframe, "Sum of Order Kgs")
    dta_rows: list[dict[str, Any]] = []

    for setting in DTA_LINE_SETTINGS:
        line_count = float(setting["lines"])
        dta_rows.append(
            {
                "Section": setting["label"],
                "Lines": line_count,
                "Sew-Jobber": setting["sew_jobber_factor"] * line_count * 3.0,
                "Pkg Jobber": setting["pkg_jobber_factor"] * line_count * 3.0,
                "Line Feed": setting["line_feed_factor"] * line_count * 3.0,
                "AQL": setting["aql_factor"] * line_count * 3.0,
                "Trim Boy": setting["trim_boy_factor"] * line_count * 3.0,
                "values": per_day_order_kgs
                if setting["label"] == "DTA (1-6)"
                else (DTA_REFERENCE_VALUE if setting["label"] == "DTA (7&8)" else None),
            }
        )

    detail_dataframe = pd.DataFrame(dta_rows)
    total_row = {
        "Section": "Total",
        "Lines": detail_dataframe["Lines"].sum(),
        "Sew-Jobber": detail_dataframe["Sew-Jobber"].sum(),
        "Pkg Jobber": detail_dataframe["Pkg Jobber"].sum(),
        "Line Feed": detail_dataframe["Line Feed"].sum(),
        "AQL": detail_dataframe["AQL"].sum(),
        "Trim Boy": detail_dataframe["Trim Boy"].sum(),
        "values": None,
    }
    scaled_row = {
        "Section": "",
        "Lines": None,
        "Sew-Jobber": per_day_order_kgs * total_row["Sew-Jobber"] / DTA_REFERENCE_VALUE,
        "Pkg Jobber": per_day_order_kgs * total_row["Pkg Jobber"] / DTA_REFERENCE_VALUE,
        "Line Feed": per_day_order_kgs * total_row["Line Feed"] / DTA_REFERENCE_VALUE,
        "AQL": per_day_order_kgs * total_row["AQL"] / DTA_REFERENCE_VALUE,
        "Trim Boy": per_day_order_kgs * total_row["Trim Boy"] / DTA_REFERENCE_VALUE,
        "values": None,
    }
    return pd.concat([detail_dataframe, pd.DataFrame([total_row, scaled_row])], ignore_index=True)


def build_juki(summary_dataframe: pd.DataFrame) -> pd.DataFrame:
    per_day_order_pcs = extract_summary_per_day_value(summary_dataframe, "Sum of Order Pcs")

    juki_rows: list[dict[str, Any]] = []
    ratio_row = {"Sr. No": 1.0, "Parameters": "Ratio"}
    length_row = {"Sr. No": 2.0, "Parameters": "Size Per Towel (In Mtrs)_Length in cm"}
    width_row = {"Sr. No": 3.0, "Parameters": "Size Per Towel (In Mtrs)_Width in cm"}
    machine_width_row = {"Sr. No": 4.0, "Parameters": "Machine Width"}
    qty_row = {"Sr. No": 5.0, "Parameters": "Qty (In Pcs)"}
    required_production_row = {"Sr. No": 6.0, "Parameters": "Reqd. Production"}
    sam_row = {"Sr. No": 7.0, "Parameters": "JUKI SAM"}
    available_minutes_row = {"Sr. No": 8.0, "Parameters": "Avail. Min/ Shift/ mc"}
    efficiency_row = {"Sr. No": 9.0, "Parameters": "Eff %"}
    machines_required_row = {"Sr. No": 10.0, "Parameters": "No. of mc reqd."}
    stitchers_required_row = {"Sr. No": 11.0, "Parameters": "No. of Stitcher Reqd/ day"}
    tqm_checker_row = {"Sr. No": 12.0, "Parameters": "TQM Checker"}
    total_stitchers_row = {"Sr. No": None, "Parameters": "TOTAL STITCHERS REQD."}

    hand_qty = 0.0
    wash_qty = 0.0

    for column_name, settings in JUKI_CATEGORY_SETTINGS.items():
        ratio_value = _build_ratio_value(summary_dataframe, settings["summary_label"])
        qty_value = _build_qty_value(ratio_value, per_day_order_pcs)
        if column_name == "JUKI_Hand":
            hand_qty = qty_value
        if column_name == "JUKI_Wash":
            wash_qty = qty_value

        ratio_row[column_name] = ratio_value
        length_row[column_name] = float(settings["length_cm"])
        width_row[column_name] = float(settings["width_cm"])
        machine_width_row[column_name] = JUKI_MACHINE_WIDTH
        qty_row[column_name] = qty_value

    hand_and_wash_total_qty = hand_qty + wash_qty
    hand_share_percentage = (hand_qty / hand_and_wash_total_qty * 100.0) if hand_and_wash_total_qty else 0.0
    wash_share_percentage = (wash_qty / hand_and_wash_total_qty * 100.0) if hand_and_wash_total_qty else 0.0

    hand_sam = extract_summary_category_value(summary_dataframe, "Hand", "SAM")
    wash_sam = extract_summary_category_value(summary_dataframe, "Wash", "SAM")
    product_average_sam = (
        ((hand_sam * JUKI_HAND_CCH_FACTOR * hand_qty) + (wash_sam * JUKI_WASH_CCH_FACTOR * wash_qty))
        / hand_and_wash_total_qty
        if hand_and_wash_total_qty
        else 0.0
    )
    total_seconds_for_cch = JUKI_CCH_TOTAL_PRODUCTION * product_average_sam
    cch_vs_juki_difference = (
        total_seconds_for_cch / JUKI_CCH_AVAIL_SECONDS_PER_MACHINE
        if JUKI_CCH_AVAIL_SECONDS_PER_MACHINE
        else 0.0
    )

    total_stitchers_required = 0.0
    for column_name, settings in JUKI_CATEGORY_SETTINGS.items():
        summary_label = settings["summary_label"]
        qty_value = qty_row[column_name]
        if column_name == "JUKI_Hand":
            required_qty = qty_value - (JUKI_CCH_TOTAL_PRODUCTION * hand_share_percentage / 100.0)
        elif column_name == "JUKI_Wash":
            required_qty = qty_value - (JUKI_CCH_TOTAL_PRODUCTION * wash_share_percentage / 100.0)
        else:
            required_qty = qty_value

        sam_value = (
            extract_summary_category_value(summary_dataframe, summary_label, "SAM")
            if summary_label
            else 0.0
        )
        machine_requirement = (
            required_qty * sam_value
            / (JUKI_AVAILABLE_MINUTES_PER_SHIFT * JUKI_EFFICIENCY * 60.0 * JUKI_STITCHERS_PER_MACHINE)
            if JUKI_AVAILABLE_MINUTES_PER_SHIFT
            else 0.0
        )
        stitchers_required = machine_requirement * JUKI_STITCHERS_PER_MACHINE
        total_stitchers_required += stitchers_required

        required_production_row[column_name] = required_qty
        sam_row[column_name] = sam_value
        available_minutes_row[column_name] = JUKI_AVAILABLE_MINUTES_PER_SHIFT
        efficiency_row[column_name] = JUKI_EFFICIENCY
        machines_required_row[column_name] = machine_requirement
        stitchers_required_row[column_name] = stitchers_required
        tqm_checker_row[column_name] = stitchers_required * JUKI_TQM_CHECKER_FACTOR

    total_stitchers_row[list(JUKI_CATEGORY_SETTINGS.keys())[-1]] = total_stitchers_required

    juki_dataframe = pd.DataFrame([
        ratio_row,
        length_row,
        width_row,
        machine_width_row,
        qty_row,
        required_production_row,
        sam_row,
        available_minutes_row,
        efficiency_row,
        machines_required_row,
        stitchers_required_row,
        tqm_checker_row,
        total_stitchers_row,
    ])
    juki_dataframe["Hand"] = [hand_qty, hand_share_percentage] + [None] * 11
    juki_dataframe["Wash"] = [wash_qty, wash_share_percentage] + [None] * 11
    juki_dataframe["Total Qty"] = [hand_and_wash_total_qty] + [None] * 12
    juki_dataframe["CCH Metric Label"] = [
        "No. of machines Planned",
        "Total Production Planned on CCH",
        "Product Avg. SAM",
        "Total Sec (for 61776 Pcs)",
        "Avail. Sec per mc",
        "Diff of CCH vs Juki.",
        "Excluding CCH Prod.",
        "Including CCH Prod.",
        None, None, None, None, None,
    ]
    juki_dataframe["CCH Metric Value"] = [
        JUKI_CCH_MACHINE_PLANNED,
        JUKI_CCH_TOTAL_PRODUCTION,
        product_average_sam,
        total_seconds_for_cch,
        JUKI_CCH_AVAIL_SECONDS_PER_MACHINE,
        cch_vs_juki_difference,
        total_stitchers_required,
        total_stitchers_required + cch_vs_juki_difference,
        None, None, None, None, None,
    ]
    return juki_dataframe


def build_stenter_outputs(stenter_inputs: dict[str, float]) -> tuple[pd.DataFrame, pd.DataFrame]:
    return build_stenter_tables(
        required_production_mt_per_day=float(stenter_inputs["required_production_mt_per_day"]),
        capacity_per_machine_per_shift_mt=float(stenter_inputs["capacity_per_machine_per_shift_mt"]),
        available_machines=float(stenter_inputs["available_machines"]),
    )


def get_weaving_backup_total(weaving_backup_dataframe: pd.DataFrame, detail_label: str) -> float:
    detail_column_name = weaving_backup_dataframe.columns[0]
    total_column_name = weaving_backup_dataframe.columns[-1]
    matching_rows = weaving_backup_dataframe[
        weaving_backup_dataframe[detail_column_name].astype(str).str.strip().str.lower()
        == detail_label.strip().lower()
    ]
    if matching_rows.empty:
        return 0.0
    return float(matching_rows.iloc[0][total_column_name])
