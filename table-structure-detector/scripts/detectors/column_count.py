from __future__ import annotations

import statistics

from .base import BaseDetector, EffectiveRange, FlaggedRow, get_row_values


class ColumnCountDetector(BaseDetector):
    """检测非空列数显著偏离中位数的行。

    单值行（非空列数 <= 2）标记为元信息行候选；
    列数过多或过少相对中位数偏离超过阈值则标记。
    """

    name = "column_count"

    def __init__(self, low_ratio: float = 0.5, high_ratio: float = 1.5):
        self.low_ratio = low_ratio
        self.high_ratio = high_ratio

    def scan(self, sheet, eff: EffectiveRange) -> list[FlaggedRow]:
        counts: list[int] = []
        for r in range(eff.min_row, eff.max_row + 1):
            values = get_row_values(sheet, r, eff)
            non_empty = sum(1 for v in values if v is not None and str(v).strip())
            counts.append(non_empty)

        if not counts:
            return []

        non_zero = [c for c in counts if c > 0]
        if not non_zero:
            return []
        median = statistics.median(non_zero)
        if median == 0:
            return []

        results: list[FlaggedRow] = []
        for i, cnt in enumerate(counts):
            r = eff.min_row + i
            if cnt == 0:
                continue
            if cnt <= 2 and median > 3:
                results.append(FlaggedRow(
                    row=r,
                    detector=self.name,
                    detail=f"单值行: 非空列数{cnt}, 中位数{median:.0f}",
                    severity="medium",
                ))
            elif cnt < median * self.low_ratio:
                results.append(FlaggedRow(
                    row=r,
                    detector=self.name,
                    detail=f"非空列数偏少: {cnt}, 中位数{median:.0f}",
                    severity="medium",
                ))
            elif cnt > median * self.high_ratio:
                results.append(FlaggedRow(
                    row=r,
                    detector=self.name,
                    detail=f"非空列数偏多: {cnt}, 中位数{median:.0f}",
                    severity="low",
                ))

        return results
