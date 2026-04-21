from __future__ import annotations

from typing import Iterable

import pandas as pd

from wtt_app.config import WTT_INTERNAL_ROW_ID_COLUMN


def add_total_row(
    dataframe: pd.DataFrame,
    label_column: str | None = None,
    total_label: str = "Total",
) -> pd.DataFrame:
    if dataframe is None or dataframe.empty:
        return dataframe.copy()

    total_ready_dataframe = dataframe.copy()
    total_ready_dataframe = total_ready_dataframe[~is_total_row(total_ready_dataframe)].copy()
    numeric_columns = total_ready_dataframe.select_dtypes(include=["number"]).columns.tolist()
    total_row = {column_name: "" for column_name in total_ready_dataframe.columns}
    if label_column and label_column in total_ready_dataframe.columns:
        total_row[label_column] = total_label
    elif len(total_ready_dataframe.columns) > 0:
        total_row[total_ready_dataframe.columns[0]] = total_label
    for column_name in numeric_columns:
        total_row[column_name] = pd.to_numeric(total_ready_dataframe[column_name], errors="coerce").sum()
    return pd.concat([total_ready_dataframe, pd.DataFrame([total_row])], ignore_index=True)


def is_total_row(dataframe: pd.DataFrame) -> pd.Series:
    candidate_columns = [
        column_name
        for column_name in ["Section", "Designation", "Row Labels", "Parameters", "Shift"]
        if column_name in dataframe.columns
    ]
    if not candidate_columns:
        return pd.Series([False] * len(dataframe), index=dataframe.index)
    mask = pd.Series([False] * len(dataframe), index=dataframe.index)
    for column_name in candidate_columns:
        mask = mask | dataframe[column_name].astype(str).str.strip().eq("Total")
    return mask


def remove_total_row(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe is None or dataframe.empty:
        return dataframe.copy()
    return dataframe.loc[~is_total_row(dataframe)].copy()


def available_designations(dataframe: pd.DataFrame) -> list[str]:
    if dataframe is None or dataframe.empty or "Designation" not in dataframe.columns:
        return []
    designation_values = dataframe["Designation"].dropna().astype(str)
    filtered_values = sorted({value for value in designation_values if value.strip() and value.strip() != "Total"})
    return filtered_values


def apply_designation_filter(dataframe: pd.DataFrame, selected_designations: Iterable[str]) -> pd.DataFrame:
    if dataframe is None or dataframe.empty:
        return dataframe.copy()
    selected_designation_list = [value for value in selected_designations if str(value).strip()]
    if not selected_designation_list or "Designation" not in dataframe.columns:
        return dataframe.copy()
    return dataframe[dataframe["Designation"].isin(selected_designation_list)].copy()


def build_compact_section_table(dataframe: pd.DataFrame, display_columns: list[str]) -> pd.DataFrame:
    available_columns = [column_name for column_name in display_columns if column_name in dataframe.columns]
    compact_dataframe = dataframe[available_columns].copy()
    return add_total_row(compact_dataframe, label_column="Section" if "Section" in compact_dataframe.columns else None)


def build_expanded_editable_table(dataframe: pd.DataFrame, display_columns: list[str]) -> pd.DataFrame:
    available_columns = [column_name for column_name in display_columns if column_name in dataframe.columns]
    if WTT_INTERNAL_ROW_ID_COLUMN in dataframe.columns and WTT_INTERNAL_ROW_ID_COLUMN not in available_columns:
        available_columns = [WTT_INTERNAL_ROW_ID_COLUMN, *available_columns]
    expanded_dataframe = dataframe[available_columns].copy()
    return add_total_row(expanded_dataframe, label_column="Section" if "Section" in expanded_dataframe.columns else None)
