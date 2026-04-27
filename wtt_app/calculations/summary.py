
from __future__ import annotations

from typing import Any

import pandas as pd

from wtt_app.config import (
    DEFAULT_DAYS,
    PREDICTION_DIVISOR,
    SIZE_CATEGORY_ORDER,
    SIZE_CATEGORY_TO_SAM,
    SUMMARY_EDITABLE_COLUMNS,
)


def build_base_size_summary(size_wise_details: pd.DataFrame) -> pd.DataFrame:
    grouped_dataframe = (
        size_wise_details.groupby("Size2", dropna=False)[["Order Pcs", "Order Kgs"]]
        .sum()
        .rename(columns={"Order Pcs": "Sum of Order Pcs", "Order Kgs": "Sum of Order Kgs"})
    )

    summary_rows: list[dict[str, Any]] = []
    for category_name in SIZE_CATEGORY_ORDER:
        category_order_pcs = (
            float(grouped_dataframe.loc[category_name, "Sum of Order Pcs"])
            if category_name in grouped_dataframe.index
            else 0.0
        )
        category_order_kgs = (
            float(grouped_dataframe.loc[category_name, "Sum of Order Kgs"])
            if category_name in grouped_dataframe.index
            else 0.0
        )
        summary_rows.append(
            {
                "Row Labels": category_name,
                "Sum of Order Pcs": category_order_pcs / PREDICTION_DIVISOR,
                "Sum of Order Kgs": category_order_kgs / PREDICTION_DIVISOR,
            }
        )

    return pd.DataFrame(summary_rows)


def apply_manual_summary_override(
    base_summary: pd.DataFrame,
    manual_override: pd.DataFrame | None,
) -> pd.DataFrame:
    if manual_override is None or manual_override.empty:
        return base_summary.copy()

    merged_dataframe = base_summary.copy().set_index("Row Labels")
    manual_override_indexed = manual_override.copy().set_index("Row Labels")

    for row_label in merged_dataframe.index:
        if row_label not in manual_override_indexed.index:
            continue
        for column_name in SUMMARY_EDITABLE_COLUMNS:
            manual_value = manual_override_indexed.at[row_label, column_name]
            if pd.notna(manual_value):
                merged_dataframe.at[row_label, column_name] = float(manual_value)

    return merged_dataframe.reset_index()




def build_summary_manual_override_from_sheet(summary_sheet_dataframe: pd.DataFrame) -> pd.DataFrame | None:
    if summary_sheet_dataframe is None or summary_sheet_dataframe.empty:
        return None

    normalized_dataframe = summary_sheet_dataframe.copy()
    if "Row Labels" not in normalized_dataframe.columns:
        return None

    detail_rows = normalized_dataframe[normalized_dataframe["Row Labels"].isin(SIZE_CATEGORY_ORDER)].copy()
    if detail_rows.empty:
        return None

    available_columns = [
        column_name
        for column_name in ["Row Labels", *SUMMARY_EDITABLE_COLUMNS]
        if column_name in detail_rows.columns
    ]
    if len(available_columns) <= 1:
        return None

    detail_rows = detail_rows[available_columns].copy()
    for column_name in SUMMARY_EDITABLE_COLUMNS:
        if column_name in detail_rows.columns:
            detail_rows[column_name] = pd.to_numeric(detail_rows[column_name], errors="coerce")
    return detail_rows.reset_index(drop=True)

def add_derived_summary_rows(summary_detail_rows: pd.DataFrame) -> pd.DataFrame:
    summary_dataframe = summary_detail_rows.copy()
    total_order_pcs = float(summary_dataframe["Sum of Order Pcs"].sum())
    total_order_kgs = float(summary_dataframe["Sum of Order Kgs"].sum())

    summary_dataframe["percentage"] = summary_dataframe["Sum of Order Pcs"].apply(
        lambda value: (float(value) / total_order_pcs * 100.0) if total_order_pcs else 0.0
    )
    summary_dataframe["Grms/Pc"] = summary_dataframe.apply(
        lambda row: (
            (float(row["Sum of Order Kgs"]) * 1000.0) / float(row["Sum of Order Pcs"])
        )
        if float(row["Sum of Order Pcs"])
        else 0.0,
        axis=1,
    )
    summary_dataframe["SAM"] = summary_dataframe["Row Labels"].map(SIZE_CATEGORY_TO_SAM).fillna(0.0)
    summary_dataframe["Pcs/Kg"] = summary_dataframe.apply(
        lambda row: (
            float(row["Sum of Order Pcs"]) / float(row["Sum of Order Kgs"])
        )
        if float(row["Sum of Order Kgs"])
        else 0.0,
        axis=1,
    )

    per_day_order_pcs = total_order_pcs / DEFAULT_DAYS if DEFAULT_DAYS else 0.0
    per_day_order_kgs = total_order_kgs / DEFAULT_DAYS if DEFAULT_DAYS else 0.0

    summary_footer = pd.DataFrame(
        [
            {
                "Row Labels": "Total",
                "Sum of Order Pcs": total_order_pcs,
                "Sum of Order Kgs": total_order_kgs,
                "percentage": 100.0 if total_order_pcs else 0.0,
                "Grms/Pc": ((total_order_kgs * 1000.0) / total_order_pcs) if total_order_pcs else 0.0,
                "SAM": None,
                "Pcs/Kg": (total_order_pcs / total_order_kgs) if total_order_kgs else 0.0,
            },
            {
                "Row Labels": "No. of Days",
                "Sum of Order Pcs": DEFAULT_DAYS,
                "Sum of Order Kgs": None,
                "percentage": None,
                "Grms/Pc": None,
                "SAM": None,
                "Pcs/Kg": None,
            },
            {
                "Row Labels": "PER DAY",
                "Sum of Order Pcs": per_day_order_pcs,
                "Sum of Order Kgs": per_day_order_kgs,
                "percentage": None,
                "Grms/Pc": None,
                "SAM": None,
                "Pcs/Kg": (per_day_order_pcs / per_day_order_kgs) if per_day_order_kgs else 0.0,
            },
        ]
    )
    return pd.concat([summary_dataframe, summary_footer], ignore_index=True)


def build_size_summary(
    size_wise_details: pd.DataFrame,
    manual_override: pd.DataFrame | None,
) -> pd.DataFrame:
    base_summary = build_base_size_summary(size_wise_details)
    overridden_summary = apply_manual_summary_override(base_summary, manual_override)
    return add_derived_summary_rows(overridden_summary)


def extract_summary_category_value(
    summary_dataframe: pd.DataFrame,
    row_label: str,
    column_name: str,
) -> float:
    matching_rows = summary_dataframe[summary_dataframe["Row Labels"] == row_label]
    if matching_rows.empty:
        return 0.0
    value = matching_rows.iloc[0][column_name]
    if pd.isna(value):
        return 0.0
    return float(value)


def extract_summary_per_day_value(summary_dataframe: pd.DataFrame, column_name: str) -> float:
    return extract_summary_category_value(summary_dataframe, "PER DAY", column_name)
