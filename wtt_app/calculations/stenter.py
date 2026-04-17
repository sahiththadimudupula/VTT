from __future__ import annotations

import pandas as pd

from wtt_app.config import (
    STENTER_DEFAULT_INPUTS,
    STENTER_DESIGNATION_RULES,
    STENTER_INPUT_LABELS,
)
from wtt_app.core.math_utils import excel_rounddown, excel_roundup


def read_stenter_inputs_from_raw(raw_dataframe: pd.DataFrame) -> dict[str, float]:
    input_values = STENTER_DEFAULT_INPUTS.copy()
    if raw_dataframe is None or raw_dataframe.empty:
        return input_values

    raw_copy = raw_dataframe.copy()
    for _, row in raw_copy.iterrows():
        first_column_value = row.iloc[0] if len(row) > 0 else None
        second_column_value = row.iloc[1] if len(row) > 1 else None
        if first_column_value in STENTER_INPUT_LABELS:
            input_key = STENTER_INPUT_LABELS[first_column_value]
            input_values[input_key] = float(second_column_value)
    return input_values


def build_stenter_tables(
    required_production_mt_per_day: float,
    capacity_per_machine_per_shift_mt: float,
    available_machines: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if capacity_per_machine_per_shift_mt <= 0:
        planning_dataframe = pd.DataFrame(
            {
                "Shift": ["1st Shift", "2nd Shift", "3rd Shift", "Total"],
                "Machines Planned": [0.0, 0.0, 0.0, 0.0],
                "Capacity / Machine / Shift": [0.0, 0.0, 0.0, pd.NA],
                "Production (MT)": [0.0, 0.0, 0.0, 0.0],
            }
        )
        manpower_dataframe = pd.DataFrame(
            [
                {
                    "Designation": designation_name,
                    "Workload": "1 Machine / Operator" if operators_per_machine == 1 else "2 Operator / Machine",
                    "Formula Logic": 0.0,
                    "BE_Scientific_Manpower": 0.0,
                    "BE_Final_Manpower": 0.0,
                    "General_Shift": 0.0,
                    "Shift_A": 0.0,
                    "Shift_B": 0.0,
                    "Shift_C": 0.0,
                    "Reliever": 0.0,
                }
                for designation_name, operators_per_machine in STENTER_DESIGNATION_RULES.items()
            ]
        )
        return planning_dataframe, manpower_dataframe

    required_machine_shifts_per_day = excel_roundup(
        required_production_mt_per_day / capacity_per_machine_per_shift_mt,
        0,
    )
    base_machines_per_shift = excel_rounddown(required_machine_shifts_per_day / 3, 0)
    remainder_machine_shifts = int(required_machine_shifts_per_day % 3)

    shift_names = ["1st Shift", "2nd Shift", "3rd Shift"]
    machines_planned: list[float] = []
    for shift_index, _ in enumerate(shift_names, start=1):
        extra_machine = 1.0 if shift_index <= remainder_machine_shifts else 0.0
        planned_machines = min(available_machines, base_machines_per_shift + extra_machine)
        machines_planned.append(float(planned_machines))

    planning_dataframe = pd.DataFrame(
        {
            "Shift": [*shift_names, "Total"],
            "Machines Planned": [
                machines_planned[0],
                machines_planned[1],
                machines_planned[2],
                sum(machines_planned),
            ],
            "Capacity / Machine / Shift": [
                capacity_per_machine_per_shift_mt,
                capacity_per_machine_per_shift_mt,
                capacity_per_machine_per_shift_mt,
                pd.NA,
            ],
            "Production (MT)": [
                machines_planned[0] * capacity_per_machine_per_shift_mt,
                machines_planned[1] * capacity_per_machine_per_shift_mt,
                machines_planned[2] * capacity_per_machine_per_shift_mt,
                sum(machines_planned) * capacity_per_machine_per_shift_mt,
            ],
        }
    )

    manpower_rows = []
    for designation_name, operators_per_machine in STENTER_DESIGNATION_RULES.items():
        shift_a = machines_planned[0] * operators_per_machine
        shift_b = machines_planned[1] * operators_per_machine
        shift_c = machines_planned[2] * operators_per_machine
        total_manpower = shift_a + shift_b + shift_c
        workload = (
            "1 Machine / Operator"
            if operators_per_machine == 1
            else "2 Operator / Machine"
        )
        manpower_rows.append(
            {
                "Designation": designation_name,
                "Workload": workload,
                "Formula Logic": total_manpower,
                "BE_Scientific_Manpower": total_manpower,
                "BE_Final_Manpower": total_manpower,
                "General_Shift": 0.0,
                "Shift_A": shift_a,
                "Shift_B": shift_b,
                "Shift_C": shift_c,
                "Reliever": 0.0,
            }
        )

    manpower_dataframe = pd.DataFrame(manpower_rows)
    return planning_dataframe, manpower_dataframe


def apply_stenter_to_wtt(
    wtt_dataframe: pd.DataFrame,
    stenter_manpower_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    updated_dataframe = wtt_dataframe.copy()
    if stenter_manpower_dataframe.empty:
        return updated_dataframe

    stenter_rows = stenter_manpower_dataframe.set_index("Designation")
    designation_names = list(stenter_rows.index)

    row_mask = (
        (updated_dataframe["Section"] == "Drying")
        & (updated_dataframe["Dept_Machine_Name"] == "Stenter")
        & (updated_dataframe["Designation"].isin(designation_names))
    )

    for designation_name in designation_names:
        designation_mask = row_mask & (updated_dataframe["Designation"] == designation_name)
        if not designation_mask.any():
            continue
        source_row = stenter_rows.loc[designation_name]
        for column_name in [
            "BE_Scientific_Manpower",
            "BE_Final_Manpower",
            "General_Shift",
            "Shift_A",
            "Shift_B",
            "Shift_C",
            "Reliever",
        ]:
            updated_dataframe.loc[designation_mask, column_name] = source_row[column_name]
    return updated_dataframe
