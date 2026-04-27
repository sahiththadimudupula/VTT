from __future__ import annotations

from pathlib import Path

APP_TITLE = "Welspun Vapi Terry Tovals Engine"
APP_ICON = "🏭"
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_WORKBOOK_PATH = PACKAGE_ROOT / "input" / "WTT.xlsx"
OUTPUT_DIRECTORY_PATH = PACKAGE_ROOT / "output"
WORKING_WORKBOOK_PATH = OUTPUT_DIRECTORY_PATH / "WTT_working.xlsx"

SIZE_WISE_DETAILS_SHEET = "Size_wise_details"
SIZE_WISE_SUMMARY_SHEET = "Size_wise_details_summary"
WEAVING_BACKUP_SHEET = "Weaving Back-Up"
STENTER_SHEET = "Stenter"
WTT_SHEET = "WTT"
TT_CUT_SEW_LC_SHEET = "TT_Cut&Sew_LC"
TT_CUT_SEW_LH_SHEET = "TT_Cut&Sew_LH"
DTA_SHEET = "DTA"
JUKI_SHEET = "JUKI"
STENTER_PLAN_SHEET = "Stenter_Plan"
STENTER_MANPOWER_SHEET = "Stenter_Manpower"

TAB_SIZE_WISE = "Size_wise_details_production"
TAB_WEAVING = "Weaving"
TAB_PROCESSING = "Processing"
TAB_CUT_SEW = "Cut&Sew"
TAB_VTT = "VTT"

SECTION_ORDER_PROCESSING = [
    "Grey Folding",
    "Processing-Fabric Dyeing",
    "Sample Dyeing",
    "Processing - Store",
    "Processing-Shearing",
    "Drying",
    "Processing-Laboratory",
    "Winding",
    "Yarn Dyeing",
]
SECTION_ORDER_WEAVING = ["Weaving Preparatory", "Loom Shed"]
SECTION_ORDER_CUT_SEW = ["TT_Cut&Sew", "TQM Quality (Other Department)"]

SIZE_CATEGORY_ORDER = ["Bath", "Beach", "Glove", "Hand", "Mat", "Sheet", "Wash"]
SIZE_CATEGORY_TO_SAM = {
    "Bath": 36.6,
    "Beach": 75.4,
    "Glove": 37.7,
    "Hand": 29.0,
    "Mat": 30.4,
    "Sheet": 47.0,
    "Wash": 22.8,
}

SUMMARY_EDITABLE_COLUMNS = ["Sum of Order Pcs", "Sum of Order Kgs"]
WTT_EDITABLE_COLUMNS = [
    "BE_Final_Manpower",
    "General_Shift",
    "Shift_A",
    "Shift_B",
    "Shift_C",
    "Reliever",
    "Remarks",
]
WTT_COMPACT_DISPLAY_COLUMNS = [
    "Section",
    "Dept_Machine_Name",
    "Designation",
    "Machine_Count",
    "BE_Final_Manpower",
]
WTT_EXPANDED_DISPLAY_COLUMNS = [
    "Section",
    "Dept_Machine_Name",
    "Designation",
    "BE_Final_Manpower",
    "General_Shift",
    "Shift_A",
    "Shift_B",
    "Shift_C",
    "Reliever",
    "Remarks",
]
FORMULA_TAG_COLUMN = "Formula Tag"

WTT_INTERNAL_ROW_ID_COLUMN = "__row_id"
INTERNAL_DISPLAY_COLUMNS = [WTT_INTERNAL_ROW_ID_COLUMN]

PREDICTION_DIVISOR = 0.97
DEFAULT_DAYS = 30.0
DECIMAL_STEP = 0.01

LC_MACHINE_WIDTH = 300.0
LC_SPEED_MPM = 40.0
LC_EFFICIENCY = 0.5
LC_AVAILABLE_HOURS_PER_DAY = 7.5 * 3.0
LC_ROUNDING_BUFFER = 0.3

LH_MACHINE_WIDTH = 300.0
LH_SPEED_MPM = 40.0
LH_HEMMING_SPEED_MPM = 16.5
LH_EFFICIENCY = 0.7
LH_AVAILABLE_HOURS_PER_DAY = 7.5 * 3.0
LH_SAMPLE_AND_MAINTENANCE = 1.0
LH_ROUNDING_BUFFER = 0.3

DTA_REFERENCE_VALUE = 83499.0
DTA_LINE_SETTINGS = [
    {
        "label": "DTA (1-6)",
        "lines": 6.0,
        "sew_jobber_factor": 2.0,
        "pkg_jobber_factor": 1.0,
        "line_feed_factor": 2.0,
        "aql_factor": 1.0,
        "trim_boy_factor": 1.0,
    },
    {
        "label": "DTA (7&8)",
        "lines": 2.0,
        "sew_jobber_factor": 2.0,
        "pkg_jobber_factor": 1.0,
        "line_feed_factor": 2.0,
        "aql_factor": 1.0,
        "trim_boy_factor": 1.0,
    },
    {
        "label": "Cont",
        "lines": 5.0,
        "sew_jobber_factor": 1.0,
        "pkg_jobber_factor": 1.0,
        "line_feed_factor": 1.0,
        "aql_factor": 1.0,
        "trim_boy_factor": 1.0,
    },
]

