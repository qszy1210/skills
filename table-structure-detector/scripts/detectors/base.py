from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Tuple


@dataclass
class FlaggedRow:
    row: int
    detector: str
    detail: str
    severity: str = "medium"  # "high" | "medium" | "low"


@dataclass
class EffectiveRange:
    """Sheet 的有效区域信息"""
    min_row: int
    max_row: int
    min_col: int
    max_col: int
    col_count: int = field(init=False)

    def __post_init__(self):
        self.col_count = self.max_col - self.min_col + 1


def compute_effective_range(sheet) -> EffectiveRange:
    """计算 sheet 的有效列范围（排除尾部全空列）"""
    min_row = sheet.min_row or 1
    max_row = sheet.max_row or 1
    min_col = sheet.min_column or 1
    max_col = sheet.max_column or 1

    while max_col > min_col:
        all_empty = True
        for r in range(min_row, min(max_row + 1, min_row + 100)):
            val = sheet.cell(row=r, column=max_col).value
            if val is not None and str(val).strip():
                all_empty = False
                break
        if all_empty:
            max_col -= 1
        else:
            break

    return EffectiveRange(
        min_row=min_row,
        max_row=max_row,
        min_col=min_col,
        max_col=max_col,
    )


def get_row_values(sheet, row: int, eff: EffectiveRange) -> list[Any]:
    """获取一行中有效范围内的所有单元格值"""
    return [
        sheet.cell(row=row, column=c).value
        for c in range(eff.min_col, eff.max_col + 1)
    ]


def classify_value(val: Any) -> str:
    """将单元格值归类为类型标签"""
    if val is None:
        return "none"
    if isinstance(val, bool):
        return "bool"
    if isinstance(val, (int, float)):
        return "number"
    import datetime
    if isinstance(val, (datetime.datetime, datetime.date, datetime.time)):
        return "date"
    s = str(val).strip()
    if not s:
        return "none"
    s_clean = s.replace(",", "").replace(" ", "")
    if s_clean.startswith(("+", "-")):
        s_clean = s_clean[1:]
    if s_clean.replace(".", "", 1).isdigit():
        return "number"
    return "str"


class BaseDetector(ABC):
    name: str = "base"

    @abstractmethod
    def scan(self, sheet, eff: EffectiveRange) -> list[FlaggedRow]:
        ...
