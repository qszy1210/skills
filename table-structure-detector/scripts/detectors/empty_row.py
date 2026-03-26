from __future__ import annotations

from .base import BaseDetector, EffectiveRange, FlaggedRow, get_row_values


class EmptyRowDetector(BaseDetector):
    """检测空行（所有单元格为 None 或空白）。

    连续空行合并为一个分隔事件，记录起止行。
    仅含空格/换行符的单元格视为空。
    """

    name = "empty_row"

    def scan(self, sheet, eff: EffectiveRange) -> list[FlaggedRow]:
        results: list[FlaggedRow] = []
        streak_start: int | None = None

        for r in range(eff.min_row, eff.max_row + 1):
            values = get_row_values(sheet, r, eff)
            is_empty = all(
                v is None or (isinstance(v, str) and not v.strip())
                for v in values
            )

            if is_empty:
                if streak_start is None:
                    streak_start = r
            else:
                if streak_start is not None:
                    self._emit(results, streak_start, r - 1)
                    streak_start = None

        if streak_start is not None:
            self._emit(results, streak_start, eff.max_row)

        return results

    def _emit(self, results: list[FlaggedRow], start: int, end: int):
        if start == end:
            detail = f"空行: 第{start}行"
        else:
            detail = f"连续空行: 第{start}-{end}行 (共{end - start + 1}行)"
        results.append(FlaggedRow(
            row=start,
            detector=self.name,
            detail=detail,
            severity="high",
        ))