JUKI_MACHINE_WIDTH = 300.0
JUKI_AVAILABLE_MINUTES_PER_SHIFT = 450.0
JUKI_EFFICIENCY = 0.6
JUKI_STITCHERS_PER_MACHINE = 2.0
JUKI_TQM_CHECKER_FACTOR = 0.8
JUKI_CCH_MACHINE_PLANNED = 8.0
JUKI_CCH_TOTAL_PRODUCTION = 100000.0
JUKI_CCH_AVAIL_SECONDS_PER_MACHINE = 450.0 * 60.0 * 0.65
JUKI_HAND_CCH_FACTOR = 0.6
JUKI_WASH_CCH_FACTOR = 0.65

STENTER_DEFAULT_INPUTS = {
    "required_production_mt_per_day": 85.0,
    "capacity_per_machine_per_shift_mt": 7.0,
    "available_machines": 5.0,
}
STENTER_SHIFT_NAMES = ["1st Shift", "2nd Shift", "3rd Shift"]
STENTER_INPUT_LABELS = {
    "Required Production / Day (MT)": "required_production_mt_per_day",
    "Capacity / Machine / Shift (MT)": "capacity_per_machine_per_shift_mt",
    "Available Machines": "available_machines",
}
STENTER_DESIGNATION_RULES = {
    "Padder Operator": 1.0,
    "Biancalanni": 2.0,
    "Stenter Operator": 1.0,
}

SESSION_KEY_WORKBOOK = "workbook_data"
SESSION_KEY_UNSAVED_CHANGES = "unsaved_changes"
STREAMLIT_NUMBER_FORMAT = "%.2f"

LC_CATEGORY_SETTINGS = {
    "LC_Mat": {"summary_label": "Mat", "length_cm": 100.0, "width_cm": 60.0},
    "LC_Sheet": {"summary_label": "Sheet", "length_cm": 180.0, "width_cm": 90.0},
    "LC_Bath": {"summary_label": "Bath", "length_cm": 160.0, "width_cm": 76.0},
    "LC_Hand": {"summary_label": "Hand", "length_cm": 70.0, "width_cm": 50.0},
    "LC_Wash": {"summary_label": "Wash", "length_cm": 43.0, "width_cm": 35.0},
    "LC_Gloves": {"summary_label": "Glove", "length_cm": 40.0, "width_cm": 40.0},
    "LC_Long": {"summary_label": None, "length_cm": 185.0, "width_cm": 90.0},
    "LC_Beach": {"summary_label": "Beach", "length_cm": 190.0, "width_cm": 90.0},
}
LH_CATEGORY_SETTINGS = {
    "LH_Mat": {"summary_label": "Mat", "length_cm": 100.0, "width_cm": 60.0},
    "LH_Sheet": {"summary_label": "Sheet", "length_cm": 180.0, "width_cm": 90.0},
    "LH_Bath": {"summary_label": "Bath", "length_cm": 160.0, "width_cm": 76.0},
    "LH_Hand": {"summary_label": "Hand", "length_cm": 70.0, "width_cm": 50.0},
    "LH_Wash": {"summary_label": "Wash", "length_cm": 43.0, "width_cm": 35.0},
    "LH_Gloves": {"summary_label": "Glove", "length_cm": 40.0, "width_cm": 40.0},
    "LH_Long": {"summary_label": None, "length_cm": 185.0, "width_cm": 90.0},
    "LH_Beach": {"summary_label": "Beach", "length_cm": 190.0, "width_cm": 90.0},
}
JUKI_CATEGORY_SETTINGS = {
    "JUKI_Mat": {"summary_label": "Mat", "length_cm": 100.0, "width_cm": 60.0},
    "JUKI_Sheet": {"summary_label": "Sheet", "length_cm": 180.0, "width_cm": 90.0},
    "JUKI_Bath": {"summary_label": "Bath", "length_cm": 160.0, "width_cm": 76.0},
    "JUKI_Hand": {"summary_label": "Hand", "length_cm": 70.0, "width_cm": 50.0},
    "JUKI_Wash": {"summary_label": "Wash", "length_cm": 43.0, "width_cm": 35.0},
    "JUKI_Gloves": {"summary_label": "Glove", "length_cm": 40.0, "width_cm": 40.0},
    "JUKI_Long": {"summary_label": None, "length_cm": 185.0, "width_cm": 90.0},
    "JUKI_Beach": {"summary_label": "Beach", "length_cm": 190.0, "width_cm": 90.0},
}

SIZE_WISE_REQUIRED_COLUMNS = [
    "SO No",
    "Customer Name",
    "Design Name",
    "Size",
    "Sort",
    "Size2",
    "Order Pcs",
    "Order Kgs",
]
