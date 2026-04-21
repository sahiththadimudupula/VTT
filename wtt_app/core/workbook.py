from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from wtt_app.calculations.formula_registry import build_formula_registry
from wtt_app.calculations.helpers import parse_stenter_inputs
from wtt_app.calculations.links import refresh_calculated_workbook
from wtt_app.config import (
    OUTPUT_DIRECTORY_PATH,
    SESSION_KEY_WORKBOOK,
    SIZE_WISE_DETAILS_SHEET,
    SIZE_WISE_REQUIRED_COLUMNS,
    SOURCE_WORKBOOK_PATH,
    WORKING_WORKBOOK_PATH,
    WTT_INTERNAL_ROW_ID_COLUMN,
    WTT_SHEET,
)
from wtt_app.core.formatters import standardize_sheet_columns
from wtt_app.core.tables import remove_total_row


def resolve_active_workbook_path() -> Path:
    if WORKING_WORKBOOK_PATH.exists():
        return WORKING_WORKBOOK_PATH
    return SOURCE_WORKBOOK_PATH


def load_workbook_sheets(source_workbook_path: str | None = None) -> dict[str, pd.DataFrame]:
    workbook_path = Path(source_workbook_path) if source_workbook_path else resolve_active_workbook_path()
    excel_file = pd.ExcelFile(workbook_path)
    return {
        sheet_name: standardize_sheet_columns(pd.read_excel(workbook_path, sheet_name=sheet_name))
        for sheet_name in excel_file.sheet_names
    }


def build_exportable_sheet_map(sheet_map: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    export_sheet_map: dict[str, pd.DataFrame] = {}
    for sheet_name, dataframe in sheet_map.items():
        export_dataframe = remove_total_row(dataframe).copy()
        hidden_columns = [
            column_name
            for column_name in [WTT_INTERNAL_ROW_ID_COLUMN]
            if column_name in export_dataframe.columns
        ]
        if hidden_columns:
            export_dataframe = export_dataframe.drop(columns=hidden_columns)
        export_sheet_map[sheet_name] = export_dataframe
    return export_sheet_map


def persist_workbook_state(workbook_state: dict[str, Any]) -> None:
    OUTPUT_DIRECTORY_PATH.mkdir(parents=True, exist_ok=True)
    export_sheet_map = build_exportable_sheet_map(workbook_state["sheets"])
    with pd.ExcelWriter(WORKING_WORKBOOK_PATH, engine="openpyxl") as excel_writer:
        for sheet_name, dataframe in export_sheet_map.items():
            dataframe.to_excel(excel_writer, sheet_name=sheet_name[:31], index=False)
    workbook_state["source_path"] = str(WORKING_WORKBOOK_PATH)


def initialize_workbook_state() -> None:
    if SESSION_KEY_WORKBOOK in st.session_state:
        return

    active_workbook_path = resolve_active_workbook_path()
    source_workbook = load_workbook_sheets(str(active_workbook_path))
    if WTT_SHEET in source_workbook and WTT_INTERNAL_ROW_ID_COLUMN not in source_workbook[WTT_SHEET].columns:
        source_workbook[WTT_SHEET] = source_workbook[WTT_SHEET].reset_index(drop=True)
        source_workbook[WTT_SHEET][WTT_INTERNAL_ROW_ID_COLUMN] = source_workbook[WTT_SHEET].index.astype(int)
    stenter_inputs = parse_stenter_inputs(source_workbook.get("Stenter", pd.DataFrame()))
    workbook_state: dict[str, Any] = {
        "source_path": str(active_workbook_path),
        "sheets": source_workbook,
        "summary_manual_override": None,
        "stenter_inputs": stenter_inputs,
        "formula_registry": build_formula_registry(),
    }
    st.session_state[SESSION_KEY_WORKBOOK] = refresh_calculated_workbook(workbook_state)


def get_workbook_state() -> dict[str, Any]:
    return st.session_state[SESSION_KEY_WORKBOOK]


def set_workbook_state(workbook_state: dict[str, Any], persist: bool = False) -> None:
    if persist:
        persist_workbook_state(workbook_state)
    st.session_state[SESSION_KEY_WORKBOOK] = workbook_state


def reload_workbook_state() -> None:
    st.session_state.pop(SESSION_KEY_WORKBOOK, None)
    initialize_workbook_state()


def reset_workbook_state() -> None:
    if WORKING_WORKBOOK_PATH.exists():
        WORKING_WORKBOOK_PATH.unlink()
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
    set_workbook_state(refresh_calculated_workbook(workbook_state), persist=True)
    return True, ""


def update_wtt_section(section_name: str, edited_section_dataframe: pd.DataFrame, persist: bool = True) -> None:
    workbook_state = get_workbook_state()
    original_wtt_dataframe = workbook_state["sheets"][WTT_SHEET].copy()
    cleaned_edited_dataframe = remove_total_row(edited_section_dataframe).copy()

    if WTT_INTERNAL_ROW_ID_COLUMN not in cleaned_edited_dataframe.columns:
        section_mask = original_wtt_dataframe["Section"].eq(section_name)
        fallback_ids = original_wtt_dataframe.loc[section_mask, WTT_INTERNAL_ROW_ID_COLUMN].tolist()
        cleaned_edited_dataframe[WTT_INTERNAL_ROW_ID_COLUMN] = fallback_ids[: len(cleaned_edited_dataframe)]

    editable_columns = [
        column_name
        for column_name in [
            "BE_Final_Manpower",
            "General_Shift",
            "Shift_A",
            "Shift_B",
            "Shift_C",
            "Reliever",
            "Remarks",
        ]
        if column_name in cleaned_edited_dataframe.columns and column_name in original_wtt_dataframe.columns
    ]

    original_wtt_dataframe = original_wtt_dataframe.set_index(WTT_INTERNAL_ROW_ID_COLUMN, drop=False)
    for _, edited_row in cleaned_edited_dataframe.iterrows():
        row_id = edited_row.get(WTT_INTERNAL_ROW_ID_COLUMN)
        if pd.isna(row_id) or row_id not in original_wtt_dataframe.index:
            continue
        for column_name in editable_columns:
            original_wtt_dataframe.at[row_id, column_name] = edited_row[column_name]

    workbook_state["sheets"][WTT_SHEET] = original_wtt_dataframe.reset_index(drop=True)
    workbook_state = refresh_calculated_workbook(workbook_state)
    set_workbook_state(workbook_state, persist=persist)


def build_export_bytes(sheet_map: dict[str, pd.DataFrame]) -> bytes:
    output_buffer = BytesIO()
    with pd.ExcelWriter(output_buffer, engine="openpyxl") as excel_writer:
        for sheet_name, dataframe in build_exportable_sheet_map(sheet_map).items():
            dataframe.to_excel(excel_writer, sheet_name=sheet_name[:31], index=False)
    return output_buffer.getvalue()
