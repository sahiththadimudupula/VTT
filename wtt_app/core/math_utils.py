from __future__ import annotations

from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP


def excel_round(value: float, digits: int = 0) -> float:
    quantize_value = Decimal('1') if digits == 0 else Decimal('1').scaleb(-digits)
    return float(Decimal(str(value)).quantize(quantize_value, rounding=ROUND_HALF_UP))


def excel_roundup(value: float, digits: int = 0) -> float:
    multiplier = 10 ** digits
    return float((Decimal(str(value * multiplier)).to_integral_value(rounding=ROUND_CEILING)) / Decimal(str(multiplier)))


def excel_rounddown(value: float, digits: int = 0) -> float:
    multiplier = 10 ** digits
    return float((Decimal(str(value * multiplier)).to_integral_value(rounding=ROUND_FLOOR)) / Decimal(str(multiplier)))
