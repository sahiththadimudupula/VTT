from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from wtt_app.config import DECIMAL_STEP, INTERNAL_DISPLAY_COLUMNS, STREAMLIT_NUMBER_FORMAT


def format_number(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (int, float)):
        return f"{float(value):,.2f}"
    return str(value)


def format_dataframe_for_display(dataframe: pd.DataFrame) -> pd.DataFrame:
    formatted_dataframe = dataframe.copy()
    hidden_columns = [
        column_name for column_name in INTERNAL_DISPLAY_COLUMNS if column_name in formatted_dataframe.columns
    ]
    if hidden_columns:
        formatted_dataframe = formatted_dataframe.drop(columns=hidden_columns)
    numeric_columns = formatted_dataframe.select_dtypes(include=["number"]).columns
    for column_name in numeric_columns:
        formatted_dataframe[column_name] = formatted_dataframe[column_name].map(format_number)
    return formatted_dataframe


def standardize_sheet_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    standardized_dataframe = dataframe.copy()
    rename_map = {
        "HO_Scientific_Manpower": "BE_Scientific_Manpower",
        "HO_Final_Manpower": "BE_Final_Manpower",
    }
    existing_rename_map = {
        source_column: target_column
        for source_column, target_column in rename_map.items()
        if source_column in standardized_dataframe.columns
    }
    if existing_rename_map:
        standardized_dataframe = standardized_dataframe.rename(columns=existing_rename_map)
    return standardized_dataframe


def split_value_across_shifts(total_value: float) -> tuple[float, float, float]:
    rounded_total_value = round(float(total_value), 2)
    shift_a = round(rounded_total_value / 3.0, 2)
    shift_b = round(rounded_total_value / 3.0, 2)
    shift_c = round(rounded_total_value - shift_a - shift_b, 2)
    return shift_a, shift_b, shift_c


def build_numeric_column_config(column_names: list[str]) -> dict[str, Any]:
    return {
        column_name: st.column_config.NumberColumn(
            column_name,
            format=STREAMLIT_NUMBER_FORMAT,
            step=DECIMAL_STEP,
        )
        for column_name in column_names
    }
