
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from wtt_app.calculations.helpers import parse_stenter_inputs
from wtt_app.calculations.links import refresh_calculated_workbook
from wtt_app.config import (
    SESSION_KEY_WORKBOOK,
    SIZE_WISE_DETAILS_SHEET,
    SIZE_WISE_REQUIRED_COLUMNS,
    SOURCE_WORKBOOK_PATH,
    STENTER_SHEET,
    WTT_SHEET,
)
from wtt_app.core.formatters import standardize_sheet_columns


@st.cache_data(show_spinner=False)
def load_local_workbook(workbook_path_str: str) -> dict[str, pd.DataFrame]:
    workbook_path = Path(workbook_path_str)
    excel_file = pd.ExcelFile(workbook_path)
    return {
        sheet_name: standardize_sheet_columns(pd.read_excel(workbook_path, sheet_name=sheet_name))
        for sheet_name in excel_file.sheet_names
    }


def initialize_workbook_state() -> None:
    if SESSION_KEY_WORKBOOK in st.session_state:
        return

    source_workbook = load_local_workbook(str(SOURCE_WORKBOOK_PATH))
    stenter_inputs = parse_stenter_inputs(source_workbook.get(STENTER_SHEET, pd.DataFrame()))
    workbook_state: dict[str, Any] = {
        "source_path": str(SOURCE_WORKBOOK_PATH),
        "sheets": source_workbook,
        "summary_manual_override": None,
        "stenter_inputs": stenter_inputs,
    }
    st.session_state[SESSION_KEY_WORKBOOK] = refresh_calculated_workbook(workbook_state)


def get_workbook_state() -> dict[str, Any]:
    return st.session_state[SESSION_KEY_WORKBOOK]


def set_workbook_state(workbook_state: dict[str, Any]) -> None:
    st.session_state[SESSION_KEY_WORKBOOK] = workbook_state


def reset_workbook_state() -> None:
    st.session_state.pop(SESSION_KEY_WORKBOOK, None)
    initialize_workbook_state()


def validate_size_wise_details_columns(size_wise_dataframe: pd.DataFrame) -> list[str]:
    return [
        column_name
        for column_name in SIZE_WISE_REQUIRED_COLUMNS
        if column_name not in size_wise_dataframe.columns
    ]


def replace_size_wise_details_sheet(uploaded_bytes: bytes) -> tuple[bool, str]:
    workbook_state = get_workbook_state()
    uploaded_excel = pd.ExcelFile(BytesIO(uploaded_bytes))
    candidate_sheet_name = (
        SIZE_WISE_DETAILS_SHEET
        if SIZE_WISE_DETAILS_SHEET in uploaded_excel.sheet_names
        else uploaded_excel.sheet_names[0]
    )
    candidate_dataframe = pd.read_excel(BytesIO(uploaded_bytes), sheet_name=candidate_sheet_name)
    missing_columns = validate_size_wise_details_columns(candidate_dataframe)
    if missing_columns:
        return False, ", ".join(missing_columns)

    workbook_state["sheets"][SIZE_WISE_DETAILS_SHEET] = standardize_sheet_columns(candidate_dataframe)
    workbook_state["summary_manual_override"] = None
    set_workbook_state(refresh_calculated_workbook(workbook_state))
    return True, ""


def update_wtt_section(section_name: str, edited_section_dataframe: pd.DataFrame) -> None:
    workbook_state = get_workbook_state()
    original_wtt_dataframe = workbook_state["sheets"][WTT_SHEET].copy()

    remaining_dataframe = original_wtt_dataframe[original_wtt_dataframe["Section"] != section_name].copy()
    updated_wtt_dataframe = pd.concat(
        [remaining_dataframe, edited_section_dataframe],
        ignore_index=True,
    )

    original_order_dataframe = original_wtt_dataframe[["Section", "Sr_No"]].copy()
    original_order_dataframe["_sort_order"] = range(len(original_order_dataframe))

    updated_wtt_dataframe = (
        updated_wtt_dataframe.merge(
            original_order_dataframe,
            on=["Section", "Sr_No"],
            how="left",
        )
        .sort_values("_sort_order")
        .drop(columns="_sort_order")
        .reset_index(drop=True)
    )
    workbook_state["sheets"][WTT_SHEET] = updated_wtt_dataframe
    set_workbook_state(workbook_state)


def build_export_bytes(sheet_map: dict[str, pd.DataFrame]) -> bytes:
    output_buffer = BytesIO()
    with pd.ExcelWriter(output_buffer, engine="openpyxl") as excel_writer:
        for sheet_name, dataframe in sheet_map.items():
            dataframe.to_excel(excel_writer, sheet_name=sheet_name[:31], index=False)
    return output_buffer.getvalue()
