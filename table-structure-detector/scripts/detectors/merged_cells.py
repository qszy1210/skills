from __future__ import annotations

from .base import BaseDetector, EffectiveRange, FlaggedRow


class MergedCellsDetector(BaseDetector):
    """检测合并单元格，标记可能的表头或分类标题行。

    跨列合并 >= 3列 或覆盖 >= 50% 有效列宽时标记。
    跨行合并单独记录。
    """

    name = "merged_cells"

    def __init__(self, min_col_span: int = 3, min_coverage: float = 0.5):
        self.min_col_span = min_col_span
        self.min_coverage = min_coverage

    def scan(self, sheet, eff: EffectiveRange) -> list[FlaggedRow]:
        row_merges: dict[int, list[str]] = {}

        for merged_range in sheet.merged_cells.ranges:
            min_row = merged_range.min_row
            max_row = merged_range.max_row
            min_col = merged_range.min_col
            max_col = merged_range.max_col
            col_span = max_col - min_col + 1
            row_span = max_row - min_row + 1

            is_significant_col = (
                col_span >= self.min_col_span
                or (eff.col_count > 0 and col_span / eff.col_count >= self.min_coverage)
            )

            if is_significant_col:
                coord = _range_str(min_row, min_col, max_row, max_col)
                for r in range(min_row, max_row + 1):
                    row_merges.setdefault(r, []).append(
                        f"{coord} 横向合并{col_span}列"
                    )

            if row_span >= 2 and not is_significant_col:
                coord = _range_str(min_row, min_col, max_row, max_col)
                for r in range(min_row, max_row + 1):
                    row_merges.setdefault(r, []).append(
                        f"{coord} 纵向合并{row_span}行"
                    )

        results: list[FlaggedRow] = []
        for r in sorted(row_merges):
            details = "; ".join(row_merges[r])
            results.append(FlaggedRow(
                row=r,
                detector=self.name,
                detail=details,
                severity="high",
            ))

        return results


def _col_letter(col: int) -> str:
    result = ""
    while col > 0:
        col, rem = divmod(col - 1, 26)
        result = chr(65 + rem) + result
    return result


def _range_str(r1: int, c1: int, r2: int, c2: int) -> str:
    if r1 == r2 and c1 == c2:
        return f"{_col_letter(c1)}{r1}"
    return f"{_col_letter(c1)}{r1}:{_col_letter(c2)}{r2}"
