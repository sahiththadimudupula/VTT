from __future__ import annotations

from typing import Any


def build_formula_registry() -> list[dict[str, Any]]:
    return [
        {
            "Formula Tag": "WEAVING_WEAVER_FROM_BACKUP",
            "Target Section": "Loom Shed",
            "Target Designation": "Weaver",
            "Source": "Weaving Back-Up -> Weaver/ Day",
        },
        {
            "Formula Tag": "WEAVING_RELIEVER_FROM_BACKUP",
            "Target Section": "Loom Shed",
            "Target Designation": "Weaver - Lunch Reliver",
            "Source": "Weaving Back-Up -> Relievers/ Day + 3",
        },
        {
            "Formula Tag": "WEAVING_PRODUCTION_FITTER_FROM_BACKUP",
            "Target Section": "Loom Shed",
            "Target Designation": "Production Fitter",
            "Source": "Weaving Back-Up -> Production Fitter",
        },
        {
            "Formula Tag": "STENTER_FROM_STENTER_PLAN",
            "Target Section": "Drying",
            "Target Designation": "Padder Operator / Biancalanni / Stenter Operator",
            "Source": "Stenter inputs -> Stenter manpower",
        },
        {
            "Formula Tag": "CUTSEW_LC_FROM_LC_TOTAL_MACHINES",
            "Target Section": "TT_Cut&Sew",
            "Target Designation": "Length Cutting Operator / L, C,Material Transport",
            "Source": "TT_Cut&Sew_LC -> (Total Machines + 1) * 3",
        },
        {
            "Formula Tag": "CUTSEW_LH_FROM_LH_TOTAL_MACHINES",
            "Target Section": "TT_Cut&Sew",
            "Target Designation": "Length Hemming Operator / Cross Cutting Operator",
            "Source": "TT_Cut&Sew_LH -> (Total Machines + 1) * 3",
        },
        {
            "Formula Tag": "CUTSEW_DTA_FROM_DTA_SCALED_TOTALS",
            "Target Section": "TT_Cut&Sew",
            "Target Designation": "DTA Jobber / Line F./Trim B/ AQL/ Segr",
            "Source": "DTA -> scaled totals",
        },
        {
            "Formula Tag": "CUTSEW_JUKI_FROM_INCLUDING_CCH",
            "Target Section": "TT_Cut&Sew",
            "Target Designation": "DTA Stitcher",
            "Source": "JUKI -> Including CCH Prod.",
        },
        {
            "Formula Tag": "CUTSEW_CARTONS_FROM_SUMMARY_PER_DAY_KGS",
            "Target Section": "TT_Cut&Sew",
            "Target Designation": "Cartons Packers",
            "Source": "Size_wise_details_summary -> PER DAY Sum of Order Kgs",
        },
    ]
